# Virtualization installation functions.  
#
# Copyright 2007-2008 Red Hat, Inc.
# Michael DeHaan <mdehaan@redhat.com>
#
# This software may be freely redistributed under the terms of the GNU
# general public license.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.

import os, sys, time, stat
import tempfile
import random
from optparse import OptionParser
import exceptions
import errno
import re
import virtinst

IMAGE_DIR = "/var/lib/vmware/images"
VMX_DIR = "/var/lib/vmware/vmx"

# FIXME: what to put for guestOS
# FIXME: are other settings ok?
TEMPLATE = """
version = "8"
virtualHW.version = "4"
numvcpus = "2"
scsi0.present = "TRUE"
scsi0.virtualDev = "lsilogic"
scsi0:0.present = "TRUE"
scsi0:0.writeThrough = "TRUE"
ide1:0.present = "TRUE"
ide1:0.deviceType = "cdrom-image"
Ethernet0.present = "TRUE"
Ethernet0.addressType = "static"
Ethernet0.Address = "%(MAC_ADDRESS)s"
Ethernet0.virtualDev = "e1000"
guestOS = "linux"
priority.grabbed = "normal"
priority.ungrabbed = "normal"
powerType.powerOff = "hard"
powerType.powerOn = "hard"
powerType.suspend = "hard"
powerType.reset = "hard"
floppy0.present = "FALSE"
scsi0:0.filename = "%(VMDK_IMAGE)s"
displayName = "%(IMAGE_NAME)s"
memsize = "%(MEMORY)s"
"""
#ide1:0.filename = "%(PATH_TO_ISO)s"

class VirtCreateException(exceptions.Exception):
    pass

def random_mac():
    """
    from xend/server/netif.py
    Generate a random MAC address.
    Uses OUI 00-16-3E, allocated to
    Xensource, Inc.  Last 3 fields are random.
    return: MAC address string
 
    FIXME: if VMware has their own range, adapt to that range
    """
    mac = [ 0x00, 0x16, 0x3e,
        random.randint(0x00, 0x7f),
        random.randint(0x00, 0xff),
        random.randint(0x00, 0xff) ]
    return ':'.join(map(lambda x: "%02x" % x, mac))

def make_disk(disksize,image):
    cmd = "vmware-vdiskmanager -c -a buslogic -s %sMb -t 0 %s" % (disksize, image)
    print "- %s" % cmd
    rc = os.system(cmd)
    if rc != 0:
       raise VirtCreateException("command failed")

def make_vmx(path,vmdk_image,image_name,mac_address,memory):
    template_params =  {
        "VMDK_IMAGE"  : vmdk_image,
        "IMAGE_NAME"  : image_name,
        "MAC_ADDRESS" : mac_address,
        "MEMORY"      : memory
    }
    templated = TEMPLATE % template_params
    fd.open(path,"w+")
    fd.write(templated)
    fd.close()

def register_vm(vmx_file):
    cmd = "vmware-cmd -s register %s" % vmx_file
    print "- %s" % cmd
    rc = os.system(cmd)
    if rc!=0:
       raise VirtCreateException("vmware registration failed")
    
def start_vm(vmx_file):
    cmd = "vmware-cmd %s start" % vmx_file
    print "- %s" % cmd
    rc = os.system(cmd)
    if rc != 0:
       raise VirtCreateException("vm start failed")

def start_install(name=None, ram=None, disks=None, mac=None,
                  uuid=None,  
                  extra=None,
                  vcpus=None, 
                  profile_data=None, bridge=None, arch=None, no_gfx=False, fullvirt=True):

    # starts vmware using PXE.  disk/mem info come from Cobbler
    # rest of the data comes from PXE which is also intended
    # to be managed by Cobbler.

    os.makedirs(IMAGE_DIR)
    os.makedirs(VMX_DIR)

    if len(disks) != 1:
       raise VirtCreateException("vmware support is limited to 1 virtual disk")

    diskname = disks[0][0]
    disksize = disks[0][1]

    image = "%s/%s" % (IMAGE_DIR, name)
    print "- saving virt disk image as %s" % image
    make_disk(disksize,image)
    vmx = "%s/%s" % (VMX_DIR, name)
    print "- saving vmx file as %s" % vmx
    make_vmx(vmx,image,mac,name,ram)
    register_vmx(vmx)
    start_vm(vmx)

