# friendly OO python API module for BootConf 
#
# Michael DeHaan <mdehaan@redhat.com>

import os
import traceback

import config
import util
import sync
import check
from msg import *

class BootAPI:

    """
    Constructor...
    """
    def __init__(self):
       self.last_error = ''
       self.config = config.BootConfig(self)
       self.utils  = util.BootUtil(self,self.config)
       # if the file already exists, load real data now
       try:
           if self.config.files_exist():
              self.config.deserialize()
       except:
           # traceback.print_exc()
           print m("no_cfg")
           try:
               self.config.serialize()
           except:
               traceback.print_exc()
               pass
       if not self.config.files_exist():
           self.config.serialize()

    """
    Forget about current list of profiles, distros, and systems
    """
    def clear(self):
       self.config.clear()

    """
    Return the current list of systems
    """
    def get_systems(self):
       return self.config.get_systems()

    """
    Return the current list of profiles 
    """
    def get_profiles(self):
       return self.config.get_profiles()

    """
    Return the current list of distributions
    """
    def get_distros(self):
       return self.config.get_distros()

    """
    Create a blank, unconfigured system
    """
    def new_system(self):
       return System(self,None)

    """
    Create a blank, unconfigured distro
    """
    def new_distro(self):
       return Distro(self,None)

    """
    Create a blank, unconfigured profile
    """
    def new_profile(self):
       return Profile(self,None)

    """
    See if all preqs for network booting are operational
    """
    def check(self):
       return check.BootCheck(self).run()

    """
    Update the system with what is specified in the config file
    """ 
    def sync(self,dry_run=True):
       self.config.deserialize();
       configurator = sync.BootSync(self)
       configurator.sync(dry_run)

    """
    Save the config file
    """
    def serialize(self):
       self.config.serialize() 
    
    """
    Make the API's internal state reflect that of the config file
    """
    def deserialize(self):
       self.config.deserialize()

#--------------------------------------

"""
Base class for any serializable lists of things...
"""
class Collection:

    """
    Return anything named 'name' in the collection, else return None
    """
    def find(self,name):
        if name in self.listing.keys():
            return self.listing[name]
        return None

    """
    Return datastructure representation (to feed to serializer)
    """
    def to_datastruct(self):
        return [x.to_datastruct() for x in self.listing.values()]
    
     
    """
    Add an object to the collection, if it's valid
    """
    def add(self,ref):
        if ref is None or not ref.is_valid(): 
            if self.api.last_error is None or self.api.last_error == "":
                self.api.last_error = m("bad_param")
            return False
        self.listing[ref.name] = ref
        return True

    """
    Printable representation
    """
    def __str__(self):
        buf = ""
        values = map(lambda(a): str(a), sorted(self.listing.values()))
        if len(values) > 0: 
           return "\n\n".join(values)
        else:
           return m("empty_list")

    def contents(self):
        return self.listing.values()

#--------------------------------------------

"""
A distro represents a network bootable matched set of kernels
and initrd files
"""
class Distros(Collection):

    def __init__(self,api,seed_data):
        self.api = api
        self.listing = {}
        if seed_data is not None:
           for x in seed_data: 
               self.add(Distro(self.api,x))
    """
    Remove element named 'name' from the collection
    """
    def remove(self,name):
        # first see if any Groups use this distro
        for k,v in self.api.get_profiles().listing.items():
            if v.distro == name:
               self.api.last_error = m("orphan_profiles")
               return False
        if self.find(name):
            del self.listing[name]
            return True
        self.api.last_error = m("delete_nothing")
        return False
    

#--------------------------------------------

"""
A profile represents a distro paired with a kickstart file.
For instance, FC5 with a kickstart file specifying OpenOffice
might represent a 'desktop' profile.  For Xen, there are many
additional options, with client-side defaults (not kept here).
"""
class Profiles(Collection):

    def __init__(self,api,seed_data):
        self.api = api
        self.listing = {}
        if seed_data is not None:
           for x in seed_data: 
               self.add(Profile(self.api,x))
    """
    Remove element named 'name' from the collection
    """
    def remove(self,name):
        for k,v in self.api.get_systems().listing.items():
           if v.profile == name:
               self.api.last_error = m("orphan_system")
               return False
        if self.find(name):
            del self.listing[name]
            return True
        self.api.last_error = m("delete_nothing")
        return False
    

#--------------------------------------------

"""
Systems are hostnames/MACs/IP names and the associated profile
they belong to.
"""
class Systems(Collection):

    def __init__(self,api,seed_data):
        self.api = api
        self.listing = {}
        if seed_data is not None:
           for x in seed_data: 
               self.add(System(self.api,x))
    """
    Remove element named 'name' from the collection
    """
    def remove(self,name):
        if self.find(name):
            del self.listing[name]
            return True
        self.api.last_error = m("delete_nothing")
        return False
    

#-----------------------------------------

"""
An Item is a serializable thing that can appear in a Collection
"""
class Item:
  
    """
    All objects have names, and with the exception of System
    they aren't picky about it.
    """
    def set_name(self,name):
        self.name = name
        return True

    def set_kernel_options(self,options_string):
        self.kernel_options = options_string
        return True

    def to_datastruct(self):
        raise "not implemented"
   
    def is_valid(self):
        return False 

#------------------------------------------

class Distro(Item):

    def __init__(self,api,seed_data):
        self.api = api
        self.name = None
        self.kernel = None
        self.initrd = None
        self.kernel_options = ""
        if seed_data is not None:
           self.name = seed_data['name']
           self.kernel = seed_data['kernel']
           self.initrd = seed_data['initrd']
           self.kernel_options = seed_data['kernel_options']

    def set_kernel(self,kernel):
        if self.api.utils.find_kernel(kernel):
            self.kernel = kernel
            return True
        self.api.last_error = m("no_kernel")
        return False

    def set_initrd(self,initrd):
        if self.api.utils.find_initrd(initrd):
            self.initrd = initrd
            return True
        self.api.last_error = m("no_initrd")
        return False

    def is_valid(self):
        for x in (self.name,self.kernel,self.initrd):
            if x is None: return False
        return True

    def to_datastruct(self):
        return { 
           'name': self.name, 
           'kernel': self.kernel, 
           'initrd' : self.initrd,
           'kernel_options' : self.kernel_options
        }

    def __str__(self):
        kstr = self.api.utils.find_kernel(self.kernel)
        istr = self.api.utils.find_initrd(self.initrd)
        if kstr is None:
            kstr = "%s (NOT FOUND!)" % self.kernel
        elif os.path.isdir(self.kernel):
            kstr = "%s (FOUND BY SEARCH)" % kstr
        if istr is None:
            istr = "%s (NOT FOUND)" % self.initrd
        elif os.path.isdir(self.initrd):
            istr = "%s (FOUND BY SEARCH)" % istr
        buf = ""
        buf = buf + "distro      : %s\n" % self.name
        buf = buf + "kernel      : %s\n" % kstr
        buf = buf + "initrd      : %s\n" % istr
        buf = buf + "kernel opts : %s" % self.kernel_options
        return buf

#---------------------------------------------

class Profile(Item):

    def __init__(self,api,seed_data):
        self.api = api
        self.name = None
        self.distro = None # a name, not a reference
        self.kickstart = None
        self.kernel_options = ''
        self.xen_name_prefix = 'xen'
        self.xen_file_path = '/var/xen-files'
        self.xen_file_size = 10240
        self.xen_ram = 2048
        self.xen_mac = ''
        self.xen_paravirt = True
        if seed_data is not None:
           self.name            = seed_data['name']
           self.distro          = seed_data['distro']
           self.kickstart       = seed_data['kickstart'] 
           self.kernel_options  = seed_data['kernel_options']
           self.xen_name_prefix = seed_data['xen_name_prefix']
           self.xen_file_path   = seed_data['xen_file_path']
           self.xen_file_size   = seed_data['xen_ram']
           self.xen_mac         = seed_data['xen_mac']
           self.xen_paravirt    = seed_data['xen_paravirt']

    def set_distro(self,distro_name):
        if self.api.get_distros().find(distro_name):
            self.distro = distro_name
            return True
        self.last_error = m("no_distro")
        return False

    def set_kickstart(self,kickstart):
        if self.api.utils.find_kickstart(kickstart):
            self.kickstart = kickstart
            return True
        self.last_error = m("no_kickstart")
        return False

    def set_xen_name_prefix(self,str):
        # no slashes or wildcards
        for bad in [ '/', '*', '?' ]:
            if str.find(bad) != -1:
                return False
        self.xen_name_prefix = str
        return True

    def set_xen_file_path(self,str):
        # path must look absolute
        if len(str) < 1 or str[0] != "/":
            return False
        self.xen_file_path = str
        return True

    def set_xen_file_size(self,num):
        # num is a non-negative integer (0 means default) 
        try:
            inum = int(num)
            if inum != float(num):
                return False
            self.xen_file_size = inum
            if inum >= 0:
                return True
            return False
        except:
            return False

    def set_xen_mac(self,mac):
        # mac needs to be in mac format AA:BB:CC:DD:EE:FF or a range
        # ranges currently *not* supported, so we'll fail them
        if self.api.utils.is_mac(mac):
            self.xen_mac = mac
            return True
        else:
            return False
   
    def set_xen_paravirt(self,truthiness):
        # truthiness needs to be True or False, or (lcased) string equivalents
        try:
            if (truthiness == False or truthiness.lower() == 'false'):
                self.xen_paravirt = False
            elif (truthiness == True or truthiness.lower() == 'true'):
                self.xen_paravirt = True
            else:
                return False      
        except:
            return False  
        return True

    def is_valid(self):
        for x in (self.name, self.distro):
            if x is None: 
                return False
        return True

    def to_datastruct(self):
        return { 
            'name' : self.name,
            'distro' : self.distro,
            'kickstart' : self.kickstart,
            'kernel_options' : self.kernel_options,
            'xen_name_prefix' : self.xen_name_prefix,
            'xen_file_path'   : self.xen_file_path,
            'xen_file_size'   : self.xen_file_size,
            'xen_ram'         : self.xen_ram,
            'xen_mac'         : self.xen_mac,
            'xen_paravirt'    : self.xen_paravirt
        }

    def __str__(self):
        buf = ""
        buf = buf + "profile         : %s\n" % self.name
        buf = buf + "distro          : %s\n" % self.distro
        buf = buf + "kickstart       : %s\n" % self.kickstart
        buf = buf + "kernel opts     : %s" % self.kernel_options
        buf = buf + "xen name prefix : %s" % self.xen_name_prefix
        buf = buf + "xen file path   : %s" % self.xen_file_path
        buf = buf + "xen file size   : %s" % self.xen_file_size
        buf = buf + "xen ram         : %s" % self.xen_ram
        buf = buf + "xen mac         : %s" % self.xen_mac
        buf = buf + "xen paravirt    : %s" % self.xen_paravirt
        return buf

#---------------------------------------------

class System(Item):

    def __init__(self,api,seed_data):
        self.api = api
        self.name = None
        self.profile = None # a name, not a reference
        self.kernel_options = ""
        if seed_data is not None:
           self.name = seed_data['name']
           self.profile = seed_data['profile']
           self.kernel_options = seed_data['kernel_options']
    
    """
    A name can be a resolvable hostname (it instantly resolved and replaced with the IP), 
    any legal ipv4 address, or any legal mac address. ipv6 is not supported yet but _should_ be.
    See utils.py
    """
    def set_name(self,name):
        new_name = self.api.utils.find_system_identifier(name) 
        if new_name is None or new_name == False:
            self.api.last_error = m("bad_sys_name")
            return False
        self.name = name  # we check it add time, but store the original value.
        return True

    def set_profile(self,profile_name):
        if self.api.get_profiles().find(profile_name):
            self.profile = profile_name
            return True
        return False

    def is_valid(self):
        if self.name is None:
            self.api.last_error = m("bad_sys_name")
            return False
        if self.profile is None:
            return False
        return True

    def to_datastruct(self):
        return {
           'name'   : self.name,
           'profile'  : self.profile,
           'kernel_options' : self.kernel_options
        }

    def __str__(self):
        buf = ""
        buf = buf + "system       : %s\n" % self.name
        buf = buf + "profile      : %s\n" % self.profile
        buf = buf + "kernel opts  : %s" % self.kernel_options
        return buf

