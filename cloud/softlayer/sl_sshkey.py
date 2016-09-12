#!/usr/bin/python
'''Implements ans ansible module to import ssh keys to SoftLayer'''
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

from ansible.module_utils.basic import AnsibleModule, json

DOCUMENTATION = '''
---
module: sl_sshkey
short_description: add or remove sshkey in SoftLayer
description:
    - Adds or removes SoftLayer ssh keys.
version_added: "2.2"
options:
    key:
        description:
            - The public key to add, on removal this or name is required.
        required: false
    name:
        description:
            - The name for the key that is being added.
        required: false

    state:
        description:
            - Create, or cancel a virtual instance. Specify "present" for create, "absent" to cancel.
        required: false
        default: 'present'
    username:
        description:
            - username credentials for api calls
        required: false
    api_key:
        description:
            - token for api call
        required: false

requirements:
    - "python >= 2.6"
    - "softlayer >= 4.1.1"
author: "Eldon Allred"
'''

EXAMPLES = '''
'''

# TODO: Disabled RETURN as it is breaking the build for docs. Needs to be fixed.
RETURN = '''# '''


STATES = ['present', 'absent']

try:
    import SoftLayer
    from SoftLayer import SshKeyManager as SSHKeyManager

    class SecureShellManager(SSHKeyManager):
        '''Wraps SoftLayer API calls to add ssh public keys to an account'''
        def __init__(self, username=None, api_key=None):
            super(SecureShellManager, self).__init__(
                SoftLayer.create_client_from_env(
                    username=username, api_key=api_key))

        def add_key(self, name, key):
            '''Adds a name public key pair to the SoftLayer account'''
            keys = self.list_keys(label=name)
            num_keys = len(keys)
            if num_keys == 0:
                instance = self.add_keys(key=key, label=name)
                return True, instance
            elif num_keys == 1:
                if keys[0].key == key:
                    return False, keys[0]
                else:
                    self.delete_key(keys[0].key_id)
                    instance = self.add_key(key=key, name=name)
                    return True, instance
            else:
                raise ValueError('Zero or one keys expected received %d' % num_keys)

        def remove_key(self, name):
            '''Removes a key by name from the SoftLayer account'''
            keys = self.list_keys(label=name)
            num_keys = len(keys)
            if num_keys == 0:
                return False, {}
            elif num_keys == 1:
                self.delete_key(keys[0].key_id)
                return True, keys[0]
            else:
                raise ValueError('Zero or one keys expected received %d' % num_keys)
    HAS_SL = True
except ImportError:
    HAS_SL = False


def main():
    '''main function'''

    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type='str', default=None),
            key=dict(type='str', default=None),
            state=dict(default='present', choices=STATES),
            username=dict(type='str', default=None),
            api_key=dict(type='str', default=None),
        )
    )

    if not HAS_SL:
        module.fail_json(msg=
                         'softlayer python library required for this module')

    username = module.params.get('username')
    api_key = module.params.get('api_key')
    state = module.params.get('state')
    name = module.params.get('name')
    key = module.params.get('key')

    manager = SecureShellManager(username, api_key)

    if state == 'absent':
        (changed, key) = manager.remove_key(name)

    elif state == 'present':
        (changed, key) = manager.add_key(name, key)

    module.exit_json(
        changed=changed,
        key=json.loads(json.dumps(key, default=lambda o: o.__dict__)))


if __name__ == '__main__':
    main()
