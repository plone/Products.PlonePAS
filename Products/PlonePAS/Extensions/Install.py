"""
$Id: Install.py,v 1.25 2005/05/06 19:03:58 jccooper Exp $
"""

from StringIO import StringIO

from Products.Archetypes.Extensions.utils import install_subskin
from Products.CMFCore.utils import getToolByName
from Products.PluginRegistry.PluginRegistry import PluginRegistry

from Products.PlonePAS import config
from Products.PlonePAS.interfaces.plugins import IUserManagement, ILocalRolesPlugin
from Products.PlonePAS.interfaces import group as igroup

from Products.PlonePAS.tools.groups import GroupsTool
from Products.PlonePAS.tools.groupdata import GroupDataTool
from Products.PlonePAS.tools.membership import MembershipTool
from Products.PlonePAS.tools.memberdata import MemberDataTool
from Products.PlonePAS.tools.plonetool import PloneTool

from Acquisition import aq_base

def activatePluginInterfaces(portal, plugin, out):
    pas = portal.acl_users
    plugin_obj = pas[plugin]

    interfaces = plugin_obj.listInterfaces()

    activatable = []

    try:
        for info in plugin_obj.plugins.listPluginTypeInfo():
            interface = info['interface']
            interface_name = info['id']
            if plugin_obj.testImplements(interface):
                activatable.append(interface_name)
                print >> out, " - Activating: " + info['title']
    except AttributeError:
        print >> out, "It looks like you have a non-PAS acl_users folder. "
        print >> out, "Please remove it before installing PlonePAS."
    plugin_obj.manage_activateInterfaces(activatable)
    print >> out, plugin + " activated."

def setupRoles( portal ):
    rmanager = portal.acl_users.role_manager
    rmanager.addRole('Member', title="portal member")
    rmanager.addRole('Reviewer', title="content reviewer")

def registerPluginType( pas, plugin_type, plugin_info ):
    pas.plugins._plugin_type_info[plugin_type] =  plugin_info 
    pas.plugins._plugin_types.append(plugin_type)

    
def registerPluginTypes( pas ):

    PluginInfo = { 'id' : 'IUserManagement',
                   'title': 'user_management',
                   'description': "The User Management plugins allow the Pluggable Auth " +\
                   "Service to add/delete/modify users"
                   }

    registerPluginType( pas, IUserManagement, PluginInfo )

    PluginInfo = { 'id' : 'IGroupManagement',
                   'title': 'group_management',
                   'description': "Group Management provides add/write/deletion of groups and member management"
                   }

    registerPluginType( pas, igroup.IGroupManagement, PluginInfo )

    PluginInfo = { 'id' : 'IGroupIntrospection',
                   'title': 'group_introspection',
                   'description': "Group Introspection provides listings of groups and membership"
                   }

    registerPluginType( pas, igroup.IGroupIntrospection, PluginInfo )

    PluginInfo = { 'id' : 'ILocalRolesPlugin',
                   'title':'local_roles',
                   'description':"Defines Policy for getting Local Roles" }

    registerPluginType( pas, ILocalRolesPlugin, PluginInfo )    

def setupPlugins( portal, out ):
    pas = portal.acl_users
    print >> out, "\nPlugin setup"

    pas.manage_addProduct['PluggableAuthService'].addCookieAuthHelper('credentials_cookie', cookie_name='__ac')
    print >> out, "Added Cookie Auth Helper."
    activatePluginInterfaces(portal, 'credentials_cookie', out)

    
    pas.manage_addProduct['PluggableAuthService'].addHTTPBasicAuthHelper('credentials_basic_auth',
            title="HTTP Basic Auth")
    print >> out, "Added Basic Auth Helper."
    activatePluginInterfaces(portal, 'credentials_basic_auth', out)


    pas.manage_addProduct['PlonePAS'].manage_addUserManager('source_users')
    print >> out, "Added User Manager."
    activatePluginInterfaces(portal, 'source_users', out)


    pas.manage_addProduct['PlonePAS'].manage_addGroupAwareRoleManager('portal_role_manager')
    print >> out, "Added Group Aware Role Manager."
    activatePluginInterfaces(portal, 'portal_role_manager', out)

    pas.manage_addProduct['PlonePAS'].manage_addLocalRolesManager('local_roles')
    print >> out, "Added Group Aware Role Manager."
    activatePluginInterfaces(portal, 'local_roles', out)


    pas.manage_addProduct['PlonePAS'].manage_addGroupManager('source_groups')
    print >> out, "Added ZODB Group Manager."
    activatePluginInterfaces(portal, 'source_groups', out)

    pas.manage_addProduct['PlonePAS'].manage_addPloneUserFactory('user_factory')
    print >> out, "Added Plone User Factory."
    activatePluginInterfaces(portal, "user_factory", out)

    pas.manage_addProduct['PlonePAS'].manage_addZODBMutablePropertyProvider('mutable_properties')
    print >> out, "Added Mutable Property Manager."
    activatePluginInterfaces(portal, "mutable_properties", out)


def configurePlonePAS(portal, out):
    """Add the necessary objects to make a usable PAS instance"""
    registerPluginTypes( portal.acl_users )
    setupPlugins( portal, out )
#    setupRoles( portal )

def setupTools(portal, out):
    print >> out, "\nTools:"

    print >> out, "Groups Tool (portal_groups)"
    print >> out, " - Removing Default"
    portal.manage_delObjects(['portal_groups'])
    print >> out, " - Installing PAS Aware"
    portal._setObject( GroupsTool.id, GroupsTool() )
    print >> out, " ...done"

    print >> out, "GroupData Tool (portal_groupdata)"
    print >> out, " - Removing Default"
    portal.manage_delObjects(['portal_groupdata'])
    # XXX TODO: data migration
    print >> out, " - Installing PAS Aware"
    portal._setObject( GroupDataTool.id, GroupDataTool() )
    print >> out, " ...done"

    print >> out, "Plone Tool (plone_utils)"
    print >> out, " - Removing Default"
    portal.manage_delObjects(['plone_utils'])
    print >> out, " - Installing PAS Aware"
    portal._setObject( PloneTool.id, PloneTool() )
    print >> out, " ...done"

    print >> out, "Membership Tool (portal_membership)"
    print >> out, " - Removing Default"
    portal.manage_delObjects(['portal_membership'])
    print >> out, " - Installing PAS Aware"
    portal._setObject( MembershipTool.id, MembershipTool() )
    print >> out, " ...done"

    migrateMemberdata(portal, out)

def updateProp(prop_manager, prop_dict):
    """Provided a PropertyManager and a property dict of {id, value, type}, set or update that property as applicable."""
    id = prop_dict['id']
    value = prop_dict['value']
    type = prop_dict['type']
    if prop_manager.hasProperty(id):
        prop_manager._updateProperty(id, value)
    else:
        prop_manager._setProperty(id, value, type)

def migrateMemberdata(portal, out):
    print >> out, "MemberData Tool (portal_memberdata)"
    
    print >> out, "  ...extracting data"
    md_tool = portal.portal_memberdata
    properties = md_tool._properties
    for elt in properties:
        elt['value'] = md_tool.getProperty(elt['id'])

    md_tool = None
    print >> out, " - Removing Default"
    portal.manage_delObjects(['portal_memberdata'])

    print >> out, " - Installing PAS Aware"
    portal._setObject(MemberDataTool.id, MemberDataTool())

    print >> out, " ...restoring data"
    md_tool = portal.portal_memberdata
    for prop in properties:
        updateProp(md_tool, prop)
    print >> out, " ...done"


def installUserFolder(portal, out):
    if not hasattr(aq_base(portal), 'acl_users'):
        portal.manage_addProduct['PluggableAuthService'].addPluggableAuthService()
    else:
        raise AttributeError, "acl_users already exists. As there is no upgrade at this time, " + \
                              "you must delete it before installing PlonePAS."

def install(self):
    out = StringIO()
    portal = getToolByName(self, 'portal_url').getPortalObject()

    installUserFolder(portal, out)

    install_subskin(self, out, config.GLOBALS)
    print >> out, "Installed skins."

    configurePlonePAS(portal, out)

    setupTools(portal, out)

    print >> out, "Successfully installed %s." % config.PROJECTNAME
    return out.getvalue()
