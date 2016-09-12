#!/usr/bin/python
'''This is an ansible module to add subnets to a SoftLayer account'''

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
module: sl_subnet
short_description: Add or remove a subnet to a SoftLayer VLAN
description:
  - Adds or removes a subnet to a SoftLayer VLAN.
version_added: "2.2"
options:
  subnet_type:
    description:
      - The type of subnet to add
      - Required when the state is 'present'
    choices:
      - private
      - public
      - global
    required: false
  quantity:
    description:
      - The number of ip addresses to allocate in the subnet
    required: false
  vlan_id:
    description:
      - The VLAN id to which to add the subnet
    required: false
  version:
    description:
      - The IP version for the subnet
    required: false
    choices:
      - 4
      - 6
    default: 4
  state:
    description:
      - Create or remove a subnet.
      - Specify "present" for create, "absent" to cancel.
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
SUBNET_TYPES = ['private', 'public', 'global']
IP_VERSION = [4, 6]

try:
    import SoftLayer
    from SoftLayer import NetworkManager

    class SubnetManager(NetworkManager):
        '''Wraps the SoftLayer API to add and remove subnets'''
        def __init__(self, username=None, api_key=None):
            super(SubnetManager, self).__init__(
                SoftLayer.create_client_from_env(
                    username=username, api_key=api_key))

        def add_subnet(self, module):
            '''Adds a subnet to the account for SoftLayer'''

            subnet_type = module.params.get('subnet_type')
            quantity = module.params.get('quantity')
            vlan_id = module.params.get('vlan_id')
            version = module.params.get('version')
            res = self.add_subnet(subnet_type, quantity, vlan_id, version, True)

            # TODO Figure out exactly what res is.
            if res is True:
                return False, res
            else:
                res = self.add_subnet(subnet_type, quantity, vlan_id, version)
                return True, res

        def remove_subnet(self, module):
            '''Removes a subnet to the account for SoftLayer'''
            # TODO implement remove_subnet
            return False, {}

    HAS_SL = True
except ImportError:
    HAS_SL = False

def main():
    '''main function'''

    module = AnsibleModule(
        argument_spec=dict(
            subnet_type=dict(type='str', choices=SUBNET_TYPES),
            quantity=dict(type='int', default=None),
            vlan_id=dict(type='str', default=None),
            version=dict(type='int', default=4, choices=IP_VERSION),
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

    manager = SubnetManager(username, api_key)

    if state == 'absent':
        (changed, instance) = manager.remove_subnet(module)

    elif state == 'present':
        (changed, instance) = manager.add_subnet(module)

    module.exit_json(
        changed=changed,
        instance=json.loads(json.dumps(instance, default=lambda o: o.__dict__)))

if __name__ == '__main__':
    main()
