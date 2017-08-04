#!/usr/bin/env python
# VMware vSphere Python SDK
# Copyright (c) 2008-2014 VMware, Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from __future__ import print_function

import atexit
import argparse
import getpass
import ssl

from pyVim import connect
import pyVmomi
from pyVmomi import vim
#from pyvMomi import vim
# Demonstrates:
# =============
# * How to write python 2.7 and 3.3 compatible code in one script
# * How to parse arguments in a python script
# * How to pretty print format a dictionary
# * How to connect to a vSphere instance
# * How to search for virtual machines efficiently
# * How to interrogate virtual machine hardware info
# * How to determine the data type of a dynamic object instance
# * How to build a summary of a virtual device & virtual disk
# * How to interrogate a datastore and its hosts mounts
#
# Not shown, how to ask a datastore for all the virtual machines it 'owns'
#
# Sample output:
#
# $ virtual_machine_device_info.py -s vcsa -u my_user -i 172.16.254.101
#
# Found Virtual Machine
# =====================
#   guest OS name            : Ubuntu Linux (64-bit)
#   name                     : box
#   last booted timestamp    : 2014-10-13 01:45:57.647340+00:00
#   bios UUID                : 420264ab-848b-1586-b589-b9bd3a71b3aa
#   path to VM               : [storage0] box/box.vmx
#   guest OS id              : ubuntu64Guest
#   host name                : esx_host_01
#   instance UUID            : 500221fe-3473-60ff-fab2-1811600208a0


def get_args():
    parser = argparse.ArgumentParser()

    parser.add_argument('-s', '--host',
                        required=True,
                        action='store',
                        help='Remote host to connect to')

    parser.add_argument('-o', '--port',
                        required=False,
                        action='store',
                        help="port to use, default 443", default=443)

    parser.add_argument('-u', '--user',
                        required=True,
                        action='store',
                        help='User name to use when connecting to host')

    parser.add_argument('-p', '--password',
                        required=False,
                        action='store',
                        help='Password to use when connecting to host')

    parser.add_argument('-d', '--uuid',
                        required=False,
                        action='store',
                        help='Instance UUID (not BIOS id) of a VM to find.')

    parser.add_argument('-i', '--ip',
                        required=False,
                        action='store',
                        help='IP address of the VM to search for')

    parser.add_argument('-v', '--vsanpolicy',
                        required=Truee,
                        action='store',
                        help='ID of Storage Policy to apply')

    args = parser.parse_args()

    password = None
    if args.password is None:
        password = getpass.getpass(
            prompt='Enter password for host %s and user %s: ' %
                   (args.host, args.user))

    args = parser.parse_args()

    if password:
        args.password = password

    return args

args = get_args()

# form a connection...

# Disabling SSL certificate verification
context = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
context.verify_mode = ssl.CERT_NONE

si = connect.SmartConnect(host=args.host, user=args.user, pwd=args.password,
                          port=args.port, sslContext=context)

# Note: from daemons use a shutdown hook to do this, not the atexit
atexit.register(connect.Disconnect, si)

# http://pubs.vmware.com/vsphere-55/topic/com.vmware.wssdk.apiref.doc/vim.SearchIndex.html
search_index = si.content.searchIndex

# without exception find managed objects using durable identifiers that the
# search index can find easily. This is much better than caching information
# that is non-durable and potentially buggy.

vm = None
if args.uuid:
    vm = search_index.FindByUuid(None, args.uuid, True, True)
elif args.ip:
    vm = search_index.FindByIp(None, args.ip, True)

if not vm:
    print(u"Could not find a virtual machine to examine.")
    exit(1)

print(u"Found Virtual Machine")
print(u"=====================")
details = {'name': vm.summary.config.name,
           'instance UUID': vm.summary.config.instanceUuid,
           'bios UUID': vm.summary.config.uuid,
           'path to VM': vm.summary.config.vmPathName,
           'guest OS id': vm.summary.config.guestId,
           'guest OS name': vm.summary.config.guestFullName,
           'host name': vm.runtime.host.name,
           'last booted timestamp': vm.runtime.bootTime}

for name, value in details.items():
    print(u"  {0:{width}{base}}: {1}".format(name, value, width=25, base='s'))


#start config of specs
spec=vim.vm.ConfigSpec()
deviceSpecs=[]
profileSpecs = []
profileSpec = vim.vm.DefinedProfileSpec()
profileSpec.profileId = args.vsanpolicy
profileSpecs.append(profileSpec)
for device in vm.config.hardware.device:
    # diving into each device, we pull out a few interesting bits
    deviceType = type(device).__name__
    if deviceType == "vim.vm.device.VirtualDisk":
      deviceSpec = vim.vm.device.VirtualDeviceSpec()
      deviceSpec.operation = vim.vm.device.VirtualDeviceSpec.Operation.edit
      deviceSpec.device = device
      #deviceSpec.device = vim.vm.device.VirtualDevice()
      #deviceSpec.device.key = device.key
      deviceSpec.profile = profileSpecs
      deviceSpecs.append(deviceSpec)
#should add logic to check if deviceSpecs > 1
spec.deviceChange=deviceSpecs
Task = vm.ReconfigVM_Task(spec)
print("done.")
exit()
