"""
This is the SSH based deploy code.
Also does power management

Copyright 2006-2009, Red Hat, Inc
Michael DeHaan <mdehaan@redhat.com>
Scott Henson <shenson@redhat.com>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
02110-1301  USA
"""

#from cexceptions import *
#import random

def register():
    """
    The mandatory cobbler module registration hook.
    """
    return "deploy"

def  __find_host(api, virt_group):
    """
    Find a system in the virtual group specified
    """

    systems = api.find_system(virt_group=virt_group, return_list = True)
    if len(systems) == 0:
        raise CX("No systems were found in virtual group %s" % virt_group)

    # FIXME: temporary hack, should find number of systems in the 
    # virtual group with the least number of virtual systems pointing
    # to it

    return random.choice(systems)

# -------------------------------------------------------

def deploy(api, system, virt_host = None, virt_group=None):
    """
    Deploy the current system to the virtual host or virtual group
    """
    if virt_host is None and virt_group is not None:
        virt_host = __find_host(api, virt_group)

    if virt_host is None and system.virt_group == '':
        virt_host = __find_host(api, system.virt_group)

    if system.virt_host != '':
        virt_host = system.virt_host

    if virt_host is None:
        raise CX("No host specified for deployment.")

    if virt_host.host_name == "":
        raise CX("System hostname for (%s) not set" % virt_host.name)

    cmd = "ssh %s koan --virt --system=%s" % (virt_host.host_name, system.name)
    print "- %s" % cmd
    rc = sub_process.call(cmd)
    if rc != 0:
        raise CX("remote deployment failed")


# -------------------------------------------------------

def delete(system):
    """
    Delete the virt system
    """
    raise CX("Removing a virtual instance is not implemented yet.")


