##############################################################################
#
# PlonePAS - Adapt PluggableAuthService for use in Plone
# Copyright (C) 2005 Enfold Systems, Kapil Thangavelu, et al
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this
# distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""
"""

from sets import Set
from StringIO import StringIO

from Products.CMFCore.utils import getToolByName
from Products.CMFCore.Expression import Expression

from zope.component.interfaces import ComponentLookupError

from Products.PluggableAuthService.interfaces.authservice \
        import IPluggableAuthService
from Products.PluggableAuthService.interfaces.plugins import IPropertiesPlugin
from Products.PluggableAuthService.interfaces.plugins import IGroupsPlugin
from Products.PluggableAuthService.interfaces.plugins \
     import IGroupEnumerationPlugin
from Products.PluggableAuthService.interfaces.plugins \
     import ICredentialsResetPlugin
from Products.PluggableAuthService.interfaces.plugins \
     import IChallengePlugin
from Products.PluggableAuthService.Extensions.upgrade \
     import replace_acl_users

from Products.PlonePAS import config
from Products.PlonePAS.interfaces.plugins import IUserManagement
from Products.PlonePAS.interfaces.plugins import IUserIntrospection
from Products.PlonePAS.interfaces.plugins import ILocalRolesPlugin
from Products.PlonePAS.interfaces import group as igroup

from Products.PlonePAS.tools.groups import GroupsTool
from Products.PlonePAS.tools.groupdata import GroupDataTool
from Products.PlonePAS.tools.membership import MembershipTool
from Products.PlonePAS.tools.memberdata import MemberDataTool

from Products.PlonePAS.MigrationCheck import canAutoMigrate
from plone.session.plugins.session import manage_addSessionPlugin

try:
    import Products.LDAPMultiPlugins
    CAN_LDAP = True
except ImportError:
    CAN_LDAP = False


def activatePluginInterfaces(portal, plugin, out, disable=[]):
    pas = portal.acl_users
    plugin_obj = pas[plugin]

    activatable = []

    for info in plugin_obj.plugins.listPluginTypeInfo():
        interface = info['interface']
        interface_name = info['id']
        if plugin_obj.testImplements(interface):
            if interface_name in disable:
                disable.append(interface_name)
                print >> out, " - Disabling: " + info['title']
            else:
                activatable.append(interface_name)
                print >> out, " - Activating: " + info['title']
    plugin_obj.manage_activateInterfaces(activatable)
    print >> out, plugin + " activated."


def installProducts(portal, out):
    print >> out, "\nInstalling other products"
    qi = getToolByName(portal, 'portal_quickinstaller')

    print >> out, " - PasswordResetTool"
    qi.installProduct('PasswordResetTool')


def setupRoles(portal):
    rmanager = portal.acl_users.role_manager
    rmanager.addRole('Member', title="Portal Member")
    rmanager.addRole('Reviewer', title="Content Reviewer")


def registerPluginType(pas, plugin_type, plugin_info):
    # Make sure there's no dupes in _plugin_types, otherwise your PAS
    # will *CRAWL*
    plugin_types = list(Set(pas.plugins._plugin_types))
    if not plugin_type in plugin_types:
        plugin_types.append(plugin_type)

    # Order doesn't seem to matter, but let's store it ordered.
    plugin_types.sort()

    # Re-assign to the object, because this is a non-persistent list.
    pas.plugins._plugin_types = plugin_types

    # It's safe to assign over a existing key here.
    pas.plugins._plugin_type_info[plugin_type] =  plugin_info


def registerPluginTypes(pas):

    PluginInfo = {
        'id' : 'IUserManagement',
        'title': 'user_management',
        'description': ("The User Management plugins allow the "
                        "Pluggable Auth Service to add/delete/modify users")
        }

    registerPluginType(pas, IUserManagement, PluginInfo)

    PluginInfo = {
        'id' : 'IUserIntrospection',
        'title': 'user_introspection',
        'description': ("The User Introspection plugins allow the "
                        "Pluggable Auth Service to provide lists of users")
        }

    registerPluginType(pas, IUserIntrospection, PluginInfo)

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
    plone_pas = uf.manage_addProduct['PlonePAS']

    setupAuthPlugins(portal, pas, plone_pas, out)

    found = uf.objectIds(['User Manager'])
    if not found:
        plone_pas.manage_addUserManager('source_users')
        print >> out, "Added User Manager."
    activatePluginInterfaces(portal, 'source_users', out)

    found = uf.objectIds(['Group Aware Role Manager'])
    if not found:
        plone_pas.manage_addGroupAwareRoleManager('portal_role_manager')
        print >> out, "Added Group Aware Role Manager."
        activatePluginInterfaces(portal, 'portal_role_manager', out)

    found = uf.objectIds(['Local Roles Manager'])
    if not found:
        plone_pas.manage_addLocalRolesManager('local_roles')
        print >> out, "Added Group Aware Role Manager."
        activatePluginInterfaces(portal, 'local_roles', out)

    found = uf.objectIds(['Group Manager'])
    if not found:
        plone_pas.manage_addGroupManager('source_groups')
        print >> out, "Added ZODB Group Manager."
        activatePluginInterfaces(portal, 'source_groups', out)

    found = uf.objectIds(['Plone User Factory'])
    if not found:
        plone_pas.manage_addPloneUserFactory('user_factory')
        print >> out, "Added Plone User Factory."
        activatePluginInterfaces(portal, "user_factory", out)

    found = uf.objectIds(['ZODB Mutable Property Provider'])
    if not found:
        plone_pas.manage_addZODBMutablePropertyProvider('mutable_properties')
        print >> out, "Added Mutable Property Manager."
        activatePluginInterfaces(portal, "mutable_properties", out)

    found = uf.objectIds(['Automatic Group Plugin'])
    if not found:
        plone_pas.manage_addAutoGroup('auto_group', "Automatic Group Provider",
                "AuthenticatedUsers", "Authenticated Users (Virtual Group)")
        print >> out, "Added Automatic Group."
        activatePluginInterfaces(portal, "auto_group", out)

    found = uf.objectIds(['Plone Session Plugin'])
    if not found:
        manage_addSessionPlugin(plone_pas, 'session')
        print >> out, "Added Plone Session Plugin."
        activatePluginInterfaces(portal, "session", out)


def setupAuthPlugins(portal, pas, plone_pas, out,
                     deactivate_basic_reset=True,
                     deactivate_cookie_challenge=False):
    uf = portal.acl_users
    print >> out, " cookie plugin setup"

    login_path = 'login_form'
    logout_path = 'logged_out'
    cookie_name = '__ac'

    crumbler = getToolByName(portal, 'cookie_authentication', None)
    if crumbler is not None:
        login_path = crumbler.auto_login_page
        logout_path = crumbler.logout_page
        cookie_name = crumbler.auth_cookie

    # note: old versions of PlonePAS (< 0.4.2) may leave a 'Cookie
    #       Auth Helper' by the same name
    found = uf.objectIds(['Cookie Auth Helper'])
    if found and 'credentials_cookie_auth' in found:
        print >> out, " old credentials_cookie_auth found; removing"
        login_path = uf.credentials_cookie_auth.login_path
        cookie_name = uf.credentials_cookie_auth.cookie_name
        uf.manage_delObjects(['credentials_cookie_auth'])

    found = uf.objectIds(['Extended Cookie Auth Helper'])
    if not found:
        plone_pas.manage_addExtendedCookieAuthHelper('credentials_cookie_auth',
                                                     cookie_name=cookie_name)
    print >> out, "Added Extended Cookie Auth Helper."
    if deactivate_basic_reset:
        disable=['ICredentialsResetPlugin', 'ICredentialsUpdatePlugin']
    else:
        disable=[]
    activatePluginInterfaces(portal, 'credentials_cookie_auth', out,
            disable=disable)

    credentials_cookie_auth = uf._getOb('credentials_cookie_auth')
    if 'login_form' in credentials_cookie_auth.objectIds():
        credentials_cookie_auth.manage_delObjects(ids=['login_form'])
        print >> out, "Removed default login_form from credentials cookie auth."
    credentials_cookie_auth.cookie_name = cookie_name
    credentials_cookie_auth.login_path = login_path

    # remove cookie crumbler(s)
    if 'cookie_authentication' in portal.objectIds():
        portal.manage_delObjects(['cookie_authentication'])

    ccs = portal.objectValues('Cookie Crumbler')
    assert not ccs, "Extra cookie crumblers found."
    print >> out, "Removed old Cookie Crumbler"

    found = uf.objectIds(['HTTP Basic Auth Helper'])
    if not found:
        pas.addHTTPBasicAuthHelper('credentials_basic_auth',
                               title="HTTP Basic Auth")
    print >> out, "Added Basic Auth Helper."
    activatePluginInterfaces(portal, 'credentials_basic_auth', out)

    if deactivate_basic_reset:
        uf.plugins.deactivatePlugin(ICredentialsResetPlugin,
                                     'credentials_basic_auth')
    if deactivate_cookie_challenge:
        uf.plugins.deactivatePlugin(IChallengePlugin,
                                     'credentials_cookie_auth')


def configurePlonePAS(portal, out):
    """Add the necessary objects to make a usable PAS instance
    """
    installProducts(portal, out)
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
    try:
        mdtool = getToolByName(portal, "portal_memberdata")
        mtool = getToolByName(portal, "portal_membership")
    except ComponentLookupError:
        return userdata

    props = mdtool.propertyIds()
    members = mtool.listMembers()
    userids=set()
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
        portrait=mtool.getPersonalPortrait(id)
        if portrait is not None:
            portrait=portrait.aq_base
        userdata += ((id, password, roles, domains, properties, portrait),)
        userids.add(id)

    for (id,data) in mdtool._members.items():
        if id not in userids:
            userdata+= ((id, None, None, None, data.__dict__, None),)
            userids.add(id)

    print >> out, "...extract done"
    return userdata


def restoreUserData(portal, out, userdata):
    print >> out, "\nRestoring Member information..."

    # re-add users
    # Password may be encypted or not: addUser will figure it out.
    mdtool = getToolByName(portal, "portal_memberdata")
    mtool = getToolByName(portal, "portal_membership")
    emerg = portal.acl_users._emergency_user.getId()
    for u in userdata:
        if u[0] == emerg:
            print >> out, (" : WARNING! member '%s' has name of "
                           "emergency user. Not migrated." % u[0])
            print >> out, ("You can undo the install if you want "
                           "to fix this condition.")
            continue  # skip Emergency User, if present

        # be careful of non-ZODB member sources, like LDAP
        member = mtool.getMemberById(u[0])
        if member is None:
            if u[1] is not None:
                mtool.addMember(*u[:5])
                print >> out, " : adding member '%s'" % u[0]
            else:
                print >> out, " : ignored member '%s' without password." % u[0]
        else:
            # set any properties. do we need anything else? roles, maybe?
            member.setMemberProperties(u[4])
            print >> out, " : setting props on member '%s'" % member.getId()

        if u[5] is not None:
            mdtool._setPortrait(u[5], u[0])

    print >> out, "...restore done"


def grabGroupData(portal, out):
    """Return a list of (id, roles, groups, properties) tuples for the
    users of the system and a mapping of group ids to a list of group
    members.
    """
    print >> out, "\nExtract Group information..."

    groupdata = ()
    groupmemberships = {}
    gdtool = getToolByName(portal, 'portal_groupdata', None)
    gtool = getToolByName(portal, 'portal_groups', None)

    if gdtool is None or gtool is None:
        print >> out, ('\nGroup-aware tools not found. Skipping '
                       'group data migration.')
        return groupdata, groupmemberships

    props = gdtool.propertyIds()

    uf = getToolByName(portal, 'acl_users')
    if hasattr(uf, 'getGroups'):
        # Must be a GRUF for this to work.
        groups = gtool.listGroups()
        for group in groups:
            id = group.getGroupName()  # in GRUF 2, getGroupId is prefixed!
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
    gtool = getToolByName(portal, 'portal_groups')
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
    modActions(portal, out)


def migratePloneTool(portal, out):
    print >> out, "Plone Tool (plone_utils)"
    pt = portal.plone_utils
    if pt.meta_type == 'PlonePAS Utilities Tool':
        from Products.CMFPlone.PloneTool import PloneTool
        print >> out, " - Removing obsolete PlonePAS version of the Plone Tool"
        portal.manage_delObjects(['plone_utils'])
        print >> out, " - Installing standard tool"
        portal._setObject(PloneTool.id, PloneTool())
    print >> out, " ...done"


def migrateMembershipTool(portal, out):
    print >> out, "Membership Tool (portal_membership)"

    mt = getToolByName(portal, "portal_membership")
    print >> out, " ...copying settings"
    memberareaCreationFlag = mt.getMemberareaCreationFlag()
    role_map = getattr(mt, 'role_map', None)
    membersfolder_id = mt.membersfolder_id

    print >> out, " ...copying actions"
    actions = getattr(mt, '_actions', None)

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

    if actions is not None:
        print >> out, " ...restoring actions"
        mt._actions = actions

    print >> out, " ...done"


def migrateGroupsTool(portal, out):
    print >> out, "Groups Tool (portal_groups)"
    # We only want the physical object in the portal, getToolByName could give
    # us a registered utility as well
    gt = getattr(portal, 'portal_groups', None)

    HAS_GT = gt is not None

    if HAS_GT:
        print >> out, " ...copying settings"
        groupworkspaces_id = gt.getGroupWorkspacesFolderId()
        groupworkspaces_title =  gt.getGroupWorkspacesFolderTitle()
        groupWorkspacesCreationFlag =  gt.getGroupWorkspacesCreationFlag()
        groupWorkspaceType =  gt.getGroupWorkspaceType()
        groupWorkspaceContainerType =  gt.getGroupWorkspaceContainerType()

        print >> out, " ...copying actions"
        actions = getattr(gt, '_actions', None)

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

        if actions is not None:
            print >> out, " ...restoring actions"
            gt._actions = actions

    print >> out, " ...done"


def migrateGroupDataTool(portal, out):
    # this could be somewhat combined with migrateMemberDataTool, but
    # I don't think it's worth it

    print >> out, "GroupData Tool (portal_groupdata)"
    # We only want the physical object in the portal, getToolByName could give
    # us a registered utility as well
    gt = getattr(portal, 'portal_groupdata', None)

    HAS_GT = gt is not None

    if HAS_GT:
        print >> out, " ...copying actions"
        actions = getattr(gt, '_actions', None)

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
        if actions is not None:
            print >> out, " ...restoring actions"
            gt._actions = actions

        print >> out, " ...restoring data"
        
        updateProperties(gt, properties)

    print >> out, " ...done"


def migrateMemberDataTool(portal, out):
    print >> out, "MemberData Tool (portal_memberdata)"

    print >> out, " ...copying actions"
    actions = getattr(portal.portal_memberdata, '_actions', None)

    print >> out, "  ...extracting data"
    mdtool = portal.portal_memberdata
    properties = mdtool._properties
    for elt in properties:
        elt['value'] = mdtool.getProperty(elt['id'])

    mdtool = None
    print >> out, " - Removing existing portal_memberdata tool"
    portal.manage_delObjects(['portal_memberdata'])

    print >> out, " - Installing PAS Aware tool"
    portal._setObject(MemberDataTool.id, MemberDataTool())

    if actions is not None:
        print >> out, " ...restoring actions"
        portal.portal_memberdata._actions = actions

    print >> out, " ...restoring data"
    mdtool = portal.portal_memberdata
    
    updateProperties(mdtool, properties)

    print >> out, " ...done"


def modActions(portal, out):
    """Change any actions necessary to support PAS."""
    # condition "set password" on capability
    cp = getToolByName(portal, 'portal_controlpanel', None)
    _actions = cp._cloneActions()
    for action in _actions:
        if action.id=='MemberPassword':
            action.condition = Expression("python:member.canPasswordSet()")
    cp._actions=_actions


def updateProperties(tool, properties):
    propsWithNoDeps = [prop for prop in properties if prop['type'] not in ('selection', 'multiple selection')]
    propsWithDeps = [prop for prop in properties if prop['type'] in ('selection', 'multiple selection')]
    for prop in propsWithNoDeps:
        updateProp(tool, prop)
    for prop in propsWithDeps:
        updateProp(tool, prop)


def updateProp(prop_manager, prop_dict):
    """Provided a PropertyManager and a property dict of {id, value,
    type}, set or update that property as applicable.

    Doesn't deal with existing properties changing type.
    """
    id = prop_dict['id']
    value = prop_dict['value']
    type = prop_dict['type']
    if type in ('selection', 'multiple selection'):
        value = prop_dict['select_variable']
    if prop_manager.hasProperty(id):
        prop_manager._updateProperty(id, value)
    else:
        prop_manager._setProperty(id, value, type)
    if type in ('selection', 'multiple selection'):
        prop_manager._updateProperty(id, prop_dict['value'])


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

            # attribute over-rides
            uid_attr = login_attr = "sAMAccountName"

            ldapmp = pas.manage_addProduct['LDAPMultiPlugins']
            ldapmp.manage_addActiveDirectoryMultiPlugin(
                id, title,
                LDAP_server, login_attr,
                uid_attr, users_base, users_scope, roles,
                groups_base, groups_scope, binduid, bindpwd,
                binduid_usage=1, rdn_attr='cn', local_groups=0,
                use_ssl=0 , encryption='SHA', read_only=0)
            getattr(pas,id).groupid_attr = 'cn'

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

def migrate_root_uf(self, out):
    # Acquire parent user folder.
    parent = self.getPhysicalRoot()
    uf = getToolByName(parent, 'acl_users')
    if IPluggableAuthService.providedBy(uf):
        # It's a PAS already, fixup if needed.
        pas_fixup(parent, out)

        # Configure Challenge Chooser plugin if available
        challenge_chooser_setup(parent, out)
        return

    if not uf.meta_type == 'User Folder':
        # It's not a standard User Folder at the root. Nothing we can do.
        return

    # It's a standard User Folder, replace it.
    replace_acl_users(parent, out)

    # Get the new uf
    uf = getToolByName(parent, 'acl_users')

    pas = uf.manage_addProduct['PluggableAuthService']
    plone_pas = uf.manage_addProduct['PlonePAS']
    # Setup authentication plugins
    setupAuthPlugins(parent, pas, plone_pas, out,
                     deactivate_basic_reset=False,
                     deactivate_cookie_challenge=True)

    # Activate *all* interfaces for user manager. IUserAdder is not
    # activated for some reason by default.
    activatePluginInterfaces(parent, 'users', out)

    # Configure Challenge Chooser plugin if available
    challenge_chooser_setup(parent, out)

def pas_fixup(self, out):
    from Products.PluggableAuthService.PluggableAuthService \
         import _PLUGIN_TYPE_INFO, PluggableAuthService

    pas = getToolByName(self, 'acl_users')
    if not IPluggableAuthService.providedBy(pas):
        print >> out, 'PAS UF not found, skipping PAS fixup'
        return

    plugins = pas['plugins']

    plugin_types = list(Set(plugins._plugin_types))
    for key, id, title, description in _PLUGIN_TYPE_INFO:
        if key in plugin_types:
            print >> out, "Plugin type '%s' already registered." % id
            continue
        print >> out, "Plugin type '%s' was not registered." % id
        plugin_types.append(key)
        plugins._plugin_type_info[key] = {
            'id': id,
            'title': title,
            'description': description,
            }
    # Make it ordered
    plugin_types.sort()

    # Re-assign because it's a non-persistent property.
    plugins._plugin_types = plugin_types

def challenge_chooser_setup(self, out):
    uf = getToolByName(self, 'acl_users')
    plugins = uf['plugins']
    pas = uf.manage_addProduct['PluggableAuthService']

    # Only install plugins if available
    req = ('addChallengeProtocolChooserPlugin',
           'addRequestTypeSnifferPlugin')
    for m in req:
        if getattr(pas, m, None) is None:
            print >> out, 'Needed plugins have not been found, ignoring'
            return

    found = uf.objectIds(['Challenge Protocol Chooser Plugin'])
    if not found:
        print >> out, 'Adding Challenge Protocol Chooser Plugin.'
        pas.addChallengeProtocolChooserPlugin(
            'chooser',
            mapping=config.DEFAULT_PROTO_MAPPING)
        activatePluginInterfaces(self, 'chooser', out)
    else:
        assert len(found) == 1, 'Found extra plugins %s' % found
        print >> out, 'Found existing Challenge Protocol Chooser Plugin.'
        plugin = uf[found[0]]
        plugin.manage_updateProtocolMapping(mapping=config.DEFAULT_PROTO_MAPPING)
        activatePluginInterfaces(self, found[0], out)

    found = uf.objectIds(['Request Type Sniffer Plugin'])
    if not found:
        print >> out, 'Adding Request Type Sniffer Plugin.'
        pas.addRequestTypeSnifferPlugin('sniffer')
        activatePluginInterfaces(self, 'sniffer', out)
    else:
        assert len(found) == 1, 'Found extra plugins %s' % found
        print >> out, 'Found existing Request Type Sniffer Plugin.'
        activatePluginInterfaces(self, found[0], out)


def install(self):
    out = StringIO()
    portal = getToolByName(self, 'portal_url').getPortalObject()

    uf = getToolByName(self, 'acl_users')

    EXISTING_UF = 'acl_users' in portal.objectIds()
    EXISTING_PAS = IPluggableAuthService.providedBy(uf)

    if EXISTING_PAS:
        # Fix possible missing PAS plugins registration.
        pas_fixup(self, out)

        # Register PAS Plugin Types
        registerPluginTypes(uf)

    ldap_ufs, ldap_gf = None, None
    userdata=groupdata=memberships=()

    if not EXISTING_UF:
        userdata = grabUserData(portal, out)
        addPAS(portal, out)
    elif not EXISTING_PAS:
        # We've got a existing user folder, but it's not a PAS
        # instance.

        goForMigration(portal, out)

        userdata = grabUserData(portal, out)
        groupdata, memberships = grabGroupData(portal, out)

        ldap_ufs, ldap_gf = grabLDAPFolders(portal, out)
        if (ldap_ufs or ldap_gf) and not CAN_LDAP:
            raise Exception, ("LDAPUserFolders present, but LDAPMultiPlugins "
                          "not present. To successfully auto-migrate, "
                          "the LDAPMultiPlugins product must be installed. "
                          "(%s, %s):%s" % (ldap_ufs, ldap_gf, CAN_LDAP))

        replaceUserFolder(portal, out)

    # Configure Challenge Chooser plugin if available
    challenge_chooser_setup(self, out)

    configurePlonePAS(portal, out)

    setupTools(portal, out)

    if (EXISTING_UF and CAN_LDAP
        and ldap_gf is not None
        and ldap_ufs is not None):
        restoreLDAP(portal, out, ldap_ufs, ldap_gf)

    if not EXISTING_PAS:
        restoreUserData(portal, out, userdata)
        restoreGroupData(portal, out, groupdata, memberships)

    # XXX Why do we need to do this?
    migrate_root_uf(self, out)

    print >> out, "\nSuccessfully installed %s." % config.PROJECTNAME
    return out.getvalue()


# Future refactor notes:
#  we cannot tell automatically between LDAP and AD uses of LDAPUserFolder
#    - except maybe sAMAccountName
#    - so some sort of UI is necessary
#  should have some sort of facility for allowing easy extension of migration of UFs
#    - register grab and restore methods, or something
#  cannot currently handle LDAPGroupsFolder
#  can probably handle multiple LDAPUserFolders, but not tested
