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

        # only required to install, not to delete or get
        url=dict(type='str', required=False),
        uiUrl=dict(type='str', required=False),
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
            url="https://{}/v3/nodedriver?name={}".format(
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
            # data=json.dumps(module.params),
        )

        resource = json.loads(result.read())

        # Determine if node driver installed
        if not resource.get('data') or resource.get('data')[0].get('name') != module.params.get('name'):
            node_driver_installed = False

        elif resource.get('data')[0].get('name') == module.params.get('name'):
            node_driver_installed = True

        else:
            node_driver_installed = None
            module.fail_json(msg="Could not determine the install state of the specified node driver.")

        # Choose workflow based on install status and specified state
        if node_driver_installed and state == "present":
            module.exit_json(changed=False, resource=resource, status=result.status, reason=result.reason)

        elif node_driver_installed and state == "absent":
            remove_url = resource['data'][0]['links']['remove']
            delete_it(module, remove_url)

        elif not node_driver_installed and state == "present":
            install_it(module)

        elif not node_driver_installed and state == "absent":
            module.exit_json(changed=False, resource=resource, status=result.status, reason=result.reason)

        else:
            module.fail_json(msg="Could not determine the install state of the specified node driver.")

    except urllib_request.HTTPError as e:
        module.fail_json(msg=json.loads(e.fp.read()))


def install_it(module):
    data = {
        'name': module.params.get('name'),
        'active': True,
        'builtin': False,
        'url': module.params.get('url'),
        'uiUrl': module.params.get('uiUrl'),
        'whitelistDomains': ['*', '10.74.82.71', 'sec01u0peafy11.uathost.prd']
    }
    result = open_url(
        url="https://{}/v3/nodedriver".format(
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
        method='POST',
        data=json.dumps(data),
    )
    resource = json.loads(result.read())
    module.exit_json(changed=True, resource=resource, reason=result.reason, status=result.status)


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
    module.exit_json(changed=True, resource=resource, reason=result.reason, status=result.status)


if __name__ == '__main__':
    main()
