# Test cases for BootConf
#
# Any test case that just is a 'pass' statement needs to be implemented, I just
# didn't want them cluttering up the failure list yet.  And lots more beyond that...
#
# Michael DeHaan <mdehaan@redhat.com>

import api
import sys
import unittest
import os

FAKE_INITRD="/tmp/initrd-2.6.15-1.2054_FAKE.img"
FAKE_INITRD2="/tmp/initrd-2.5.16-2.2055_FAKE.img"
FAKE_INITRD3="/tmp/initrd-1.8.18-3.9999_FAKE.img"
FAKE_KERNEL="/tmp/vmlinuz-2.6.15-1.2054_FAKE"
FAKE_KERNEL2="/tmp/vmlinuz-2.5.16-2.2055_FAKE"
FAKE_KERNEL3="/tmp/vmlinuz-1.8.18-3.9999_FAKE"
FAKE_KICKSTART="http://127.0.0.1/fake.ks"

class BootTest(unittest.TestCase):
    def setUp(self):
        try:
           # it will interfere with results...
           os.remove("/etc/cobbler.conf")
        except:
           pass
        self.api = api.BootAPI()
        self.hostname = os.uname()[1]
        create =  [FAKE_INITRD,FAKE_INITRD2,FAKE_INITRD3,
                   FAKE_KERNEL,FAKE_KERNEL2,FAKE_KERNEL3]
        for fn in create:
            f = open(fn,"w+")
        self.make_basic_config()

    def tearDown(self):
        self.api = None

    def make_basic_config(self):
        distro = self.api.new_distro()
        self.assertTrue(distro.set_name("testdistro0"))
        self.assertTrue(distro.set_kernel(FAKE_KERNEL))
        self.assertTrue(distro.set_initrd(FAKE_INITRD))
        self.assertTrue(self.api.get_distros().add(distro))
        self.assertTrue(self.api.get_distros().find("testdistro0"))

        profile = self.api.new_profile()
        self.assertTrue(profile.set_name("testprofile0"))
        self.assertTrue(profile.set_distro("testdistro0"))
        self.assertTrue(profile.set_kickstart(FAKE_KICKSTART))
        self.assertTrue(self.api.get_profiles().add(profile))
        self.assertTrue(self.api.get_profiles().find("testprofile0"))

        system = self.api.new_system()
        self.assertTrue(system.set_name(self.hostname))
        self.assertTrue(system.set_profile("testprofile0"))
        self.assertTrue(self.api.get_systems().add(system))
        self.assertTrue(self.api.get_systems().find(self.hostname))

class Utilities(BootTest):


    def test_kernel_scan(self):
        self.assertTrue(self.api.utils.find_kernel(FAKE_KERNEL))
        self.assertFalse(self.api.utils.find_kernel("/etc/fstab"))
        self.assertFalse(self.api.utils.find_kernel("filedoesnotexist"))
        self.assertTrue(self.api.utils.find_kernel("/tmp") == FAKE_KERNEL)

    def test_initrd_scan(self):
        self.assertTrue(self.api.utils.find_initrd(FAKE_INITRD))
        self.assertFalse(self.api.utils.find_kernel("/etc/fstab"))
        self.assertFalse(self.api.utils.find_initrd("filedoesnotexist"))
        self.assertTrue(self.api.utils.find_initrd("/tmp") == FAKE_INITRD)
        
    def test_kickstart_scan(self):
        self.assertFalse(self.api.utils.find_kickstart(FAKE_INITRD))
        self.assertFalse(self.api.utils.find_kickstart("filedoesnotexist"))
        self.assertFalse(self.api.utils.find_kickstart("/tmp"))
        self.assertTrue(self.api.utils.find_kickstart("http://bar"))
        self.assertTrue(self.api.utils.find_kickstart("ftp://bar"))
        self.assertTrue(self.api.utils.find_kickstart("nfs://bar"))
        self.assertFalse(self.api.utils.find_kickstart("gopher://bar"))

    def test_matching(self):
        self.assertTrue(self.api.utils.is_mac("00:C0:B7:7E:55:50"))
        self.assertFalse(self.api.utils.is_mac("00:c0:b7:7E:55:50"))
        self.assertFalse(self.api.utils.is_mac("00.D0.B7.7E.55.50"))
        self.assertFalse(self.api.utils.is_mac(self.hostname))
        self.assertTrue(self.api.utils.is_ip("127.0.0.1"))
        self.assertTrue(self.api.utils.is_ip("192.168.1.1"))
        self.assertFalse(self.api.utils.is_ip("00:C0:B7:7E:55:50"))
        self.assertFalse(self.api.utils.is_ip(self.hostname))    

class Additions(BootTest):

    def test_basics(self):
        self.make_basic_config()

    def test_invalid_distro_non_referenced_kernel(self):
        distro = self.api.new_distro()
        self.assertTrue(distro.set_name("testdistro2"))
        self.assertFalse(distro.set_kernel("filedoesntexist"))
        self.assertTrue(distro.set_initrd(FAKE_INITRD))
        self.assertFalse(self.api.get_distros().add(distro))
        self.assertFalse(self.api.get_distros().find("testdistro2"))

    def test_invalid_distro_non_referenced_initrd(self):
        distro = self.api.new_distro()
        self.assertTrue(distro.set_name("testdistro3"))
        self.assertTrue(distro.set_kernel(FAKE_KERNEL))
        self.assertFalse(distro.set_initrd("filedoesntexist"))
        self.assertFalse(self.api.get_distros().add(distro))
        self.assertFalse(self.api.get_distros().find("testdistro3"))
 
    def test_invalid_profile_non_referenced_distro(self):
        profile = self.api.new_profile()
        self.assertTrue(profile.set_name("testprofile11"))
        self.assertFalse(profile.set_distro("distrodoesntexist"))
        self.assertTrue(profile.set_kickstart(FAKE_KICKSTART))
        self.assertFalse(self.api.get_profiles().add(profile))
        self.assertFalse(self.api.get_profiles().find("testprofile2"))

    def test_invalid_profile_kickstart_not_url(self):
        profile = self.api.new_profile()
        self.assertTrue(profile.set_name("testprofile12"))
        self.assertTrue(profile.set_distro("testdistro0"))
        self.assertFalse(profile.set_kickstart("kickstartdoesntexist"))
        # since kickstarts are optional, you can still add it
        self.assertTrue(self.api.get_profiles().add(profile))
        self.assertTrue(self.api.get_profiles().find("testprofile12"))
        # now verify the other kickstart forms would still work
        self.assertTrue(profile.set_kickstart("http://bar"))
        self.assertTrue(profile.set_kickstart("ftp://bar"))
        self.assertTrue(profile.set_kickstart("nfs://bar"))

    def test_profile_xen_parameter_checking(self):
        profile = self.api.new_profile()
        self.assertTrue(profile.set_name("testprofile12b"))
        self.assertTrue(profile.set_distro("testdistro0"))
        self.assertTrue(profile.set_kickstart("http://127.0.0.1/foo"))
        # no slashes or wildcards in name
        self.assertTrue(profile.set_xen_name("xen"))
        self.assertTrue(profile.set_xen_name("xen"))
        self.assertFalse(profile.set_xen_name("xen/foo"))
        self.assertFalse(profile.set_xen_name("xen*foo"))
        self.assertFalse(profile.set_xen_name("xen?foo"))
        # sizes must be integers
        self.assertTrue(profile.set_xen_file_size("54321"))
        self.assertFalse(profile.set_xen_file_size("huge"))
        self.assertFalse(profile.set_xen_file_size("54321.23"))
        # macs must be properly formatted
        self.assertTrue(profile.set_xen_mac("AA:BB:CC:DD:EE:FF"))
        self.assertFalse(profile.set_xen_mac("AA-BB-CC-DD-EE-FF")) 
        # paravirt must be 'true' or 'false'
        self.assertFalse(profile.set_xen_mac("cowbell"))
        self.assertTrue(profile.set_xen_paravirt('true'))
        self.assertTrue(profile.set_xen_paravirt('fALsE'))
        self.assertFalse(profile.set_xen_paravirt('sputnik'))
        self.assertFalse(profile.set_xen_paravirt(11))
        # each item should be 'true' now, so we can add it
        # since the failed items don't affect status
        self.assertTrue(self.api.get_profiles().add(profile))

    def test_invalid_system_bad_name_host(self):
        system = self.api.new_system()
        name = "hostnamewontresolveanyway"
        self.assertFalse(system.set_name(name))
        self.assertTrue(system.set_profile("testprofile0"))
        self.assertFalse(self.api.get_systems().add(system))
        self.assertFalse(self.api.get_systems().find(name))

    def test_system_name_is_a_MAC(self):
        system = self.api.new_system()
        name = "00:16:41:14:B7:71"
        self.assertTrue(system.set_name(name))
        self.assertTrue(system.set_profile("testprofile0"))
        self.assertTrue(self.api.get_systems().add(system))
        self.assertTrue(self.api.get_systems().find(name))

    def test_system_name_is_an_IP(self):
        system = self.api.new_system()
        name = "192.168.1.54"
        self.assertTrue(system.set_name(name))
        self.assertTrue(system.set_profile("testprofile0"))
        self.assertTrue(self.api.get_systems().add(system))
        self.assertTrue(self.api.get_systems().find(name))

    def test_invalid_system_non_referenced_profile(self):
        system = self.api.new_system()
        self.assertTrue(system.set_name(self.hostname))
        self.assertFalse(system.set_profile("profiledoesntexist"))
        self.assertFalse(self.api.get_systems().add(system))

class Deletions(BootTest):
  
    def test_invalid_delete_profile_doesnt_exist(self):
        self.assertFalse(self.api.get_profiles().remove("doesnotexist"))

    def test_invalid_delete_profile_would_orphan_systems(self):
        self.make_basic_config()
        self.assertFalse(self.api.get_profiles().remove("testprofile0"))

    def test_invalid_delete_system_doesnt_exist(self):
        self.assertFalse(self.api.get_systems().remove("doesnotexist"))

    def test_invalid_delete_distro_doesnt_exist(self):
        self.assertFalse(self.api.get_distros().remove("doesnotexist"))

    def test_invalid_delete_distro_would_orphan_profile(self):
        self.make_basic_config()
        self.assertFalse(self.api.get_distros().remove("testdistro0"))
        
    def test_working_deletes(self):
        self.api.clear()
        self.make_basic_config()
        self.assertTrue(self.api.get_systems().remove(self.hostname))
        self.api.serialize()
        self.assertTrue(self.api.get_profiles().remove("testprofile0"))
        self.assertTrue(self.api.get_distros().remove("testdistro0"))
        self.assertFalse(self.api.get_systems().find(self.hostname))
        self.assertFalse(self.api.get_profiles().find("testprofile0"))
        self.assertFalse(self.api.get_distros().find("testdistro0"))

class TestSerialization(BootTest):
   
   def test_serialization(self):
       self.make_basic_config()
       self.api.serialize()
       self.api.clear()
       self.assertFalse(self.api.get_systems().find(self.hostname))
       self.assertFalse(self.api.get_profiles().find("testprofile0"))
       self.assertFalse(self.api.get_distros().find("testdistro0"))
       self.api.deserialize()
       self.assertTrue(self.api.get_systems().find(self.hostname))
       self.assertTrue(self.api.get_profiles().find("testprofile0"))
       self.assertTrue(self.api.get_distros().find("testdistro0"))
       

class TestCheck(BootTest):
  
   def test_check(self):
       # we can't know if it's supposed to fail in advance
       # (ain't that the halting problem), but it shouldn't ever
       # throw exceptions.
       self.api.check()

class TestSync(BootTest):
  
   def test_dry_run(self):
       # WARNING: dry run isn't implemented yet, so no test
       # we don't want to run a real 'sync' in an automated context
       pass

   def test_real_run(self):
       # testing sync could mess up a valid install, so unless
       # a re-homing option is added, don't write a test for this
       # it wouldn't be comprehensive anyway
       pass

if __name__ == "__main__":
    if os.getuid()!=0:
        print "root would be nice"
        sys.exit(1) 
    unittest.main()

