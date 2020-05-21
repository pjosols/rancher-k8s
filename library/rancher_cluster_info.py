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
        module.exit_json(changed=False, resource=resource, status=result.status, reason=result.reason)

    except urllib_request.HTTPError as e:
        module.fail_json(msg=json.loads(e.fp.read()))


if __name__ == '__main__':
    main()
