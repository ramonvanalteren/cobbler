from django.template.loader import get_template
from django.template import Context
from django.template import RequestContext
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from mod_python import apache

import xmlrpclib
import time
import simplejson
import string
import distutils
import exceptions
import time

import cobbler.item_distro  as item_distro
import cobbler.item_profile as item_profile
import cobbler.item_system  as item_system
import cobbler.item_repo    as item_repo
import cobbler.item_image   as item_image
import cobbler.item_network as item_network
import cobbler.field_info   as field_info

my_uri = "http://127.0.0.1/cobbler_api"
remote = None
token = None
username = None

#==================================================================================

def authenhandler(req):
    """
    Mod python security handler.   Logs into XMLRPC and saves the token
    for later use.
    """

    global remote
    global token
    global username

    password = req.get_basic_auth_pw()
    username = req.user     
    try:
        remote = xmlrpclib.Server(my_uri, allow_none=True)
        token = remote.login(username, password)
        remote.update(token)
        return apache.OK
    except:
        return apache.HTTP_UNAUTHORIZED

#==================================================================================


def index(request):
   """
   This is the main greeting page for cobbler web.  
   """
   t = get_template('index.tmpl')
   html = t.render(Context({
        'version': remote.version(token), 
        'username':username
   }))
   return HttpResponse(html)

#========================================================================

def task_created(request):
   """
   Let's the user know what to expect for task updates.
   """
   t = get_template("task_created.tmpl")
   html = t.render(Context({
       'username' : username
   }))
   return HttpResponse(html)

#========================================================================

def error_page(request,message):
   """
   This page is used to explain error messages to the user.
   """
   # FIXME: test and make sure we use this rather than throwing lots of tracebacks for
   # field errors
   t = get_template('error_page.tmpl')
   message = message.replace("<Fault 1: \"<class 'cobbler.cexceptions.CX'>:'","Remote exception: ")
   message = message.replace(": '\">","")
   html = t.render(Context({
       'message': message,
       'username': username
   }))
   return HttpResponse(html)

#==================================================================================

def get_fields(what, is_subobject, seed_item=None):
  
    """
    Helper function.  Retrieves the field table from the cobbler objects
    and formats it in a way to make it useful for Django templating.
    The field structure indicates what fields to display and what the default
    values are, etc.
    """

    if what == "distro":
       field_data = item_distro.FIELDS
    if what == "profile":
       field_data = item_profile.FIELDS
    if what == "system":
       field_data = item_system.FIELDS
    if what == "repo":
       field_data = item_repo.FIELDS
    if what == "image":
       field_data =  item_image.FIELDS
    if what == "network":
       field_data = item_network.FIELDS

    settings = remote.get_settings()
  
    fields = []
    for row in field_data:

        # if we are subprofile and see the field "distro", make it say parent
        # with this really sneaky hack here
        if is_subobject and row[0] == "distro":
            row[0] = "parent"
            row[3] = "Parent object"
            row[5] = "Inherit settings from this profile" 
            row[6] = []

        elem = {
            "name"                    : row[0],
            "value"                   : "?",
            "caption"                 : row[3],
            "editable"                : row[4],
            "tooltip"                 : row[5],
            "choices"                 : row[6],
            "css_class"               : "generic",
            "html_element"            : "generic",
        }


        if not elem["editable"]:
            continue

        if seed_item is not None:
            if row[0].startswith("*"):
                # system interfaces are loaded by javascript, not this
                elem["value"]             = ""
                elem["name"]              = row[0].replace("*","")
            elif row[0].find("widget") == -1:
                elem["value"]             = seed_item[row[0]]
        elif is_subobject:
            elem["value"]             = row[2]
        else:
            elem["value"]             = row[1]

        if elem["value"] is None:
            elem["value"] = ""

        # we'll process this for display but still need to present the original to some
        # template logic
        elem["value_raw"]             = elem["value"]

        if isinstance(elem["value"],basestring) and elem["value"].startswith("SETTINGS:"):
            key = elem["value"].replace("SETTINGS:","",1)
            elem["value"] = settings[key]

        # flatten hashes of all types, they can only be edited as text
        # as we have no HTML hash widget (yet)
        if type(elem["value"]) == type({}):
            tokens = []
            for (x,y) in elem["value"].items():
               if y is not None:
                  tokens.append("%s=%s" % (x,y))
               else:
                  tokens.appned("%s" % x)
            elem["value"] = " ".join(tokens)
 
        name = row[0]
        if name.find("_widget") != -1:
            elem["html_element"] = "widget"
        elif name in field_info.USES_SELECT:
            elem["html_element"] = "select"
        elif name in field_info.USES_MULTI_SELECT:
            elem["html_element"] = "multiselect"
        elif name in field_info.USES_RADIO:
            elem["html_element"] = "radio"
        elif name in field_info.USES_CHECKBOX:
            elem["html_element"] = "checkbox"
        elif name in field_info.USES_TEXTAREA:
            elem["html_element"] = "textarea"
        else:
            elem["html_element"] = "text"

        elem["css_class"] = field_info.CSS_MAPPINGS.get(name, "genericedit")
        
        # flatten lists for those that aren't using select boxes
        if type(elem["value"]) == type([]):
            if elem["html_element"] != "select":
                elem["value"] = string.join(elem["value"], sep=" ")

        # FIXME: need to handle interfaces special, they are prefixed with "*"

        fields.append(elem)

    return fields

#==================================================================================

def __tweak_field(fields,field_name,attribute,value):
    """
    Helper function to insert extra data into the field list.
    """
    # FIXME: eliminate this function.
    for x in fields:
       if x["name"] == field_name:
           x[attribute] = value

#==================================================================================


def __format_items(items, column_names):
    """
    Format items retrieved from XMLRPC for rendering by the generic_edit template
    """
    dataset = []
    for itemhash in items:
        row = []
        for fieldname in column_names:
            row.append([fieldname,itemhash[fieldname]])
        dataset.append(row)
    return dataset

#==================================================================================

def genlist(request, what, page=None):
    """
    Lists all object types, complete with links to actions
    on those objects.
    """

    # get details from the session
    if page == None:
        page = int(request.session.get("%s_page" % what, 1))
    limit = int(request.session.get("%s_limit" % what, 50))   
    sort_field = request.session.get("%s_sort_field" % what, None)  # FIXME: no UI for this?
    filters = simplejson.loads(request.session.get("%s_filters" % what, "{}"))
    pageditems = remote.find_items_paged(what,filters,sort_field,page,limit)

    # what columns to show for each page?
    if what == "distro":
       columns = [ "name" ]
    if what == "profile":
       columns = [ "name", "distro" ]
    if what == "system":
       # FIXME: also list network, once working
       columns = [ "name", "profile", "netboot_enabled" ] 
    if what == "repo":
       columns = [ "name", "mirror" ]
    if what == "image":
       columns = [ "name", "file" ]
    if what == "network":
       columns = [ "name" ] 

    # render the list
    t = get_template('generic_list.tmpl')
    html = t.render(RequestContext(request,{
        'what'           : what,
        'otypes'         : [ "distro", "profile", "image" ], # controls linking in fields
        'columns'        : columns,
        'items'          : __format_items(pageditems["items"],columns),
        'pageinfo'       : pageditems["pageinfo"],
        'filters'        : filters,
        'username'       : username,
    }))
    return HttpResponse(html)


def modify_list(request, what, pref, value=None):
    """
    This function is used in the generic list view
    to modify the page/column sort/number of items 
    shown per page, and also modify the filters.

    This function modifies the session object to 
    store these preferences persistently.
    """


    # what preference are we tweaking?

    if pref == "sort":

        # FIXME: this isn't exposed in the UI.

        # sorting list on columns
        old_sort = request.session.get("%s_sort_field" % what,"")
        if old_sort.startswith("!"):
            old_sort = old_sort[1:]
            old_revsort = True
        else:
            old_revsort = False
        # User clicked on the column already sorted on, 
        # so reverse the sorting list
        if old_sort == value and not old_revsort:
            value = "!" + value
        request.session["%s_sort_field" % what] = value
        request.session["%s_page" % what] = 1

    elif pref == "limit":
        # number of items to show per page
        request.session["%s_limit" % what] = int(value)
        request.session["%s_page" % what] = 1

    elif pref == "page":
        # what page are we currently on
        request.session["%s_page" % what] = int(value)

    elif pref in ("addfilter","removefilter"):
        # filters limit what we show in the lists
        # they are stored in json format for marshalling
        filters = simplejson.loads(request.session.get("%s_filters" % what, "{}"))
        if pref == "addfilter":
            (field_name, field_value) = value.split(":", 1)
            # add this filter
            filters[field_name] = field_value
        else:
            # remove this filter, if it exists
            if filters.has_key(value):
                del filters[value]
        # save session variable
        request.session["%s_filters" % what] = simplejson.dumps(filters)
        # since we changed what is viewed, reset the page
        request.session["%s_page" % what] = 1

    else:
        return error_page(request, "Invalid preference change request")

    # redirect to the list page
    return HttpResponseRedirect("/cobbler_web/%s/list" % what)

# ======================================================================

def generic_rename(request, what, obj_name=None, obj_newname=None):

   """
   Renames an object.
   """

   if obj_name == None:
      return error_page(request,"You must specify a %s to rename" % what)
   if not remote.has_item(what,obj_name):
      return error_page(request,"Unknown %s specified" % what)
   elif not remote.check_access_no_fail(token, "modify_%s" % what, obj_name):
      return error_page(request,"You do not have permission to rename this %s" % what)
   else:
      obj_id = remote.get_item_handle(what, obj_name, token)
      remote.rename_item(what, obj_id, obj_newname, token)
      return HttpResponseRedirect("/cobbler_web/%s/list" % what)

# ======================================================================

def generic_copy(request, what, obj_name=None, obj_newname=None):
   """
   Copies an object.
   """
   # FIXME: shares all but one line with rename, merge it.
   if obj_name == None:
      return error_page(request,"You must specify a %s to rename" % what)
   if not remote.has_item(what,obj_name):
      return error_page(request,"Unknown %s specified" % what)
   elif not remote.check_access_no_fail(token, "modify_%s" % what, obj_name):
      return error_page(request,"You do not have permission to copy this %s" % what)
   else:
      obj_id = remote.get_item_handle(what, obj_name, token)
      remote.copy_item(what, obj_id, obj_newname, token)
      return HttpResponseRedirect("/cobbler_web/%s/list" % what)

# ======================================================================

def generic_delete(request, what, obj_name=None):
   """
   Deletes an object.
   """
   # FIXME: consolidate code with above functions.
   if obj_name == None:
      return error_page(request,"You must specify a %s to delete" % what)
   if not remote.has_item(what,obj_name):
      return error_page(request,"Unknown %s specified" % what)
   elif not remote.check_access_no_fail(token, "remove_%s" % what, obj_name):
      return error_page(request,"You do not have permission to delete this %s" % what)
   else:  
      remote.remove_item(what, obj_name, token)
      return HttpResponseRedirect("/cobbler_web/%s/list" % what)


# ======================================================================

def generic_domulti(request, what, multi_mode=None, multi_arg=None):

    """
    Process operations like profile reassignment, netboot toggling, and deletion
    which occur on all items that are checked on the list page.
    """

    # FIXME: cleanup
    # FIXME: COMMENTS!!!11111???

    names = request.POST.get('names', '').strip().split()
    if names == "":
        return error_page(request, "Need to select some systems first")        

    if multi_mode == "delete":
        # too dangerous to expose?
        # for obj_name in names:
        #    remote.remove_item(what,obj_name, token)
        pass
    elif what == "system" and multi_mode == "netboot":
        netboot_enabled = multi_arg # values: enable or disable
        if netboot_enabled is None:
            return error_page(request,"Cannot modify systems without specifying netboot_enabled")
        if netboot_enabled == "enable":
            netboot_enabled = True
        elif netboot_enabled == "disable":
            netboot_enabled = False
        else:
            return error_page(request,"Invalid netboot option, expect enable or disable")
        for obj_name in names:
            obj_id = remote.get_system_handle(obj_name, token)
            remote.modify_system(obj_id, "netboot_enabled", netboot_enabled, token)
            remote.save_system(obj_id, token, "edit")
    elif what == "system" and multi_mode == "profile":
        profile = multi_arg
        if profile is None:
            return error_page(request,"Cannot modify systems without specifying profile")
        for obj_name in names:
            obj_id = remote.get_system_handle(obj_name, token)
            remote.modify_system(obj_id, "profile", profile, token)
            remote.save_system(obj_id, token, "edit")
    elif what == "system" and multi_mode == "power":
        power = multi_arg
        if power is None:
            return error_page(request,"Cannot modify systems without specifying power option")
        for obj_name in names:
            obj_id = remote.get_system_handle(obj_name, token)
            remote.background_power_system(obj_id, power, token)
    else:
        return error_page(request,"Unknown multiple operation on %ss: %s" % (what,str(multi_mode)))

    # FIXME: "operation complete" would make a lot more sense here than a redirect
    return HttpResponseRedirect("/cobbler_web/%s/list"%what)

# ======================================================================

def import_prompt(request):
   t = get_template('import.tmpl')
   html = t.render(Context({
       'username' : username,
   }))
   return HttpResponse(html)

# ======================================================================

def import_run(request):
   name  = request.POST.get("name","")
   path  = request.POST.get("path","") 
   breed = request.POST.get("breed","") 
   arch  = request.POST.get("arch","") 
   remote.background_import(name,path,breed,arch,token)
   return HttpResponseRedirect('/cobbler_web/task_created')

# ======================================================================

def ksfile_list(request, page=None):
   """
   List all kickstart templates and link to their edit pages.
   """
   ksfiles = remote.get_kickstart_templates(token)

   ksfile_list = []
   for ksfile in ksfiles:
      if ksfile.startswith("/var/lib/cobbler/kickstarts") or ksfile.startswith("/etc/cobbler"):
         ksfile_list.append((ksfile,ksfile.replace('/var/lib/cobbler/kickstarts/',''),'editable'))
      elif ksfile["kickstart"].startswith("http://") or ksfile["kickstart"].startswith("ftp://"):
         ksfile_list.append((ksfile,ksfile,'','viewable'))
      else:
         ksfile_list.append((ksfile,ksfile,None))

   t = get_template('ksfile_list.tmpl')
   html = t.render(Context({
       'what':'ksfile', 
       'ksfiles': ksfile_list,
       'username': username
   }))
   return HttpResponse(html)

# ======================================================================


def ksfile_edit(request, ksfile_name=None, editmode='edit'):
   """
   This is the page where a kickstart file is edited.
   """
   if editmode == 'edit':
      editable = False
   else:
      editable = True
   deleteable = False
   ksdata = ""
   if not ksfile_name is None:
      editable = remote.check_access_no_fail(token, "modify_kickstart", ksfile_name)
      deleteable = not remote.is_kickstart_in_use(ksfile_name, token)
      ksdata = remote.read_or_write_kickstart_template(ksfile_name, True, "", token)

   t = get_template('ksfile_edit.tmpl')
   html = t.render(Context({
       'ksfile_name' : ksfile_name, 
       'deleteable'  : deleteable, 
       'ksdata'      : ksdata, 
       'editable'    : editable, 
       'editmode'    : editmode,
       'username'    : username
   }))
   return HttpResponse(html)

# ======================================================================

def ksfile_save(request):
   """
   This page processes and saves edits to a kickstart file.
   """
   # FIXME: error checking

   editmode = request.POST.get('editmode', 'edit')
   ksfile_name = request.POST.get('ksfile_name', None)
   ksdata = request.POST.get('ksdata', "")

   if ksfile_name == None:
      return HttpResponse("NO KSFILE NAME SPECIFIED")
   if editmode != 'edit':
      ksfile_name = "/var/lib/cobbler/kickstarts/" + ksfile_name

   delete1   = request.POST.get('delete1', None)
   delete2   = request.POST.get('delete2', None)

   if delete1 and delete2:
      remote.read_or_write_kickstart_template(ksfile_name, False, -1, token)
      return HttpResponseRedirect('/cobbler_web/ksfile/list')
   else:
      remote.read_or_write_kickstart_template(ksfile_name,False,ksdata,token)
      return HttpResponseRedirect('/cobbler_web/ksfile/edit/%s' % ksfile_name)

# ======================================================================

def snippet_list(request, page=None):
   """
   This page lists all available snippets and has links to edit them.
   """
   snippets = remote.get_snippets(token)

   snippet_list = []
   for snippet in snippets:
      if snippet.startswith("/var/lib/cobbler/snippets"):
         snippet_list.append((snippet,snippet.replace("/var/lib/cobbler/snippets/",""),'editable'))
      else:
         snippet_list.append((snippet,snippet,None))

   t = get_template('snippet_list.tmpl')
   html = t.render(Context({
       'what'     : 'snippet', 
       'snippets' : snippet_list,
       'username' : username
   }))
   return HttpResponse(html)

# ======================================================================

def snippet_edit(request, snippet_name=None, editmode='edit'):
   """
   This page edits a specific snippet.
   """
   if editmode == 'edit':
      editable = False
   else:
      editable = True
   deleteable = False
   snippetdata = ""
   if not snippet_name is None:
      editable = remote.check_access_no_fail(token, "modify_snippet", snippet_name)
      deleteable = True
      snippetdata = remote.read_or_write_snippet(snippet_name, True, "", token)

   t = get_template('snippet_edit.tmpl')
   html = t.render(Context({
       'snippet_name' : snippet_name, 
       'deleteable'   : deleteable, 
       'snippetdata'  : snippetdata, 
       'editable'     : editable, 
       'editmode'     : editmode,
       'username'     : username
   }))
   return HttpResponse(html)

# ======================================================================

def snippet_save(request):
   """
   This snippet saves a snippet once edited.
   """
   # FIXME: error checking

   editmode = request.POST.get('editmode', 'edit')
   snippet_name = request.POST.get('snippet_name', None)
   snippetdata = request.POST.get('snippetdata', "")

   if snippet_name == None:
      return HttpResponse("NO SNIPPET NAME SPECIFIED")
   if editmode != 'edit':
      snippet_name = "/var/lib/cobbler/snippets/" + snippet_name

   delete1   = request.POST.get('delete1', None)
   delete2   = request.POST.get('delete2', None)

   if delete1 and delete2:
      remote.read_or_write_snippet(snippet_name, False, -1, token)
      return HttpResponseRedirect('/cobbler_web/snippet/list')
   else:
      remote.read_or_write_snippet(snippet_name,False,snippetdata,token)
      return HttpResponseRedirect('/cobbler_web/snippet/edit/%s' % snippet_name)

# ======================================================================

def settings(request):
   """
   This page presents a list of all the settings to the user.  They are not editable.
   """
   settings = remote.get_settings()
   t = get_template('settings.tmpl')
   html = t.render(Context({
        'settings' : settings,
        'username' : username,
   }))
   return HttpResponse(html)

# ======================================================================

def events(request):
   """
   This page presents a list of all the tasks and links to the task log viewer.
   """
   tasks = remote.get_events()
 
   tasks2 = []
   for id in tasks.keys():
      (ttime, name, state, read_by) = tasks[id]
      tasks2.append([id,time.asctime(time.gmtime(ttime)),name,state])

   def sorter(a,b):
      return cmp(a[2],b[2])
   tasks2.sort(sorter)

   t = get_template('tasks.tmpl')
   html = t.render(Context({
       'results'  : tasks2,
       'username' : username
   }))
   return HttpResponse(html)

# ======================================================================

def tasklog(request, task=0):
   """
   Shows the log for a given task.
   """
   task_info = remote.get_events()
   if not task_info.has_key(task):
      return HttpResponse("task not found")

   data      = task_info[task]
   taskname  = data[0]
   tasktime  = data[1]
   taskstate = data[2]
   tasklog   = remote.get_task_log(task)

   t = get_template('tasklog.tmpl')
   vars = {
      'tasklog'   : tasklog,
      'taskname'  : taskname,
      'taskstate' : taskstate,
      'taskid'    : task,
      'tasktime'  : tasktime,
      'username'  : username
   }
   html = t.render(Context(vars))
   return HttpResponse(html)

# ======================================================================

def random_mac(request, virttype="xenpv"):
   """
   Used in an ajax call to fill in a field with a mac address.
   """
   # FIXME: not exposed in UI currently
   random_mac = remote.get_random_mac(virttype, token)
   return HttpResponse(random_mac)

# ======================================================================

def sync(request):
   """
   Runs 'cobbler sync' from the API when the user presses the sync button.
   """
   remote.background_sync(token)
   return HttpResponseRedirect("/cobbler_web/task_created")

# ======================================================================

def reposync(request):
   """
   Syncs all repos that are configured to be synced.
   """
   remote.background_reposync("",3,token)
   return HttpResponseRedirect("/cobbler_web/task_created")

# ======================================================================

def hardlink(request):
   """
   Hardlinks files between repos and install trees to save space.
   """
   remote.background_hardlink(token)
   return HttpResponseRedirect("/cobbler_web/task_created")

# ======================================================================

def replicate(request):
   """
   Replicate configuration from the central cobbler server, configured
   in /etc/cobbler/settings (note: this is uni-directional!)
   """
   remote.background_replicate(token)
   return HttpResponseRedirect("/cobbler_web/task_created")

# ======================================================================

def __names_from_dicts(loh,optional=True):
   """
   Tiny helper function.
   Get the names out of an array of hashes that the remote interface returns.
   """
   results = []
   if optional:
      results.append("<<None>>")
   for x in loh:
      results.append(x["name"])
   return results

# ======================================================================

def generic_edit(request, what=None, obj_name=None, editmode="new"):

   """
   Presents an editor page for any type of object.
   While this is generally standardized, systems are a little bit special.
   """

   obj = None

   settings = remote.get_settings()

   child = False
   if what == "subprofile":
      what = "profile"
      child = True
   

   if not obj_name is None:
      editable = remote.check_access_no_fail(token, "modify_%s" % what, obj_name)
      obj = remote.get_item(what, obj_name, True)
   #
   #   if obj.has_key('ctime'):
   #      obj['ctime'] = time.ctime(obj['ctime'])
   #   if obj.has_key('mtime'):
   #      obj['mtime'] = time.ctime(obj['mtime'])

   else:
       editable = remote.check_access_no_fail(token, "new_%s" % what, None)
       obj = None


   interfaces = {}
   if what == "system":
       if obj:
           interfaces = obj.get("interfaces",{})
       else:
           interfaces = {}

   fields = get_fields(what, child, obj)

   # populate some select boxes
   # FIXME: we really want to just populate with the names, right?
   if what == "profile":
      if (obj and obj["parent"] not in (None,"")) or child:
         __tweak_field(fields, "parent", "choices", __names_from_dicts(remote.get_profiles()))
      else:
         __tweak_field(fields, "distro", "choices", __names_from_dicts(remote.get_distros()))
      __tweak_field(fields, "repos", "choices",     __names_from_dicts(remote.get_repos()))
   elif what == "system":
      __tweak_field(fields, "profile", "choices",   __names_from_dicts(remote.get_profiles()))
      __tweak_field(fields, "image", "choices",     __names_from_dicts(remote.get_images(),optional=True))
      __tweak_field(fields, "network", "choices",   __names_from_dicts(remote.get_networks(),optional=True))


   t = get_template('generic_edit.tmpl')
   inames = interfaces.keys()
   inames.sort()
   html = t.render(Context({
       'what'            : what, 
       'fields'          : fields, 
       'subobject'       : child,
       'editmode'        : editmode, 
       'editable'        : editable,
       'interfaces'      : interfaces,
       'interface_names' : inames,
       'interface_length': len(inames),
       'username'        : username
   }))

   return HttpResponse(html)

# ======================================================================

def generic_save(request,what):

    """
    Saves an object back using the cobbler API after clearing any 'generic_edit' page.
    """

    # load request fields and see if they are valid
    editmode  = request.POST.get('editmode', 'edit')
    obj_name  = request.POST.get('name', "")    
    subobject = request.POST.get('subobject', True)    
    if obj_name == "":
        return error_page(request,"Required field name is missing")
              
    # grab the remote object handle
    # for edits, fail in the object cannot be found to be edited
    # for new objects, fail if the object already exists
    if editmode == "edit":
        if not remote.has_item(what, obj_name):
            return error_page(request,"Failure trying to access item %s, it may have been deleted." % (obj_name))
        obj_id = remote.get_item_handle( what, obj_name, token )
    else:
        if remote.has_item(what, obj_name):
            return error_page(request,"Could not create a new item %s, it already exists." % (obj_name))
        obj_id = remote.new_item( what, token )

    # walk through our fields list saving things we know how to save
    fields = get_fields(what, subobject)

    for field in fields:
        if field['name'] == 'name' and editmode == 'edit':
            # do not attempt renames here
            continue
        elif field['name'].startswith("*"):
            # interface fields will be handled below
            continue
        else:
            value = request.POST.get(field['name'],None)
            # Checkboxes return the value of the field if checked, otherwise None
            # convert to True/False
            if field["html_element"] == "checkbox":
                if value==field['name']:
                    value=True
                else:
                    value=False
            if value != None:
                if value == "<<None>>":
                    value = ""
                if value is not None and (not subobject or field['name'] != 'distro'):
                    try:
                        remote.modify_item(what,obj_id,field['name'],value,token)
                    except Exception, e:
                        return error_page(request, str(e))                

    # special handling for system interface fields
    # which are the only objects in cobbler that will ever work this way
    if what == "system":
        interface_field_list = []
        for field in fields:
            if field['name'].startswith("*"):
                field = field['name'].replace("*","")
                interface_field_list.append(field)
        interfaces = request.POST.get('interface_list', "").split(",")
        for interface in interfaces:
            if interface == "":
                continue
            ifdata = {}
            for item in interface_field_list:
                ifdata["%s-%s" % (item,interface)] = request.POST.get("%s-%s" % (item,interface), "")
            # FIXME: I think this button is missing.
            present  = request.POST.get("present-%s" % interface, "") 
            original = request.POST.get("original-%s" % interface, "") 
            try:
                if present == "0" and original == "1":
                    remote.modify_system(obj_id, 'delete_interface', interface, token)
                elif present == "1":
                    remote.modify_system(obj_id, 'modify_interface', ifdata, token)
            except Exception, e:
                return error_page(request, str(e))

    try:
        remote.save_item(what, obj_id, token, editmode)
    except Exception, e:
        return error_page(request, str(e))

    return HttpResponseRedirect('/cobbler_web/%s/list' % what)


