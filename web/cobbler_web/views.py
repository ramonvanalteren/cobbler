from django.template.loader import get_template
from django.template import Context
from django.template import RequestContext
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from mod_python import apache

import xmlrpclib, time, simplejson, string, distutils

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

def authenhandler(req):
    global remote
    global token
    global username

    password = req.get_basic_auth_pw()
    username = req.user     
    #try:
    remote = xmlrpclib.Server(my_uri, allow_none=True)
    token = remote.login(username, password)
    remote.update(token)
    return apache.OK
    #except:
    #    return apache.HTTP_UNAUTHORIZED

def index(request):
   t = get_template('index.tmpl')
   html = t.render(Context({'version': remote.version(token), 'username':username}))
   return HttpResponse(html)

def error_page(request,message):
   t = get_template('error_page.tmpl')
   html = t.render(Context({'message': message}))
   return HttpResponse(html)

def list(request, what, page=None):
    if page == None:
        page = int(request.session.get("%s_page" % what, 1))
    limit = int(request.session.get("%s_limit" % what, 50))
    sort_field = request.session.get("%s_sort_field" % what, None)
    filters = simplejson.loads(request.session.get("%s_filters" % what, "{}"))

    pageditems = remote.find_items_paged(what,filters,sort_field,page,limit)

    t = get_template('%s_list.tmpl'%what)
    html = t.render(RequestContext(request,{
        'what'      : what,
        '%ss'%what  : pageditems["items"],
        'pageinfo'  : pageditems["pageinfo"],
        'filters'   : filters,
    }))
    return HttpResponse(html)

def get_fields(what, is_subobject, seed_item=None):

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


        elem = {
            "name"                    : row[0],
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
            else:
                elem["value"]             = seed_item[row[0]]
        elif is_subobject:
            elem["value"]             = row[2]
        else:
            elem["value"]             = row[1]
                

        # we'll process this for display but still need to present the original to some
        # template logic
        elem["value_raw"]             = elem["value"]

        if isinstance(elem["value"],basestring) and elem["value"].startswith("SETTINGS:"):
            key = value.replace("SETTINGS:","",1)
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
            elem["value"] = tokens.join(" ")
 
        name = row[0]
        if name in field_info.USES_SELECT:
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
           elem["html_element"]  = "text"

        elem["css_class"] = field_info.CSS_MAPPINGS.get(name, "genericedit")
        
        # flatten lists for those that aren't using select boxes
        if type(elem["value"]) == type([]):
            if elem["html_element"] != "select":
                elem["value"] = string.join(elem["value"], sep=" ")

        # FIXME: need to handle interfaces special, they are prefixed with "*"

        fields.append(elem)

    return fields

def __tweak_field(fields,field_name,attribute,value):
    for x in fields:
       if x["name"] == field_name:
           x[attribute] = value

def __format_items(items, column_names):
    """
    Format items retrieved from XMLRPC for rendering by the generic_edit template
    """
    dataset = []
    for itemhash in items:
        row = []
        for fieldname in column_names:
            row.append(itemhash[fieldname])
        dataset.append(row)
    return dataset



def genlist(request, what, page=None):

    # FIXME: cleanup
    if page == None:
        page = int(request.session.get("%s_page" % what, 1))
    limit = int(request.session.get("%s_limit" % what, 50))                      # FIXME: does this work?
    sort_field = request.session.get("%s_sort_field" % what, None)               # FIXME: is this used?
    filters = simplejson.loads(request.session.get("%s_filters" % what, "{}"))
    pageditems = remote.find_items_paged(what,filters,sort_field,page,limit)

    # what columns to show for each page?
    if what == "distro":
       columns = [ "name" ]
    if what == "profile":
       columns = [ "name", "distro" ]
    if what == "system":
       columns = [ "name", "profile" ] 
    if what == "repo":
       columns = [ "name", "mirror" ]
    if what == "image":
       columns = [ "name", "file" ]
    if what == "network":
       columns = [ "name" ] 

    t = get_template('generic_list.tmpl')
    html = t.render(RequestContext(request,{
        'what'           : what,
        'columns'        : columns,
        'items'          : __format_items(pageditems["items"],columns),
        'pageinfo'       : pageditems["pageinfo"],
        'filters'        : filters,
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

    # FIXME: cleanup

    try:
        if pref == "sort":
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
            request.session["%s_limit" % what] = int(value)
            request.session["%s_page" % what] = 1
        elif pref == "page":
            request.session["%s_page" % what] = int(value)
        elif pref in ("addfilter","removefilter"):
            # filter are stored in json format for marshalling
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
            raise ""
        # redirect to the list
        return HttpResponseRedirect("/cobbler_web/%s/list" % what)
    except:
        return error_page(request,"Invalid preference: %s" % pref)

def generic_rename(request, what, obj_name=None, obj_newname=None):
   # FIXME: cleanup
   if obj_name == None:
      return error_page(request,"You must specify a %s to rename" % what)
   if not remote.has_item(what,obj_name):
      return error_page(request,"Unknown %s specified" % what)
   elif not remote.check_access_no_fail(token, "modify_%s" % what, obj_name):
      return error_page(request,"You do not have permission to rename this %s" % what)
   elif obj_newname == None:
      t = get_template('generic_rename.tmpl')
      html = t.render(Context({
            'what' : what,
            'name' : obj_name
      }))
      return HttpResponse(html)
   else:
      obj_id = remote.get_item_handle(what, obj_name, token)
      remote.rename_item(what, obj_id, obj_newname, token)
      return HttpResponseRedirect("/cobbler_web/%s/list" % what)

def generic_multi(request, what, multi_mode=None):
    # FIXME: cleanup
    # FIXME: how does this work, COMMENTS!

    names = request.POST.getlist('items')

    all_items = remote.get_items(what)
    sel_items = []
    sel_names = []
    for item in all_items:
        if item['name'] in names:
            if not remote.check_access_no_fail(token, "modify_%s" % what, item["name"]):
                return error_page(request,"You do not have permission to modify one or more of the %ss you selected" % what)
            sel_items.append(item)
            sel_names.append(item['name'])

    htmlvars={
        'what'  : what,
        'names' : sel_names,
    }
    if multi_mode in ("profile","power","netboot"):
        htmlname='system_%s.tmpl' % multi_mode
        htmlvars['systems']=sel_items
        if multi_mode=="profile":
            htmlvars['profiles'] = remote.get_profiles(token)
    else:
        htmlname='generic_%s.tmpl' % multi_mode
        htmlvars['items']=sel_items

    t = get_template(htmlname)
    html=t.render(Context(htmlvars))
    return HttpResponse(html)

def generic_domulti(request, what, multi_mode=None):

    # FIXME: cleanup
    # FIXME: COMMENTS!!!11111???

    names = request.POST.get('names', '').split(" ")

    if multi_mode == "delete":
        for obj_name in names:
            remote.remove_item(what,obj_name, token)
    elif what == "system" and multi_mode == "netboot":
        netboot_enabled = request.POST.get('netboot_enabled', None)
        if netboot_enabled is None:
            raise "Cannot modify systems without specifying netboot_enabled"
        for obj_name in names:
            obj_id = remote.get_system_handle(obj_name, token)
            remote.modify_system(obj_id, "netboot_enabled", netboot_enabled, token)
            remote.save_system(obj_id, token, "edit")
    elif what == "system" and multi_mode == "profile":
        profile = request.POST.get('profile', None)
        if profile is None:
            raise "Cannot modify systems without specifying profile"
        for obj_name in names:
            obj_id = remote.get_system_handle(obj_name, token)
            remote.modify_system(obj_id, "profile", profile, token)
            remote.save_system(obj_id, token, "edit")
    elif what == "system" and multi_mode == "power":
        power = request.POST.get('power', None)
        if power is None:
            raise "Cannot modify systems without specifying power option"
        try:
            for obj_name in names:
                obj_id = remote.get_system_handle(obj_name, token)
                remote.power_system(obj_id, power, token)
        except:
            # TODO: something besides ignore.  We should probably
            #       print out an error message at the top of whatever
            #       page we go to next, whether it's the system list 
            #       or a results page
            pass
    else:
        raise "Unknown multiple operation on %ss: %s" % (what,str(multi_mode))
    return HttpResponseRedirect("/cobbler_web/%s/list"%what)

def ksfile_list(request, page=None):
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
   html = t.render(Context({'what':'ksfile', 'ksfiles': ksfile_list}))
   return HttpResponse(html)

def ksfile_edit(request, ksfile_name=None, editmode='edit'):
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
   html = t.render(Context({'ksfile_name':ksfile_name, 'deleteable':deleteable, 'ksdata':ksdata, 'editable':editable, 'editmode':editmode}))
   return HttpResponse(html)

def ksfile_save(request):
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

###


def snippet_list(request, page=None):
   snippets = remote.get_snippets(token)

   snippet_list = []
   for snippet in snippets:
      if snippet.startswith("/var/lib/cobbler/snippets"):
         snippet_list.append((snippet,snippet.replace("/var/lib/cobbler/snippets/",""),'editable'))
      else:
         snippet_list.append((snippet,snippet,None))

   t = get_template('snippet_list.tmpl')
   html = t.render(Context({'what':'snippet', 'snippets': snippet_list}))
   return HttpResponse(html)

def snippet_edit(request, snippet_name=None, editmode='edit'):
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
   html = t.render(Context({'snippet_name':snippet_name, 'deleteable':deleteable, 'snippetdata':snippetdata, 'editable':editable, 'editmode':editmode}))
   return HttpResponse(html)

def snippet_save(request):
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

def settings(request):
   settings = remote.get_settings()
   t = get_template('settings.tmpl')
   html = t.render(Context({'settings': remote.get_settings()}))
   return HttpResponse(html)

def random_mac(request, virttype="xenpv"):
   random_mac = remote.get_random_mac(virttype, token)
   return HttpResponse(random_mac)

def dosync(request):
   remote.sync(token)
   return HttpResponseRedirect("/cobbler_web/")

def __names_from_dicts(loh):
   """
   Tiny helper function.
   Get the names out of an array of hashes that the remote interface returns.
   """
   results = []
   for x in loh:
      results.append(x["name"])
   return results

def generic_edit(request, what=None, obj_name=None, editmode="new"):

   # FIXME: cleanup
   # FIXME: comments

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
       interfaces = obj.get("interfaces",{})

   fields = get_fields(what, child, obj)

   # populate some select boxes
   # FIXME: we really want to just populate with the names, right?
   if what == "profile":
      if (obj and obj["parent"] not in (None,"")) or child:
         __tweak_field(fields, "parent", "choices", __names_from_dicts(remote.get_profiles()))
      else:
         __tweak_field(fields, "distro", "choices", __names_from_dicts(remote.get_distros()))
   __tweak_field(fields, "repos", "choices", __names_from_dicts(remote.get_repos()))

   t = get_template('generic_edit.tmpl')
   html = t.render(Context({
       'what'            : what, 
       'fields'          : fields, 
       'editmode'        : editmode, 
       'editable'        : editable,
       'interfaces'      : interfaces,
       'interface_names' : interfaces.keys()
   }))

   return HttpResponse(html)

def generic_save(request,what):

    # FIXME: cleanup
    # FIXME: comments

    editmode = request.POST.get('editmode', 'edit')
    obj_name = request.POST.get('name', "")
    
    if obj_name == "":
        return error_page(request,"%s name field is missing" % what)
              
    if editmode == "edit":
        if not remote.has_item( what, obj_name ):
            return error_page(request,"Failed to lookup %s: %s" % (what,obj_name))
        obj_id = remote.get_item_handle( what, obj_name, token )
    else:
        if remote.has_item( what, obj_name ):
            return error_page(request,"Failed to create new %s: %s already exists." % (what,obj_name))
        obj_id = remote.new_item( what, token )

    # FIXME: signature has changed 
    fields = remote.get_fields(what, token)

    for field in fields.keys():
        if field == 'name' and editmode == 'edit':
            continue
        elif what == 'system' and field == "interfaces":
            # FIXME: we should pull this from the fields table so it's not hard coded
            interface_field_list = ('mac_address','ip_address','dns_name','static_routes','static','virt_bridge','dhcptag','subnet','bonding','bonding_opts','bonding_master','present','original')
            interfaces = request.POST.get('interface_list', "").split(",")
            for interface in interfaces:
                ifdata = {}
                for item in interface_field_list:
                    ifdata["%s-%s" % (item,interface)] = request.POST.get("%s-%s" % (item,interface), "")
                if ifdata['present-%s' % interface] == "0" and ifdata['original-%s' % interface] == "1":
                    remote.modify_system(obj_id, 'delete_interface', interface, token)
                elif ifdata['present-%s' % interface] == "1":
                    remote.modify_system(obj_id, 'modify_interface', ifdata, token)
        else:
            value = request.POST.get(field, None)
            if value != None:
                remote.modify_item(what,obj_id, field, value, token)
                
    remote.save_item(what, obj_id, token, editmode)
    return HttpResponseRedirect('/cobbler_web/%s/list' % what)


