#!/usr/bin/python


from ansible.module_utils.basic import AnsibleModule, json
from ansible.module_utils.urls import open_url, urllib_request


def main():

    argument_spec = dict(
        name=dict(type='str', required=True),
        host=dict(type='str', required=True),
        state=dict(type='str', required=False),  # default: present
        user=dict(type='str', required=True),
        password=dict(type='str', required=True, no_log=True),
        server=dict(type='str', required=True),
        token=dict(type='str', required=True, no_log=True),
        region=dict(type='str', required=True),
        network=dict(type='str', required=True),
        ssh_user=dict(type='str', required=False),
        cpu=dict(type='int', required=True),
        memory=dict(type='int', required=True),
        disk=dict(type='int', required=True),
        labels=dict(type='dict', required=False),
        image=dict(type='str', required=True),
        engine_install_url=dict(type='str', required=True),
        engine_storage_driver=dict(type='str', required=True),
        engine_options=dict(type='dict', required=True),
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
            url="https://{}/v3/nodetemplate?name={}".format(
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

        # Determine if node template exists
        if not resource.get('data') or resource.get('data')[0].get('name') != module.params.get('name'):
            template_exists = False

        elif resource.get('data')[0].get('name') == module.params.get('name'):
            template_exists = True

        else:
            template_exists = None
            module.fail_json(msg="Could not determine if the node template exists.")

        # Choose workflow based on node template existence and specified state
        if template_exists and state == "present":
            module.exit_json(changed=False, resource=resource, status=result.status, reason=result.reason)

        elif template_exists and state == "absent":
            remove_url = resource['data'][0]['links']['remove']
            delete_it(module, remove_url)

        elif not template_exists and state == "present":
            install_it(module)

        elif not template_exists and state == "absent":
            module.exit_json(changed=False, resource=resource, status=result.status, reason=result.reason)

        else:
            module.fail_json(msg="Could not determine the install state of the specified node template.")

    except urllib_request.HTTPError as e:
        module.fail_json(msg=json.loads(e.fp.read()))


def install_it(module):
    data = {
        "name": module.params.get('name'),
        "eportalConfig": {
            "cpu": module.params.get('cpu'),
            "memory": module.params.get('memory'),
            "disk": module.params.get('disk'),
            "location": module.params.get('region'),
            "os": module.params.get('image'),
            # "sshUser": module.params.get('ssh_user'), # because local_prodadmin is baked into eportal backend anyway
            "server": module.params.get('server'),
            "token": module.params.get('token'),
            "vlan": module.params.get('network'),
        },
        "engineInstallURL": module.params.get('engine_install_url'),
        "engineStorageDriver": module.params.get('engine_storage_driver'),
        "engineOpt": module.params.get('engine_options'),
        "labels": module.params.get('labels')
    }

    result = open_url(
        url="https://{}/v3/nodetemplate".format(
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
    module.exit_json(changed=True, reason=result.reason, status=result.status, resource=resource)


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
    module.exit_json(changed=True, reason=result.reason, status=result.status)


if __name__ == '__main__':
    main()
