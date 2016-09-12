#!/usr/bin/python
'''Implements an ansible module to make a bare metal server for SoftLayer'''
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

import time
from ansible.module_utils.basic import AnsibleModule, json

DOCUMENTATION = '''
---
module: sl_hardware
short_description: create or cancel a bare metal instance in SoftLayer
description:
  - Creates or cancels SoftLayer instances. When created, optionally waits for it to be 'running'.
version_added: "2.2"
options:
  instance_id:
    description:
      - Instance Id of the instance on which to perform an action
    required: false
    default: null
  hostname:
    description:
      - Hostname to be used in the instance
    required: false
    default: null
  domain:
    description:
      - Domain name to be provided to the instance
    required: false
    default: null
  datacenter:
    description:
      - Datacenter where to deploy the instance
    required: false
    default: null
  hourly:
    description:
      - Flag to determine if the instance should be hourly billed
    required: false
    default: true
  private:
    description:
      - Flag to determine if the instance should be private only
    required: false
    default: false
  os_code:
    description:
      - The OS Code for the new instance
    required: false
    default: null
  nic_speed:
    description:
      - NIC Speed to assign to new the instance
    required: false
    default: 10
  ssh_keys:
    description:
      - List of ssh keys by their Id to assign to the instance
    required: false
    default: null
  post_uri:
    description:
      - URL of a post provisioning script to load and execute on the instance
    required: false
    default: null
  state:
    description:
      - Create, or cancel a the instance. Specify "present" for create, "absent" to cancel.
    required: false
    default: 'present'
  wait:
    description:
      - Flag used to wait for active status before returning
    required: false
    default: true
  wait_timeout:
    description:
      - time in seconds before wait returns
    required: false
    default: 600
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
DATACENTERS = ['ams01', 'ams03', 'dal01', 'dal05', 'dal06', 'dal09', 'fra02',
               'hkg02', 'hou02', 'lon02', 'mel01', 'mex01', 'mil01', 'mon01',
               'par01', 'sjc01', 'sjc03', 'sao01', 'sea01', 'sng01', 'syd01',
               'tok02', 'tor01', 'wdc01', 'wdc04']
CPU_SIZES = [1, 2, 4, 8, 16]
MEMORY_SIZES = [1024, 2048, 4096, 6144, 8192, 12288, 16384, 32768, 49152, 65536]
INITIALDISK_SIZES = [25, 100]
LOCALDISK_SIZES = [25, 100, 150, 200, 300]
SANDISK_SIZES = [10, 20, 25, 30, 40, 50, 75, 100, 125, 150, 175, 200, 250, 300,
                 350, 400, 500, 750, 1000, 1500, 2000]
NIC_SPEEDS = [10, 100, 1000]

try:
    import SoftLayer
    from SoftLayer import HardwareManager

    HAS_SL = True

    class BareMetalManager(HardwareManager):
        '''Wraps calls to the SoftLayer API'''
        def __init__(self, username=None, api_key=None):
            super(BareMetalManager, self).__init__(
                SoftLayer.create_client_from_env(
                    username=username, api_key=api_key))

        def create_baremetal_instance(self, module):
            '''Provisions an instance with SoftLayer'''
            instances = self.list_instances(
                hostname=module.params.get('hostname'),
                domain=module.params.get('domain'),
                datacenter=module.params.get('datacenter')
            )

            if instances:
                return False, None

            # Check if OS or Image Template is provided
            # (Can't be both, defaults to OS)
            if module.params.get('os_code') != None and \
                    module.params.get('os_code') != '':
                module.params['image_id'] = ''
            elif module.params.get('image_id') != None and \
                    module.params.get('image_id') != '':
                # Blank out disks since it will use the template
                module.params['os_code'] = ''
                module.params['disks'] = []
            else:
                return False, None

            tags = module.params.get('tags')

            if isinstance(tags, list):
                tags = ','.join(map(str, module.params.get('tags')))

            instance = self.place_order(
                hostname=module.params.get('hostname'),
                domain=module.params.get('domain'),
                cpus=module.params.get('cpus'),
                memory=module.params.get('memory'),
                hourly=module.params.get('hourly'),
                datacenter=module.params.get('datacenter'),
                os_code=module.params.get('os_code'),
                image_id=module.params.get('image_id'),
                local_disk=module.params.get('local_disk'),
                disks=module.params.get('disks'),
                ssh_keys=module.params.get('ssh_keys'),
                nic_speed=module.params.get('nic_speed'),
                private=module.params.get('private'),
                public_vlan=module.params.get('public_vlan'),
                private_vlan=module.params.get('private_vlan'),
                dedicated=module.params.get('dedicated'),
                post_uri=module.params.get('post_uri'),
                tags=tags)

            if instance != None and instance['id'] > 0:
                return True, instance
            else:
                return False, None

        def wait_for_instance(self, module, instance_id):
            '''Pauses execution until the instance is running'''
            instance = None
            completed = False
            wait_timeout = time.time() + module.params.get('wait_time')
            while not completed and wait_timeout > time.time():
                try:
                    completed = self.wait_for_ready(instance_id, 10, 2)
                    if completed:
                        instance = self.get_instance(instance_id)
                except:
                    completed = False

            return completed, instance

        def cancel_instance(self, module):
            '''Removes machine instance from the account'''
            canceled = True
            if module.params.get('instance_id') is None and \
                    (module.params.get('tags') or \
                    module.params.get('hostname') or \
                    module.params.get('domain')):

                tags = module.params.get('tags')
                if isinstance(tags, basestring):
                    tags = [module.params.get('tags')]
                    instances = self.list_instances(
                        tags=tags,
                        hostname=module.params.get('hostname'),
                        domain=module.params.get('domain'))
                    for instance in instances:
                        try:
                            self.cancel_instance(instance['id'])
                        except:
                            canceled = False
                elif module.params.get('instance_id') and \
                        module.params.get('instance_id') != 0:
                    try:
                        self.cancel_instance(instance['id'])
                    except:
                        canceled = False
                else:
                    return False, None

            return canceled, None

except ImportError:
    HAS_SL = False

def main():
    '''main'''

    module = AnsibleModule(
        argument_spec=dict(
            instance_id=dict(),
            hostname=dict(),
            domain=dict(),
            datacenter=dict(choices=DATACENTERS),
            tags=dict(),
            hourly=dict(type='bool', default=True),
            private=dict(type='bool', default=False),
            dedicated=dict(type='bool', default=False),
            local_disk=dict(type='bool', default=True),
            cpus=dict(type='int', choices=CPU_SIZES),
            memory=dict(type='int', choices=MEMORY_SIZES),
            disks=dict(type='list', default=[25]),
            os_code=dict(),
            image_id=dict(),
            nic_speed=dict(type='int', choices=NIC_SPEEDS),
            public_vlan=dict(),
            private_vlan=dict(),
            ssh_keys=dict(type='list', default=[]),
            post_uri=dict(),
            state=dict(default='present', choices=STATES),
            wait=dict(type='bool', default=True),
            wait_time=dict(type='int', default=600),
            username=dict(type='str', default=None),
            api_key=dict(type='str', default=None),
        )
    )

    if not HAS_SL:
        module.fail_json(msg=
                         'softlayer python library required for this module')

    state = module.params.get('state')
    username = module.params.get('username')
    api_key = module.params.get('api_key')
    wait = module.params.get('wait')

    manager = BareMetalManager(username, api_key)

    if state == 'absent':
        (changed, instance) = manager.cancel_instance(module)

    elif state == 'present':
        (changed, instance) = manager.create_baremetal_instance(module)
        if wait is True and instance:
            (changed, instance) = manager.wait_for_instance(module, instance['id'])

    module.exit_json(
        changed=changed,
        instance=json.loads(json.dumps(instance, default=lambda o: o.__dict__)))


if __name__ == '__main__':
    main()
