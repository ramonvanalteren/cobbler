# Messages used by bootconf.
# Just consolidated here so they're not in the source.
# No plans on localization any time soon.
# 
# Michael DeHaan <mdehaan@redhat.com>

msg_table = {
  "parse_error"     : "could not parse /etc/bootconf.conf",
  "no_create"       : "cannot create: %s",
  "no_args"         : "this command requires arguments.",
  "missing_options" : "cannot add, all parameters have not been set",
  "unknown_cmd"     : "bootconf doesn't understand '%s'",
  "bad_arg"         : "expecting an equal sign in argument '%s'",
  "reject_arg"      : "the value of parameter '%s' is not valid",
  "weird_arg"       : "this command doesn't take a parameter named '%s'",
  "bad_sys_name"    : "system name must be a MAC, IP, or resolveable host",
  "run_check"       : "run 'bootconf check' and fix errors before running sync",
  "usage"           : "for help, run 'bootconf help'",
  "need_to_fix"     : "the following items need to be corrected:",
  "need_root"       : "bootconf must be run as root",
  "no_dhcpd"        : "can't find dhcpd, try 'yum install dhcpd'",
  "no_pxelinux"     : "can't find pxelinux, try 'yum install pxelinux'", 
  "no_tftpd"        : "can't find tftpd, try 'yum install tftpd'",
  "no_dir"          : "can't find %s, need to create it",
  "chg_attrib"      : "need to change '%s' to '%s' in '%s'",
  "no_exist"        : "%s does not exist",
  "no_line"         : "file '%s' should have a line '%s' somewhere",
  "no_dir2"         : "can't find %s for %s in bootconf.conf", 
  "no_cfg"          : "could not find bootconf.conf, recreating",
  "bad_param"       : "at least one parameter is missing for this function",
  "empty_list"      : "(Empty)",
  "orphan_group"    : "could not delete, distro is referenced by a group",
  "orphan_system"   : "could not delete, group is referenced by a system",
  "delete_nothing"  : "can't delete something that doesn't exist",
  "no_distro"       : "distro does not exist",
  "no_group"        : "group does not exist",
  "no_kickstart"    : "kickstart must be an http://, ftp:// or nfs:// URL",
  "no_kernel"       : "the kernel needs to be a directory containing a kernel, or a full path.  Kernels must be named just 'vmlinuz' or in the form 'vmlinuz-AA.BB.CC-something'",
  "no_initrd"       : "the initrd needs to be a directory containing an initrd, or a full path.  Initrds must be named just 'initrd.img' or in the form 'initrd-AA.BB.CC-something.img",
  "check_ok"        : """
No setup problems found.  

Manual editing of /etc/dhcpd.conf and /etc/bootconf.conf is suggested to tailor them to your specific configuration.  Kickstarts will not work without editing the URL in /etc/bootconf.conf, for instance. Your dhcpd.conf has some PXE related information in it, but it's imposible to tell automatically that it's totally correct in a general sense.  We'll leave this up to you. 

Good luck.
""",
  "help"           : "see 'man bootconf'"
}

"""
Return the lookup of a string key.
"""
def m(key):
   if key in msg_table:
       # localization could use different tables or just gettext.
       return msg_table[key]
   else:
       return "?%s?" % key

