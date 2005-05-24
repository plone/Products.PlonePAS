"""
$Id: Install.py,v 1.36 2005/05/24 22:16:52 jccooper Exp $
"""

from StringIO import StringIO

from Products.Archetypes.Extensions.utils import install_subskin
from Products.CMFCore.utils import getToolByName
from Products.PluginRegistry.PluginRegistry import PluginRegistry

from Products.PluggableAuthService.interfaces.plugins import IPropertiesPlugin
from Products.PluggableAuthService.interfaces.plugins import IGroupsPlugin
from Products.PluggableAuthService.interfaces.plugins \
     import IGroupEnumerationPlugin

from Products.PlonePAS import config
from Products.PlonePAS.interfaces.plugins import IUserManagement
from Products.PlonePAS.interfaces.plugins import ILocalRolesPlugin
from Products.PlonePAS.interfaces import group as igroup

from Products.PlonePAS.tools.groups import GroupsTool
from Products.PlonePAS.tools.groupdata import GroupDataTool
from Products.PlonePAS.tools.membership import MembershipTool
from Products.PlonePAS.tools.memberdata import MemberDataTool
from Products.PlonePAS.tools.plonetool import PloneTool

from Products.PlonePAS.MigrationCheck import canAutoMigrate

CAN_LDAP = 0
try:
    import Products.LDAPMultiPlugins
    CAN_LDAP = 1
except ImportError:
    pass

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

def setupRoles(portal):
    rmanager = portal.acl_users.role_manager
    rmanager.addRole('Member', title="Portal Member")
    rmanager.addRole('Reviewer', title="Content Reviewer")

def registerPluginType(pas, plugin_type, plugin_info):
    pas.plugins._plugin_type_info[plugin_type] =  plugin_info
    pas.plugins._plugin_types.append(plugin_type)

def registerPluginTypes(pas):

    PluginInfo = {
        'id' : 'IUserManagement',
        'title': 'user_management',
        'description': ("The User Management plugins allow the "
                        "Pluggable Auth Service to add/delete/modify users")
        }

    registerPluginType(pas, IUserManagement, PluginInfo)

    PluginInfo = {
        'id' : 'IGroupManagement',
        'title': 'group_management',
        'description': ("Group Management provides add/write/deletion "
                        "of groups and member management")
        }

    registerPluginType(pas, igroup.IGroupManagement, PluginInfo)

    PluginInfo = {
        'id' : 'IGroupIntrospection',
        'title': 'group_introspection',
        'description': ("Group Introspection provides listings "
                        "of groups and membership")
        }

    registerPluginType(pas, igroup.IGroupIntrospection, PluginInfo)

    PluginInfo = {
        'id' : 'ILocalRolesPlugin',
        'title': 'local_roles',
        'description': "Defines Policy for getting Local Roles"
        }

    registerPluginType(pas, ILocalRolesPlugin, PluginInfo)

def setupPlugins(portal, out):
    uf = portal.acl_users
    print >> out, "\nPlugin setup"

    pas = uf.manage_addProduct['PluggableAuthService']
    pas.addCookieAuthHelper('credentials_cookie', cookie_name='__ac')
    print >> out, "Added Cookie Auth Helper."
    activatePluginInterfaces(portal, 'credentials_cookie', out)

    credentials_cookie = uf._getOb('credentials_cookie')
    if 'login_form' in credentials_cookie.objectIds():
        credentials_cookie.manage_delObjects(ids=['login_form'])
        print >> out, "Removed default login_form from credentials cookie."

    pas.addHTTPBasicAuthHelper('credentials_basic_auth',
                               title="HTTP Basic Auth")
    print >> out, "Added Basic Auth Helper."
    activatePluginInterfaces(portal, 'credentials_basic_auth', out)

    plone_pas = uf.manage_addProduct['PlonePAS']
    plone_pas.manage_addUserManager('source_users')
    print >> out, "Added User Manager."
    activatePluginInterfaces(portal, 'source_users', out)

    plone_pas.manage_addGroupAwareRoleManager('portal_role_manager')
    print >> out, "Added Group Aware Role Manager."
    activatePluginInterfaces(portal, 'portal_role_manager', out)

    plone_pas.manage_addLocalRolesManager('local_roles')
    print >> out, "Added Group Aware Role Manager."
    activatePluginInterfaces(portal, 'local_roles', out)

    plone_pas.manage_addGroupManager('source_groups')
    print >> out, "Added ZODB Group Manager."
    activatePluginInterfaces(portal, 'source_groups', out)

    plone_pas.manage_addPloneUserFactory('user_factory')
    print >> out, "Added Plone User Factory."
    activatePluginInterfaces(portal, "user_factory", out)

    plone_pas.manage_addZODBMutablePropertyProvider('mutable_properties')
    print >> out, "Added Mutable Property Manager."
    activatePluginInterfaces(portal, "mutable_properties", out)

def configurePlonePAS(portal, out):
    """Add the necessary objects to make a usable PAS instance
    """
    registerPluginTypes(portal.acl_users)
    setupPlugins(portal, out)
#    setupRoles( portal )

def grabUserData(portal, out):
    """Return a list of (id, password, roles, domains, properties)
    tuples for the users of the system.

    Password may be encypted or not: addUser will figure it out.
    """
    print >> out, "\nExtract Member information..."

    userdata = ()
    mdtool = getToolByName(portal, 'portal_memberdata')
    mtool = getToolByName(portal, 'portal_membership')

    props = mdtool.propertyIds()
    members = mtool.listMembers()
    for member in members:
        id = member.getId()
        print >> out, " : %s" % id
        password = member.getPassword()
        roles = [role for role in member.getRoles() if role != 'Authenticated']
        print >> out, "with roles %s" % roles
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
    emerg = portal.acl_users._emergency_user
    for u in userdata:
        if u[0] == str(emerg):
            print >> out, " : WARNING! member '%s' has name of emergency user. Not migrated." % u[0]
            print >> out, "You can undo the install if you want to fix this condition."
            continue  # skip Emergency User, if present
        
        # be careful of non-ZODB member sources, like LDAP
        member = mtool.getMemberById(u[0])
        if member is None:
            mtool.addMember(*u)
            print >> out, " : adding member '%s'" % u[0]
        else:
            # set any properties. do we need anything else? roles, maybe?
            member.setMemberProperties(userdata[-1])
            print >> out, " : setting props on member '%s'" % member.getId()

    print >> out, "...restore done"

def grabGroupData(portal, out):
    """Return a list of (id, roles, groups, properties) tuples for the
    users of the system and a mapping of group ids to a list of group
    members.

    Password may be encypted or not: addUser will figure it out.
    """
    print >> out, "\nExtract Group information..."

    groupdata = ()
    groupmemberships = {}
    gdtool = getToolByName(portal, 'portal_groupdata', None)
    gtool = getToolByName(portal, 'portal_groups', None)

    if gdtool is None or gtool is None:
        print >> out, ('\nGroup-aware tools not found. Skipping '
                       'group data migration.')

    props = gdtool.propertyIds()

    uf = getToolByName(portal, 'acl_users')
    if hasattr(uf, 'getGroups'):
        # Must be a GRUF for this to work.
        groups = gtool.listGroups()
        for group in groups:
            id = group.getGroupId()
            print >> out, " : %s" % id
            roles = [role for role in group.getRoles() if role != 'Authenticated']
            print >> out, "with roles %s" % roles
            properties = {}
            has_groups = [] # we take care of this with the
                            # groupmemberships stuff
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
        print >> out, " : adding group '%s' with members: " % g[0]
        gtool.addGroup(*g)

        # restore group memberships
        gid = g[0]
        group = gtool.getGroupById(gid)
        for mid in groupmemberships[gid]:
            group.addMember(mid)
            print >> out, "%s " % mid

    print >> out, "...restore done"


def setupTools(portal, out):
    print >> out, "\nTools:"

    migratePloneTool(portal, out)
    migrateMembershipTool(portal, out)
    migrateGroupsTool(portal, out)
    migrateMemberDataTool(portal, out)
    migrateGroupDataTool(portal, out)

def migratePloneTool(portal, out):
    print >> out, "Plone Tool (plone_utils)"
    print >> out, " ...nothing to migrate"
    print >> out, " - Removing Default"
    portal.manage_delObjects(['plone_utils'])
    print >> out, " - Installing PAS Aware"
    portal._setObject(PloneTool.id, PloneTool())
    print >> out, " ...done"

def migrateMembershipTool(portal, out):
    print >> out, "Membership Tool (portal_membership)"

    mt = getToolByName(portal, 'portal_membership')
    print >> out, " ...copying settings"
    memberareaCreationFlag = mt.getMemberareaCreationFlag()
    role_map = getattr(mt, 'role_map', None)
    membersfolder_id = mt.membersfolder_id

    print >> out, " ...copying actions"
    actions = mt._actions

    print >> out, " - Removing Default"
    portal.manage_delObjects(['portal_membership'])

    print >> out, " - Installing PAS Aware"
    portal._setObject(MembershipTool.id, MembershipTool())

    # Get new tool.
    mt = getToolByName(portal, 'portal_membership')

    print >> out, " ...restoring settings"
    mt.memberareaCreationFlag = memberareaCreationFlag
    if role_map:
        mt.role_map = role_map
    if membersfolder_id:
        mt.membersfolder_id = membersfolder_id

    print >> out, " ...restoring actions"
    mt._actions = actions

    print >> out, " ...done"

def migrateGroupsTool(portal, out):
    print >> out, "Groups Tool (portal_groups)"
    gt = getToolByName(portal, 'portal_groups', None)

    HAS_GT = gt is not None

    if HAS_GT:
        print >> out, " ...copying settings"
        groupworkspaces_id = gt.getGroupWorkspacesFolderId()
        groupworkspaces_title =  gt.getGroupWorkspacesFolderTitle()
        groupWorkspacesCreationFlag =  gt.getGroupWorkspacesCreationFlag()
        groupWorkspaceType =  gt.getGroupWorkspaceType()
        groupWorkspaceContainerType =  gt.getGroupWorkspaceContainerType()

        print >> out, " ...copying actions"
        actions = gt._actions

        print >> out, " - Removing Default"
        portal.manage_delObjects(['portal_groups'])

    print >> out, " - Installing PAS Aware"
    portal._setObject(GroupsTool.id, GroupsTool())

    gt = getToolByName(portal, 'portal_groups')

    if HAS_GT:
        print >> out, " ...restoring settings"
        gt.setGroupWorkspacesFolder(groupworkspaces_id, groupworkspaces_title)
        gt.groupWorkspacesCreationFlag = groupWorkspacesCreationFlag
        gt.setGroupWorkspaceType(groupWorkspaceType)
        gt.setGroupWorkspaceContainerType(groupWorkspaceContainerType)

        print >> out, " ...restoring actions"
        gt._actions = actions

    print >> out, " ...done"

def migrateGroupDataTool(portal, out):
    # this could be somewhat combined with migrateMemberDataTool, but
    # I don't think it's worth it

    print >> out, "GroupData Tool (portal_groupdata)"
    gt = getToolByName(portal, 'portal_groupdata', None)

    HAS_GT = gt is not None

    if HAS_GT:
        print >> out, " ...copying actions"
        actions = gt._actions

        print >> out, " ...extracting data"
        properties = gt._properties
        for elt in properties:
            elt['value'] = gt.getProperty(elt['id'])

        print >> out, " - Removing Default"
        portal.manage_delObjects(['portal_groupdata'])

    print >> out, " - Installing PAS Aware"
    portal._setObject(GroupDataTool.id, GroupDataTool())
    gt = getToolByName(portal, 'portal_groupdata')

    if HAS_GT:
        print >> out, " ...restoring actions"
        gt._actions = actions

        print >> out, " ...restoring data"
        for prop in properties:
            updateProp(gt, prop)

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
    """Provided a PropertyManager and a property dict of {id, value,
    type}, set or update that property as applicable.

    Doesn't deal with existing properties changing type.
    """
    id = prop_dict['id']
    value = prop_dict['value']
    type = prop_dict['type']
    if prop_manager.hasProperty(id):
        prop_manager._updateProperty(id, value)
    else:
        prop_manager._setProperty(id, value, type)


def grabLDAPFolders(portal, out):
    """Get hold of any existing LDAPUserFolders so that we can put
    them into LDAPMultiPlugins later.
    """
    print >> out, "\nPreserving LDAP folders, if any:"

    user_sources = portal.acl_users.listUserSources()
    group_source = portal.acl_users.Groups.acl_users

    ldap_ufs = []
    ldap_gf = None

    for uf in user_sources:
        if uf.meta_type == "LDAPUserFolder":
            print >> out, " - LDAPUserFolder %s" % uf.title
            ldap_ufs.append(uf)

    if group_source.meta_type == "LDAPGroupFolder %s" % group_source.title:
        print >> out, " - LDAPGroupFolder"
        ldap_gf = group_source

    print >> out, "...done"
    return ldap_ufs, ldap_gf

def restoreLDAP(portal, out, ldap_ufs, ldap_gf):
    """Create appropriate plugins to replace destroyed LDAP user
    folders.
    """
    if not (ldap_ufs or ldap_gf):
        print >> out, "\nNo LDAP auth sources to restore. Skipping."
    else:
        print >> out, "\nRestoring LDAP auth sources:"
        pas = portal.acl_users

        x = ""
        if len(ldap_ufs) > 1:
            x = 0
        for lduf in ldap_ufs:
            id = 'ad_multi%s' % x
            title = 'ActiveDirectory Multi-plugin %s' % x
            LDAP_server = lduf.LDAP_server + ":" + `lduf.LDAP_port`
            login_attr = lduf._login_attr
            uid_attr = lduf._uid_attr
            users_base = lduf.users_base
            users_scope = lduf.users_scope
            roles = lduf._roles
            groups_base = lduf.groups_base
            groups_scope = lduf.groups_scope
            binduid = lduf._binduid
            bindpwd = lduf._bindpwd
            binduid_usage = lduf._binduid_usage
            rdn_attr = lduf._rdnattr
            local_groups = lduf._local_groups
            use_ssl = lduf._conn_proto == 'ldaps'
            encryption = lduf._pwd_encryption
            read_only = lduf.read_only

            ldapmp = pas.manage_addProduct['LDAPMultiPlugins']
            ldapmp.manage_addActiveDirectoryMultiPlugin(
                id, title,
                LDAP_server, login_attr,
                uid_attr, users_base, users_scope, roles,
                groups_base, groups_scope, binduid, bindpwd,
                binduid_usage=1, rdn_attr='cn', local_groups=0,
                use_ssl=0 , encryption='SHA', read_only=0)
            print >> out, "Added ActiveDirectoryMultiPlugin %s" % x
            x = x or 0 + 1

            activatePluginInterfaces(portal, id, out)
            # turn off groups
            pas.plugins.deactivatePlugin(IGroupsPlugin, id)
            pas.plugins.deactivatePlugin(IGroupEnumerationPlugin, id)
            # move properties up
            pas.plugins.movePluginsUp(IPropertiesPlugin, [id])

def replaceUserFolder(portal, out):
    print >> out, "\nUser folder replacement:"

    print >> out, " - Removing existing user folder"
    portal.manage_delObjects(['acl_users'])

    addPAS(portal, out)

    print >> out, "...replace done"

def addPAS(portal, out):
    print >> out, " - Adding PAS user folder"
    portal.manage_addProduct['PluggableAuthService'].addPluggableAuthService()

def goForMigration(portal, out):
    """Checks for supported configurations.
    Other configurations might work. The migration code is pretty generic.

    Should provide some way to extend this check.
    """
    if not canAutoMigrate(portal.acl_users):
        msg = ("Your user folder is in a configuration not supported "
               "by the migration script.\nOnly GroupUserFolders with "
               "basic UserFolder and LDAPUserFolder sources can be "
               "migrated at this time.\nAny other setup will require "
               "custom migration. You may install PlonePAS empty by "
               "deleting you current UserFolder.")
        raise Exception, msg

    return 1


def install(self):
    out = StringIO()
    portal = getToolByName(self, 'portal_url').getPortalObject()

    EXISTING_UF = 'acl_users' in portal.objectIds()

    userdata = grabUserData(portal, out)
    groupdata, memberships = grabGroupData(portal, out)

    if not EXISTING_UF:
        addPAS(portal, out)
    else:
        goForMigration(portal, out)

        ldap_ufs, ldap_gf = grabLDAPFolders(portal, out)
        if (ldap_ufs or ldap_gf) and not CAN_LDAP:
            raise Exception, ("LDAPUserFolders present, but LDAPMultiPlugins "
                              "not present. To successfully auto-migrate, "
                              "the LDAPMultiPlugins product must be installed. "
                              "(%s, %s):%s" % (ldap_ufs, ldap_gf, CAN_LDAP))

        replaceUserFolder(portal, out)

    install_subskin(self, out, config.GLOBALS)
    print >> out, "\nInstalled skins."

    configurePlonePAS(portal, out)

    setupTools(portal, out)

    if EXISTING_UF:
        if CAN_LDAP:
            restoreLDAP(portal, out, ldap_ufs, ldap_gf)

    restoreUserData(portal, out, userdata)
    restoreGroupData(portal, out, groupdata, memberships)

    print >> out, "\nSuccessfully installed %s." % config.PROJECTNAME
    return out.getvalue()


# Future refactor notes:
#  we cannot tell automatically between LDAP and AD uses of LDAPUserFolder
#    - except maybe sAMAAccountName
#    - so some sort of UI is necessary
#  should have some sort of facility for allowing easy extension of migration of UFs
#    - register grab and restore methods, or something
#  cannot currently handle GRUFGroupsFolder
#  can probably handle multiple LDAPUserFolders, but not tested
