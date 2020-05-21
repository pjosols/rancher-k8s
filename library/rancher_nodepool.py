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
        prefix=dict(type='str', required=True),
        quantity=dict(type='int', required=True),
        controlplane=dict(type='bool', required=True),
        etcd=dict(type='bool', required=True),
        worker=dict(type='bool', required=True),
        cluster=dict(type='str', required=True),
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
            url="https://{}/v3/nodepool?name={}".format(
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
        # module.exit_json(changed=False, resource=resource, status=result.status, reason=result.reason)

        if not resource.get('data') or resource.get('data')[0].get('name') != module.params.get('name'):
            node_pool_installed = False

        elif resource.get('data')[0].get('name') == module.params.get('name'):
            node_pool_installed = True

        else:
            node_pool_installed = None
            module.fail_json(msg="Could not determine the install state of the specified node driver.")

        # Choose workflow based on install status and specified state
        if node_pool_installed and state == "present":
            # todo: we might have to update it # put
            # update_it(module)
            module.exit_json(changed=False, resource=resource, status=result.status, reason=result.reason)

        elif node_pool_installed and state == "absent":
            remove_url = resource['data'][0]['links']['remove']
            delete_it(module, remove_url)

        elif not node_pool_installed and state == "present":
            install_it(module) # post

        elif not node_pool_installed and state == "absent":
            module.exit_json(changed=False, resource=resource, status=result.status, reason=result.reason)

        else:
            module.fail_json(msg="Could not determine the install state of the specified node driver.")

    except urllib_request.HTTPError as e:
        module.fail_json(msg=json.loads(e.fp.read()))


def update_it(module):
    pass


def install_it(module):

    # get the clusterId
    result = open_url(
        url="https://{}/v3/cluster?name={}".format(
            module.params.get("host"),
            module.params.get("cluster")
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
    cluster_resource = json.loads(result.read())
    cluster_id = cluster_resource['data'][0]['id']

    # get the nodeTemplateId
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
    template_resource = json.loads(result.read())
    template_id = template_resource['data'][0]['id']

    # create the nodepool
    data = {
        "name": module.params.get('name'),
        "clusterId": cluster_id,
        "nodeTemplateId": template_id,
        "hostnamePrefix": module.params.get('prefix'),
        "quantity": module.params.get('quantity'),
        "controlPlane": module.params.get('controlplane'),
        "etcd": module.params.get('etcd'),
        "worker": module.params.get('worker'),
    }
    result = open_url(
        url="https://{}/v3/nodepool".format(
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
