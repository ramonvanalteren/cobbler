"""
A cobbler distribution.  A distribution is a kernel, and initrd, and potentially
some kernel options.

Copyright 2006, Red Hat, Inc
Michael DeHaan <mdehaan@redhat.com>

This software may be freely redistributed under the terms of the GNU
general public license.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
"""


import utils
import item
import weakref
import os
from cexceptions import *

from rhpl.translate import _, N_, textdomain, utf8

class Distro(item.Item):

    TYPE_NAME = _("distro")

    def clear(self):
        """
        Reset this object.
        """
        self.name = None
        self.kernel = None
        self.initrd = None
        self.kernel_options = {}
        self.ks_meta = {}
        self.arch = "x86"
        self.breed = "redhat"
        self.source_repos = []

    def make_clone(self):
        ds = self.to_datastruct()
        cloned = Distro(self.config)
        cloned.from_datastruct(ds)
        return cloned

    def get_parent(self):
        """
        Return object next highest up the tree.
        """
        return None

    def from_datastruct(self,seed_data):
        """
        Modify this object to take on values in seed_data
        """
        self.name           = self.load_item(seed_data,'name')
        self.kernel         = self.load_item(seed_data,'kernel')
        self.initrd         = self.load_item(seed_data,'initrd')
        self.kernel_options = self.load_item(seed_data,'kernel_options')
        self.ks_meta        = self.load_item(seed_data,'ks_meta')
        self.arch           = self.load_item(seed_data,'arch','x86')
        self.breed          = self.load_item(seed_data,'breed','redhat')
        self.source_repos   = self.load_item(seed_data,'source_repos',[])

        # backwards compatibility -- convert string entries to dicts for storage
        if type(self.kernel_options) != dict:
            self.set_kernel_options(self.kernel_options)
        if type(self.ks_meta) != dict:
            self.set_ksmeta(self.ks_meta)
        return self

    def set_kernel(self,kernel):
        """
	Specifies a kernel.  The kernel parameter is a full path, a filename
	in the configured kernel directory (set in /etc/cobbler.conf) or a
	directory path that would contain a selectable kernel.  Kernel
	naming conventions are checked, see docs in the utils module
	for find_kernel.
	"""
        if utils.find_kernel(kernel):
            self.kernel = kernel
            return True
        raise CX(_("kernel not found"))

    def set_breed(self, breed):
        if breed is not None and breed.lower() in [ "redhat", "suse" ]:
            self.breed = breed.lower()
            return True
        raise CX(_("invalid value for --breed, see manpage"))

    def set_initrd(self,initrd):
        """
	Specifies an initrd image.  Path search works as in set_kernel.
	File must be named appropriately.
	"""
        if utils.find_initrd(initrd):
            self.initrd = initrd
            return True
        raise CX(_("initrd not found"))

    def set_source_repos(self, repos):
        """
        A list of http:// URLs on the cobbler server that point to
        yum configuration files that can be used to
        install core packages.  Use by cobbler import only.
        """
        self.source_repos = repos

    def set_arch(self,arch):
        """
        The field is mainly relevant to PXE provisioning.

        Should someone have Itanium machines on a network, having
        syslinux (pxelinux.0) be the only option in the config file causes
        problems.

        Using an alternative distro type allows for dhcpd.conf templating
        to "do the right thing" with those systems -- this also relates to
        bootloader configuration files which have different syntax for different
        distro types (because of the bootloaders).

        This field is named "arch" because mainly on Linux, we only care about
        the architecture, though if (in the future) new provisioning types
        are added, an arch value might be something like "bsd_x86".
        """
        if arch in [ "standard", "ia64", "x86", "x86_64" ]:
            self.arch = arch
            return True
        raise CX(_("PXE arch choices include: x86, x86_64, and ia64"))

    def is_valid(self):
        """
	A distro requires that the kernel and initrd be set.  All
	other variables are optional.
	"""
        for x in (self.name,self.kernel,self.initrd):
            if x is None: return False
        return True

    def to_datastruct(self):
        """
        Return a serializable datastructure representation of this object.
        """
        return {
           'name'           : self.name,
           'kernel'         : self.kernel,
           'initrd'         : self.initrd,
           'kernel_options' : self.kernel_options,
           'ks_meta'        : self.ks_meta,
           'arch'           : self.arch,
           'breed'          : self.breed,
           'source_repos'   : self.source_repos
        }

    def printable(self):
        """
	Human-readable representation.
	"""
        kstr = utils.find_kernel(self.kernel)
        istr = utils.find_initrd(self.initrd)
        buf =       _("distro          : %s\n") % self.name
        buf = buf + _("kernel          : %s\n") % kstr
        buf = buf + _("initrd          : %s\n") % istr
        buf = buf + _("kernel options  : %s\n") % self.kernel_options
        buf = buf + _("architecture    : %s\n") % self.arch
        buf = buf + _("ks metadata     : %s\n") % self.ks_meta
        buf = buf + _("breed           : %s\n") % self.breed
        # FIXME: temporary
        buf = buf + _("children        : %s\n") % self.get_children()
        buf = buf + _("descendants     : %s\n") % self.get_descendants()
        return buf

