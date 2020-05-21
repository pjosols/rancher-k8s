#!/usr/bin/python


from ansible.module_utils.basic import AnsibleModule, json
from ansible.module_utils.urls import open_url, urllib_request


def main():

    argument_spec = dict(

        name=dict(type='str', required=True),
        region=dict(type='str', required=True),
        host=dict(type='str', required=True),
        state=dict(type='str', required=False),  # default: present
        user=dict(type='str', required=True),
        password=dict(type='str', required=True, no_log=True),
        kubernetes_version=dict(type='str', required=True),
        cni_provider=dict(type='str', required=True),
        ingress_provider=dict(type='str', required=True),
        enable_dvp=dict(type='bool', required=True),

        # Optional vcenter params when dvp is required
        vcenter_host=dict(type='str', required=False),
        vcenter_user=dict(type='str', required=False),
        vcenter_password=dict(type='str', required=False, no_log=True),
        vcenter_machine_folder=dict(type='str', required=False),
        vcenter_datastore=dict(type='str', required=False),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=False
    )

    state = module.params.get("state") or "present"
    if state not in ['present', 'absent']:
        module.fail_json(msg="The state specified may only be either 'present' or 'absent'.")

    try:
        result = open_url(
            url="https://{}/v3/cluster?name={}".format(
                module.params.get("host"),
                module.params.get("name")
            ),
            url_username=module.params.get("user"),
            url_password=module.params.get("password"),
            force_basic_auth=True,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            validate_certs=False,
            method='GET',
        )

        resource = json.loads(result.read())

        # Determine if cluster exists
        if not resource.get('data') or resource.get('data')[0].get('name') != module.params.get('name'):
            cluster_exists = False

        elif resource.get('data')[0].get('name') == module.params.get('name'):
            cluster_exists = True

        else:
            cluster_exists = None
            module.fail_json(msg="Could not determine if the cluster exists.")

        # Choose workflow based on cluster existence and specified state
        if cluster_exists and state == "present":
            module.exit_json(changed=False, resource=resource, status=result.status, reason=result.reason)

        elif cluster_exists and state == "absent":
            remove_url = resource['data'][0]['links']['remove']
            delete_it(module, remove_url)

        elif not cluster_exists and state == "present":
            install_it(module)

        elif not cluster_exists and state == "absent":
            module.exit_json(changed=False, resource=resource, status=result.status, reason=result.reason)

        else:
            module.fail_json(msg="Could not determine the install state of the specified cluster.")

    except urllib_request.HTTPError as e:
        module.fail_json(msg=json.loads(e.fp.read()))


def install_it(module):
    data = {
        "name": module.params.get('name'),
        "dockerRootDir": "/var/lib/docker",
        "enableClusterAlerting": False,
        "enableClusterMonitoring": False,
        "enableNetworkPolicy": False,
        "rancherKubernetesEngineConfig": {
            "addonJobTimeout": 30,
            "ignoreDockerVersion": True,
            # "cloudProvider": "{{ cloudProvider if k8s[site_name].dynamic_volume_provisioning else omit }}",
            "sshAgentAuth": False,
            "kubernetesVersion": module.params.get("kubernetes_version"),  # v1.14.5-rancher1-1
            "authentication": {
                "strategy": "x509"
            },
            "network": {
                "plugin": module.params.get("cni_provider")  # calico
            },
            "ingress": {
                "provider": module.params.get("ingress_provider")  # nginx
            },
            "monitoring": {
                "provider": "metrics-server"
            },
            "services": {
                "kubeApi": {
                    "alwaysPullImages": False,
                    "podSecurityPolicy": False,
                    "serviceNodePortRange": "30000-32767"
                },
                "etcd": {
                    "creation": "12h",
                    "extraArgs": {
                        "heartbeat-interval": 500,
                        "election-timeout": 5000
                    },
                    "retention": "72h",
                    "snapshot": False,
                    "backupConfig": {
                        "enabled": True,
                        "intervalHours": 12,
                        "retention": 6
                    }
                }
            }
        },
        "localClusterAuthEndpoint": {
            "enabled": True
        }
    }

    # https://rancher.com/docs/rke/latest/en/config-options/cloud-providers/vsphere/config-reference/
    if module.params.get('enable_dvp'):
        cloud_provider = {
            "name": "vsphere",
            "vsphereCloudProvider": {
                "global": {
                    "insecure-flag": True,
                    "soap-roundtrip-count": 0
                },
                "virtualCenter": {
                    module.params["vcenter_host"]: {
                        "datacenters": module.params.get('region'),
                        "user": module.params["vcenter_user"],
                        "password": module.params["vcenter_password"]
                    }
                },
                "workspace": {
                    "datacenter": module.params.get('region'),
                    "default-datastore": module.params["vcenter_datastore"],
                    "folder": module.params["vcenter_machine_folder"],  # for dummy VMs used for volume provisioning
                    "server": module.params["vcenter_host"]
                }
            }
        }
        data['rancherKubernetesEngineConfig'].update({'cloudProvider': cloud_provider})

    result = open_url(
        url="https://{}/v3/cluster".format(
            module.params.get("host"),
        ),
        url_username=module.params.get("user"),
        url_password=module.params.get("password"),
        force_basic_auth=True,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        validate_certs=False,
        method='POST',
        data=json.dumps(data),
    )
    resource = json.loads(result.read())
    module.exit_json(changed=True, resource=resource, status=result.status, reason=result.reason)


def delete_it(module, remove_url):
    result = open_url(
        url="{}".format(remove_url),
        url_username=module.params.get("user"),
        url_password=module.params.get("password"),
        force_basic_auth=True,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        validate_certs=False,
        method='DELETE',
    )
    resource = json.loads(result.read())
    module.exit_json(changed=True, resource=resource, status=result.status, reason=result.reason)


if __name__ == '__main__':
    main()
