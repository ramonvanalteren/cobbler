#!/usr/bin/env python




##################################################
## DEPENDENCIES
import sys
import os
import os.path
from os.path import getmtime, exists
import time
import types
import __builtin__
from Cheetah.Version import MinCompatibleVersion as RequiredCheetahVersion
from Cheetah.Version import MinCompatibleVersionTuple as RequiredCheetahVersionTuple
from Cheetah.Template import Template
from Cheetah.DummyTransaction import DummyTransaction
from Cheetah.NameMapper import NotFound, valueForName, valueFromSearchList, valueFromFrameOrSearchList
from Cheetah.CacheRegion import CacheRegion
import Cheetah.Filters as Filters
import Cheetah.ErrorCatchers as ErrorCatchers

##################################################
## MODULE CONSTANTS
try:
    True, False
except NameError:
    True, False = (1==1), (1==0)
VFFSL=valueFromFrameOrSearchList
VFSL=valueFromSearchList
VFN=valueForName
currentTime=time.time
__CHEETAH_version__ = '2.0rc8'
__CHEETAH_versionTuple__ = (2, 0, 0, 'candidate', 8)
__CHEETAH_genTime__ = 1192820351.713706
__CHEETAH_genTimestamp__ = 'Fri Oct 19 14:59:11 2007'
__CHEETAH_src__ = 'webui_templates/master.tmpl'
__CHEETAH_srcLastModified__ = 'Fri Oct 12 11:53:14 2007'
__CHEETAH_docstring__ = 'Autogenerated by CHEETAH: The Python-Powered Template Engine'

if __CHEETAH_versionTuple__ < RequiredCheetahVersionTuple:
    raise AssertionError(
      'This template was compiled with Cheetah version'
      ' %s. Templates compiled before version %s must be recompiled.'%(
         __CHEETAH_version__, RequiredCheetahVersion))

##################################################
## CLASSES

class master(Template):

    ##################################################
    ## CHEETAH GENERATED METHODS


    def __init__(self, *args, **KWs):

        Template.__init__(self, *args, **KWs)
        if not self._CHEETAH__instanceInitialized:
            cheetahKWArgs = {}
            allowedKWs = 'searchList namespaces filter filtersLib errorCatcher'.split()
            for k,v in KWs.items():
                if k in allowedKWs: cheetahKWArgs[k] = v
            self._initCheetahInstance(**cheetahKWArgs)
        

    def body(self, **KWS):



        ## CHEETAH: generated from #block body at line 60, col 1.
        trans = KWS.get("trans")
        if (not trans and not self._CHEETAH__isBuffering and not callable(self.transaction)):
            trans = self.transaction # is None unless self.awake() was called
        if not trans:
            trans = DummyTransaction()
            _dummyTrans = True
        else: _dummyTrans = False
        write = trans.response().write
        SL = self._CHEETAH__searchList
        _filter = self._CHEETAH__currentFilter
        
        ########################################
        ## START - generated method body
        
        write('''
    <h1 style="color: red;">Template Failure</h1>

''')
        
        ########################################
        ## END - generated method body
        
        return _dummyTrans and trans.response().getvalue() or ""
        

    def respond(self, trans=None):



        ## CHEETAH: main method generated for this template
        if (not trans and not self._CHEETAH__isBuffering and not callable(self.transaction)):
            trans = self.transaction # is None unless self.awake() was called
        if not trans:
            trans = DummyTransaction()
            _dummyTrans = True
        else: _dummyTrans = False
        write = trans.response().write
        SL = self._CHEETAH__searchList
        _filter = self._CHEETAH__currentFilter
        
        ########################################
        ## START - generated method body
        
        write('''<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xml:lang="en" lang="en" xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>''')
        _v = VFFSL(SL,"title",True) # '$title' on line 5, col 12
        if _v is not None: write(_filter(_v, rawExpr='$title')) # from line 5, col 12.
        write('''</title>
    <meta http-equiv="Content-Type" content="text/html;charset=utf-8"/>

    <link rel="stylesheet" type="text/css" media="all" href="/cobbler/webui/style.css" />
    <link rel="stylesheet" type="text/css" media="all" href="/cobbler/webui/cobblerweb.css" />

<script language="Javascript" src="/cobbler/webui/cobbler.js" ></script>

</head>


<body onload="global_onload();">

<div id="wrap">
    <h1 id="masthead">
        <a href="''')
        _v = VFFSL(SL,"base_url",True) # '$base_url' on line 20, col 18
        if _v is not None: write(_filter(_v, rawExpr='$base_url')) # from line 20, col 18.
        write('''/index">
            <img alt="Cobbler Logo"
                 src="/cobbler/webui/logo-cobbler.png"/>
        </a>
    </h1>
</div>

<div id="main">

<div id="sidebar">
    <ul id="nav">
''')
        if not VFFSL(SL,"logged_in",True): # generated from line 31, col 9
            write('''            <li><a href="''')
            _v = VFFSL(SL,"base_url",True) # '$base_url' on line 32, col 26
            if _v is not None: write(_filter(_v, rawExpr='$base_url')) # from line 32, col 26.
            write('''/login" class="menu">Log In</a></li>
''')
        else: # generated from line 33, col 9
            write('''            <li><a href="/cobbler/webui/wui.html" class="menu">Docs</a></li>
            <li><a href="''')
            _v = VFFSL(SL,"base_url",True) # '$base_url' on line 35, col 26
            if _v is not None: write(_filter(_v, rawExpr='$base_url')) # from line 35, col 26.
            write('''/settings_view" class="menu">Settings</a></li>
            <li><a href="''')
            _v = VFFSL(SL,"base_url",True) # '$base_url' on line 36, col 26
            if _v is not None: write(_filter(_v, rawExpr='$base_url')) # from line 36, col 26.
            write('''/logout_submit" class="menu">Log Out</a></li>
            <li><hr/></li>
            <li>LIST</li>
            <li><a href="''')
            _v = VFFSL(SL,"base_url",True) # '$base_url' on line 39, col 26
            if _v is not None: write(_filter(_v, rawExpr='$base_url')) # from line 39, col 26.
            write('''/distro_list" class="menu">Distros</a></li>
            <li><a href="''')
            _v = VFFSL(SL,"base_url",True) # '$base_url' on line 40, col 26
            if _v is not None: write(_filter(_v, rawExpr='$base_url')) # from line 40, col 26.
            write('''/profile_list" class="menu">Profiles</a></li>
            <li><a href="''')
            _v = VFFSL(SL,"base_url",True) # '$base_url' on line 41, col 26
            if _v is not None: write(_filter(_v, rawExpr='$base_url')) # from line 41, col 26.
            write('''/system_list" class="menu">Systems</a></li>
            <li><a href="''')
            _v = VFFSL(SL,"base_url",True) # '$base_url' on line 42, col 26
            if _v is not None: write(_filter(_v, rawExpr='$base_url')) # from line 42, col 26.
            write('''/ksfile_list" class="menu">Kickstarts</a></li>
            <li><a href="''')
            _v = VFFSL(SL,"base_url",True) # '$base_url' on line 43, col 26
            if _v is not None: write(_filter(_v, rawExpr='$base_url')) # from line 43, col 26.
            write('''/repo_list" class="menu">Repos</a></li>
            <li><hr/></li>
            <li>ADD</li>
            <li><a href="''')
            _v = VFFSL(SL,"base_url",True) # '$base_url' on line 46, col 26
            if _v is not None: write(_filter(_v, rawExpr='$base_url')) # from line 46, col 26.
            write('''/distro_edit" class="menu">Distro</a></li>
            <li><a href="''')
            _v = VFFSL(SL,"base_url",True) # '$base_url' on line 47, col 26
            if _v is not None: write(_filter(_v, rawExpr='$base_url')) # from line 47, col 26.
            write('''/profile_edit" class="menu">Profile</a></li>
            <li><a href="''')
            _v = VFFSL(SL,"base_url",True) # '$base_url' on line 48, col 26
            if _v is not None: write(_filter(_v, rawExpr='$base_url')) # from line 48, col 26.
            write('''/subprofile_edit" class="menu">Subprofile</a></li>
            <li><a href="''')
            _v = VFFSL(SL,"base_url",True) # '$base_url' on line 49, col 26
            if _v is not None: write(_filter(_v, rawExpr='$base_url')) # from line 49, col 26.
            write('''/system_edit" class="menu">System</a></li>
            <li><a href="''')
            _v = VFFSL(SL,"base_url",True) # '$base_url' on line 50, col 26
            if _v is not None: write(_filter(_v, rawExpr='$base_url')) # from line 50, col 26.
            write('''/repo_edit" class="menu">Repo</a></li>
            <li><hr/><br/></li>
            <li><a class="button sync" href="''')
            _v = VFFSL(SL,"base_url",True) # '$base_url' on line 52, col 46
            if _v is not None: write(_filter(_v, rawExpr='$base_url')) # from line 52, col 46.
            write('''/sync">Sync</a></li>
''')
        write('''

    </ul>
</div>

<div id="content">
''')
        self.body(trans=trans)
        write('''</div><!-- content -->
</div><!-- main -->

</body>
</html>
''')
        
        ########################################
        ## END - generated method body
        
        return _dummyTrans and trans.response().getvalue() or ""
        
    ##################################################
    ## CHEETAH GENERATED ATTRIBUTES


    _CHEETAH__instanceInitialized = False

    _CHEETAH_version = __CHEETAH_version__

    _CHEETAH_versionTuple = __CHEETAH_versionTuple__

    _CHEETAH_genTime = __CHEETAH_genTime__

    _CHEETAH_genTimestamp = __CHEETAH_genTimestamp__

    _CHEETAH_src = __CHEETAH_src__

    _CHEETAH_srcLastModified = __CHEETAH_srcLastModified__

    title = "Cobbler Web Interface"

    _mainCheetahMethod_for_master= 'respond'

## END CLASS DEFINITION

if not hasattr(master, '_initCheetahAttributes'):
    templateAPIClass = getattr(master, '_CHEETAH_templateClass', Template)
    templateAPIClass._addCheetahPlumbingCodeToClass(master)


# CHEETAH was developed by Tavis Rudd and Mike Orr
# with code, advice and input from many other volunteers.
# For more information visit http://www.CheetahTemplate.org/

##################################################
## if run from command line:
if __name__ == '__main__':
    from Cheetah.TemplateCmdLineIface import CmdLineIface
    CmdLineIface(templateObj=master()).run()


