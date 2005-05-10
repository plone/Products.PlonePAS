"""
$Id: Install.py,v 1.28 2005/05/10 21:20:48 jccooper Exp $
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

def grabUserData(portal, out):
    """Return a list of (id, password, roles, domains, properties) tuples for the users of the system.
    Password may be encypted or not: addUser will figure it out.
    """
    print >> out, "\nExtract Member information..."

    userdata = ()
    mdtool = portal.portal_memberdata
    mtool = portal.portal_membership

    props = mdtool.propertyIds()
    members = mtool.listMembers()
    for member in members:
        id = member.getId()
        password = member.getPassword()
        roles = [role for role in member.getRoles() if role != 'Authenticated']
        domains = member.getDomains()
        properties = {}
        for propid in props:
            properties[propid] = member.getProperty(propid, None)
        userdata += ((id, password, roles, domains, properties),)

    print >> out, "...extract done"
    return userdata

def restoreUserData(portal, out, userdata):
    print >> out, "\nRestoring Member information..."

    # re-add users
    # Password may be encypted or not: addUser will figure it out.
    mtool = portal.portal_membership
    for u in userdata:
        mtool.addMember(*u)

    print >> out, "...restore done"

def grabGroupData(portal, out):
    """Return a list of (id, roles, groups, properties) tuples for the users of the system and
    a mapping of group ids to a list of group members.
    Password may be encypted or not: addUser will figure it out.
    """
    print >> out, "\nExtract Group information..."

    groupdata = ()
    groupmemberships = {}
    gdtool = portal.portal_groupdata
    gtool = portal.portal_groups

    props = gdtool.propertyIds()
    groups = gtool.listGroups()
    for group in groups:
        id = group.getGroupId()
        roles = [role for role in group.getRoles() if role != 'Authenticated']
        properties = {}
        has_groups = []    # we take care of this with the groupmemberships stuff
        for propid in props:
            properties[propid] = group.getProperty(propid, None)
        groupdata += ((id, roles, has_groups, properties),)
        groupmemberships[id] = group.getGroupMemberIds()

    print >> out, "...extract done"
    return groupdata, groupmemberships

def restoreGroupData(portal, out, groupdata, groupmemberships):
    print >> out, "\nRestoring Group information..."

    # re-add groups
    gtool = portal.portal_groups
    for g in groupdata:
        gtool.addGroup(*g)

        # restore group memberships
        gid = g[0]
        group = gtool.getGroupById(gid)
        for mid in groupmemberships[gid]:
            group.addMember(mid)

    print >> out, "...restore done"


def setupTools(portal, out):
    print >> out, "\nTools:"

    print >> out, "Plone Tool (plone_utils)"
    print >> out, " ...nothing to migrate"
    print >> out, " - Removing Default"
    portal.manage_delObjects(['plone_utils'])
    print >> out, " - Installing PAS Aware"
    portal._setObject( PloneTool.id, PloneTool() )
    print >> out, " ...done"



    print >> out, "Membership Tool (portal_membership)"

    print >> out, " ...copying settings"
    memberareaCreationFlag = portal.portal_membership.getMemberareaCreationFlag()
    role_map = getattr(portal.portal_membership, 'role_map', None)
    membersfolder_id = portal.portal_membership.membersfolder_id

    print >> out, " ...copying actions"
    actions = portal.portal_membership._actions

    print >> out, " - Removing Default"
    portal.manage_delObjects(['portal_membership'])

    print >> out, " - Installing PAS Aware"
    portal._setObject( MembershipTool.id, MembershipTool() )

    print >> out, " ...restoring settings"
    portal.portal_membership.memberareaCreationFlag = memberareaCreationFlag
    if role_map: portal.portal_membership.role_map = role_map
    if membersfolder_id: portal.portal_membership.membersfolder_id = membersfolder_id

    print >> out, " ...restoring actions"
    portal.portal_membership._actions = actions

    print >> out, " ...done"



    print >> out, "Groups Tool (portal_groups)"

    print >> out, " ...copying settings"
    groupworkspaces_id = portal.portal_groups.getGroupWorkspacesFolderId()
    groupworkspaces_title =  portal.portal_groups.getGroupWorkspacesFolderTitle()
    groupWorkspacesCreationFlag =  portal.portal_groups.getGroupWorkspacesCreationFlag()
    groupWorkspaceType =  portal.portal_groups.getGroupWorkspaceType()
    groupWorkspaceContainerType =  portal.portal_groups.getGroupWorkspaceContainerType()

    print >> out, " ...copying actions"
    actions = portal.portal_groups._actions

    print >> out, " - Removing Default"
    portal.manage_delObjects(['portal_groups'])

    print >> out, " - Installing PAS Aware"
    portal._setObject( GroupsTool.id, GroupsTool() )

    print >> out, " ...restoring settings"
    portal.portal_groups.setGroupWorkspacesFolder(groupworkspaces_id, groupworkspaces_title)
    portal.portal_groups.groupWorkspacesCreationFlag = groupWorkspacesCreationFlag
    portal.portal_groups.setGroupWorkspaceType(groupWorkspaceType)
    portal.portal_groups.setGroupWorkspaceContainerType(groupWorkspaceContainerType)

    print >> out, " ...restoring actions"
    portal.portal_groups._actions = actions

    print >> out, " ...done"



    migrateMemberDataTool(portal, out)
    migrateGroupDataTool(portal, out)


def migrateGroupDataTool(portal, out):
    # this could be somewhat combined with migrateMemberDataTool, but I don't think it's worth it

    print >> out, "GroupData Tool (portal_groupdata)"    

    print >> out, " ...copying actions"
    actions = portal.portal_groupdata._actions

    print >> out, " ...extracting data"
    gdtool = portal.portal_groupdata
    properties = gdtool._properties
    for elt in properties:
        elt['value'] = gdtool.getProperty(elt['id'])

    gdtool = None
    print >> out, " - Removing Default"
    portal.manage_delObjects(['portal_groupdata'])

    print >> out, " - Installing PAS Aware"
    portal._setObject(GroupDataTool.id, GroupDataTool())

    print >> out, " ...restoring actions"
    portal.portal_groupdata._actions = actions

    print >> out, " ...restoring data"
    gdtool = portal.portal_groupdata
    for prop in properties:
        updateProp(gdtool, prop)

    print >> out, " ...done"

def migrateMemberDataTool(portal, out):
    print >> out, "MemberData Tool (portal_memberdata)"    

    print >> out, " ...copying actions"
    actions = portal.portal_memberdata._actions

    print >> out, "  ...extracting data"
    mdtool = portal.portal_memberdata
    properties = mdtool._properties
    for elt in properties:
        elt['value'] = mdtool.getProperty(elt['id'])

    mdtool = None
    print >> out, " - Removing Default"
    portal.manage_delObjects(['portal_memberdata'])

    print >> out, " - Installing PAS Aware"
    portal._setObject(MemberDataTool.id, MemberDataTool())

    print >> out, " ...restoring actions"
    portal.portal_memberdata._actions = actions

    print >> out, " ...restoring data"
    mdtool = portal.portal_memberdata
    for prop in properties:
        updateProp(mdtool, prop)

    print >> out, " ...done"


def updateProp(prop_manager, prop_dict):
    """Provided a PropertyManager and a property dict of {id, value, type}, set or update that property as applicable.
    Doesn't deal with existing properties changing type.
    """
    id = prop_dict['id']
    value = prop_dict['value']
    type = prop_dict['type']
    if prop_manager.hasProperty(id):
        prop_manager._updateProperty(id, value)
    else:
        prop_manager._setProperty(id, value, type)


def installUserFolder(portal, out):
    # XXX: this should probably check if it's GRUF + basic UserFolder, although...
    # other configurations might work. The migration code it pretty generic.

    print >> out, "\nUser folder replacement:"

    print >> out, " - Removing existing user folder"
    portal.manage_delObjects(['acl_users'])

    print >> out, " - Adding PAS user folder"
    portal.manage_addProduct['PluggableAuthService'].addPluggableAuthService()

    print >> out, "...replace done"


def install(self):
    out = StringIO()
    portal = getToolByName(self, 'portal_url').getPortalObject()

    userdata = grabUserData(portal, out)
    groupdata, memberships = grabGroupData(portal, out)

    installUserFolder(portal, out)

    install_subskin(self, out, config.GLOBALS)
    print >> out, "\nInstalled skins."

    configurePlonePAS(portal, out)

    setupTools(portal, out)

    restoreUserData(portal, out, userdata)
    restoreGroupData(portal, out, groupdata, memberships)

    print >> out, "\nSuccessfully installed %s." % config.PROJECTNAME
    return out.getvalue()
