#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule, json
from ansible.module_utils.urls import open_url, urllib_request


def main():

    argument_spec = dict(

        name=dict(type='str', required=True),
        host=dict(type='str', required=True),
        user=dict(type='str', required=True),
        password=dict(type='str', required=True, no_log=True),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=False
    )

    state = module.params.get("state") or "present"
    if state not in ['present', 'absent']:
        module.fail_json(msg="The state specified may only be either 'present' or 'absent'.")

    try:
        # Get the cluster object id
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
        cluster_id = resource.get('data')[0].get('id')
        state = resource.get('data')[0].get('state')

        if state != "active":
            module.fail_json(msg="The cluster state is not active, but {}.".format(state))

        # Generate the kubeconfig
        post_result = open_url(
            url="https://{}/v3/cluster/{}?action=generateKubeconfig".format(
                module.params.get("host"),
                cluster_id
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
        )
        kubeconfig_resource = json.loads(post_result.read())
        module.exit_json(changed=False, resource=kubeconfig_resource, status=result.status, reason=result.reason)

    except urllib_request.HTTPError as e:
        module.fail_json(msg=json.loads(e.fp.read()))




if __name__ == '__main__':
    main()
