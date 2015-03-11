# -*- coding: utf-8 -*-
from Acquisition import aq_parent
from Products.CMFCore.utils import getToolByName
from Products.PlonePAS import config
from Products.PlonePAS.interfaces import group as igroup
from Products.PlonePAS.interfaces.plugins import ILocalRolesPlugin
from Products.PlonePAS.interfaces.plugins import IUserIntrospection
from Products.PlonePAS.interfaces.plugins import IUserManagement
from Products.PluggableAuthService.Extensions.upgrade import replace_acl_users
from Products.PluggableAuthService.interfaces.authservice \
    import IPluggableAuthService
from Products.PluggableAuthService.interfaces.plugins import IChallengePlugin
from Products.PluggableAuthService.interfaces.plugins \
    import ICredentialsResetPlugin
from Products.PluggableAuthService.plugins.RecursiveGroupsPlugin \
    import addRecursiveGroupsPlugin
from plone.session.plugins.session import manage_addSessionPlugin
import logging

logger = logging.getLogger('PlonePAS setup')


def activatePluginInterfaces(portal, plugin, disable=None):
    if disable is None:
        disable = []
    pas = portal.acl_users
    plugin_obj = pas[plugin]

    activatable = []

    for info in plugin_obj.plugins.listPluginTypeInfo():
        interface = info['interface']
        interface_name = info['id']
        if plugin_obj.testImplements(interface):
            if interface_name in disable:
                disable.append(interface_name)
                logger.debug("Disabling: " + info['title'])
            else:
                activatable.append(interface_name)
                logger.debug("Activating: " + info['title'])
    plugin_obj.manage_activateInterfaces(activatable)
    logger.debug(plugin + " activated.")


def setupRoles(portal):
    rmanager = portal.acl_users.role_manager
    rmanager.addRole('Member', title="Portal Member")
    rmanager.addRole('Reviewer', title="Content Reviewer")


def registerPluginType(pas, plugin_type, plugin_info):
    # Make sure there's no dupes in _plugin_types, otherwise your PAS
    # will *CRAWL*
    plugin_types = list(set(pas.plugins._plugin_types))
    if plugin_type not in plugin_types:
        plugin_types.append(plugin_type)

    # Order doesn't seem to matter, but let's store it ordered.
    plugin_types.sort()

    # Re-assign to the object, because this is a non-persistent list.
    pas.plugins._plugin_types = plugin_types

    # It's safe to assign over a existing key here.
    pas.plugins._plugin_type_info[plugin_type] = plugin_info


def registerPluginTypes(pas):

    PluginInfo = {
        'id': 'IUserManagement',
        'title': 'user_management',
        'description': ("The User Management plugins allow the "
                        "Pluggable Auth Service to add/delete/modify users")
    }

    registerPluginType(pas, IUserManagement, PluginInfo)

    PluginInfo = {
        'id': 'IUserIntrospection',
        'title': 'user_introspection',
        'description': ("The User Introspection plugins allow the "
                        "Pluggable Auth Service to provide lists of users")
    }

    registerPluginType(pas, IUserIntrospection, PluginInfo)

    PluginInfo = {
        'id': 'IGroupManagement',
        'title': 'group_management',
        'description': ("Group Management provides add/write/deletion "
                        "of groups and member management")
    }

    registerPluginType(pas, igroup.IGroupManagement, PluginInfo)

    PluginInfo = {
        'id': 'IGroupIntrospection',
        'title': 'group_introspection',
        'description': ("Group Introspection provides listings "
                        "of groups and membership")
    }

    registerPluginType(pas, igroup.IGroupIntrospection, PluginInfo)

    PluginInfo = {
        'id': 'ILocalRolesPlugin',
        'title': 'local_roles',
        'description': "Defines Policy for getting Local Roles"
    }

    registerPluginType(pas, ILocalRolesPlugin, PluginInfo)


def setupPlugins(portal):
    uf = portal.acl_users
    logger.debug("\nPlugin setup")

    pas = uf.manage_addProduct['PluggableAuthService']
    plone_pas = uf.manage_addProduct['PlonePAS']

    setupAuthPlugins(portal, pas, plone_pas)

    found = uf.objectIds(['User Manager'])
    if not found:
        plone_pas.manage_addUserManager('source_users')
        logger.debug("Added User Manager.")
    activatePluginInterfaces(portal, 'source_users')

    found = uf.objectIds(['Group Aware Role Manager'])
    if not found:
        plone_pas.manage_addGroupAwareRoleManager('portal_role_manager')
        logger.debug("Added Group Aware Role Manager.")
        activatePluginInterfaces(portal, 'portal_role_manager')

    found = uf.objectIds(['Local Roles Manager'])
    if not found:
        plone_pas.manage_addLocalRolesManager('local_roles')
        logger.debug("Added Group Aware Role Manager.")
        activatePluginInterfaces(portal, 'local_roles')

    found = uf.objectIds(['Group Manager'])
    if not found:
        plone_pas.manage_addGroupManager('source_groups')
        logger.debug("Added ZODB Group Manager.")
        activatePluginInterfaces(portal, 'source_groups')

    found = uf.objectIds(['Plone User Factory'])
    if not found:
        plone_pas.manage_addPloneUserFactory('user_factory')
        logger.debug("Added Plone User Factory.")
        activatePluginInterfaces(portal, "user_factory")

    found = uf.objectIds(['ZODB Mutable Property Provider'])
    if not found:
        plone_pas.manage_addZODBMutablePropertyProvider('mutable_properties')
        logger.debug("Added Mutable Property Manager.")
        activatePluginInterfaces(portal, "mutable_properties")

    found = uf.objectIds(['Automatic Group Plugin'])
    if not found:
        plone_pas.manage_addAutoGroup(
            "auto_group", "Authenticated Users (Virtual Group)",
            "AuthenticatedUsers", "Automatic Group Provider")
        logger.debug("Added Automatic Group.")
        activatePluginInterfaces(portal, "auto_group")

    found = uf.objectIds(['Plone Session Plugin'])
    if not found:
        manage_addSessionPlugin(plone_pas, 'session')
        logger.debug("Added Plone Session Plugin.")
        activatePluginInterfaces(portal, "session")

    found = uf.objectIds(['Recursive Groups Plugin'])
    if not found:
        addRecursiveGroupsPlugin(plone_pas, 'recursive_groups',
                                 "Recursive Groups Plugin")
        activatePluginInterfaces(portal, 'recursive_groups')
        logger.debug("Added Recursive Groups plugin.")

    setupPasswordPolicyPlugin(portal)


def setupAuthPlugins(portal, pas, plone_pas,
                     deactivate_basic_reset=True,
                     deactivate_cookie_challenge=False):
    uf = portal.acl_users
    logger.debug("Cookie plugin setup")

    login_path = 'login_form'
    cookie_name = '__ac'

    crumbler = getToolByName(portal, 'cookie_authentication', None)
    if crumbler is not None:
        login_path = crumbler.auto_login_page
        cookie_name = crumbler.auth_cookie

    found = uf.objectIds(['Extended Cookie Auth Helper'])
    if not found:
        plone_pas.manage_addExtendedCookieAuthHelper('credentials_cookie_auth',
                                                     cookie_name=cookie_name)
    logger.debug("Added Extended Cookie Auth Helper.")
    if deactivate_basic_reset:
        disable = ['ICredentialsResetPlugin', 'ICredentialsUpdatePlugin']
    else:
        disable = []
    activatePluginInterfaces(
        portal,
        'credentials_cookie_auth',
        disable=disable
    )

    credentials_cookie_auth = uf._getOb('credentials_cookie_auth')
    if 'login_form' in credentials_cookie_auth:
        credentials_cookie_auth.manage_delObjects(ids=['login_form'])
        logger.debug("Removed default login_form from credentials cookie "
                     "auth.")
    credentials_cookie_auth.cookie_name = cookie_name
    credentials_cookie_auth.login_path = login_path

    # remove cookie crumbler(s)
    if 'cookie_authentication' in portal:
        portal.manage_delObjects(['cookie_authentication'])
    logger.debug("Removed old Cookie Crumbler")

    found = uf.objectIds(['HTTP Basic Auth Helper'])
    if not found:
        pas.addHTTPBasicAuthHelper(
            'credentials_basic_auth',
            title="HTTP Basic Auth"
        )
    logger.debug("Added Basic Auth Helper.")
    activatePluginInterfaces(portal, 'credentials_basic_auth')

    if deactivate_basic_reset:
        uf.plugins.deactivatePlugin(
            ICredentialsResetPlugin,
            'credentials_basic_auth'
        )
    if deactivate_cookie_challenge:
        uf.plugins.deactivatePlugin(
            IChallengePlugin,
            'credentials_cookie_auth'
        )


def updateProperties(tool, properties):
    dependency_keys = ('selection', 'multiple selection')
    propsWithNoDeps = [prop for prop in properties
                       if prop['type'] not in dependency_keys]
    propsWithDeps = [prop for prop in properties
                     if prop['type'] in dependency_keys]
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


def addPAS(portal):
    logger.debug("Adding PAS user folder")
    portal.manage_addProduct['PluggableAuthService'].addPluggableAuthService()


def migrate_root_uf(self):
    # Acquire parent user folder.
    parent = self.getPhysicalRoot()
    uf = getToolByName(parent, 'acl_users')
    if IPluggableAuthService.providedBy(uf):
        # It's a PAS already, fixup if needed.
        pas_fixup(parent)

        # Configure Challenge Chooser plugin if available
        challenge_chooser_setup(parent)
        return

    if not uf.meta_type == 'User Folder':
        # It's not a standard User Folder at the root. Nothing we can do.
        return

    # It's a standard User Folder, replace it.
    replace_acl_users(parent)

    # Get the new uf
    uf = getToolByName(parent, 'acl_users')

    pas = uf.manage_addProduct['PluggableAuthService']
    plone_pas = uf.manage_addProduct['PlonePAS']
    # Setup authentication plugins
    setupAuthPlugins(parent, pas, plone_pas,
                     deactivate_basic_reset=False,
                     deactivate_cookie_challenge=True)

    # Activate *all* interfaces for user manager. IUserAdder is not
    # activated for some reason by default.
    activatePluginInterfaces(parent, 'users')

    # Configure Challenge Chooser plugin if available
    challenge_chooser_setup(parent)


def pas_fixup(self):
    from Products.PluggableAuthService.PluggableAuthService \
        import _PLUGIN_TYPE_INFO

    pas = getToolByName(self, 'acl_users')
    if not IPluggableAuthService.providedBy(pas):
        logger.debug('PAS UF not found, skipping PAS fixup.')
        return

    plugins = pas['plugins']

    plugin_types = list(set(plugins._plugin_types))
    for key, id, title, description in _PLUGIN_TYPE_INFO:
        if key in plugin_types:
            logger.debug("Plugin type '%s' already registered." % id)
            continue
        logger.debug("Plugin type '%s' was not registered." % id)
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


def challenge_chooser_setup(self):
    uf = getToolByName(self, 'acl_users')
    pas = uf.manage_addProduct['PluggableAuthService']

    # Only install plugins if available
    req = ('addChallengeProtocolChooserPlugin',
           'addRequestTypeSnifferPlugin')
    for m in req:
        if getattr(pas, m, None) is None:
            logger.debug('Needed plugins have not been found, ignoring')
            return

    found = uf.objectIds(['Challenge Protocol Chooser Plugin'])
    if not found:
        logger.debug('Adding Challenge Protocol Chooser Plugin.')
        pas.addChallengeProtocolChooserPlugin(
            'chooser',
            mapping=config.DEFAULT_PROTO_MAPPING)
        activatePluginInterfaces(self, 'chooser')
    else:
        assert len(found) == 1, 'Found extra plugins %s' % found
        logger.debug('Found existing Challenge Protocol Chooser Plugin.')
        plugin = uf[found[0]]
        plugin.manage_updateProtocolMapping(
            mapping=config.DEFAULT_PROTO_MAPPING)
        activatePluginInterfaces(self, found[0])

    found = uf.objectIds(['Request Type Sniffer Plugin'])
    if not found:
        logger.debug('Adding Request Type Sniffer Plugin.')
        pas.addRequestTypeSnifferPlugin('sniffer')
        activatePluginInterfaces(self, 'sniffer')
    else:
        assert len(found) == 1, 'Found extra plugins %s' % found
        logger.debug('Found existing Request Type Sniffer Plugin.')
        activatePluginInterfaces(self, found[0])


def setupPasswordPolicyPlugin(portal):
    uf = portal.acl_users
    plone_pas = uf.manage_addProduct['PlonePAS']

    found = uf.objectIds(['Default Plone Password Policy'])
    logger.debug("\nDefault Password Ploicy Plugin setup")
    if not found:
        plone_pas.manage_addPasswordPolicyPlugin(
            'password_policy',
            title="Default Plone Password Policy"
        )
        logger.debug("Added Default Plone Password Policy.")
        activatePluginInterfaces(portal, 'password_policy')


def setLoginFormInCookieAuth(context):
    """Makes sure the cookie auth redirects to 'require_login' instead
       of 'login_form'."""
    uf = getattr(context, 'acl_users', None)
    if uf is None or getattr(uf.aq_base, '_getOb', None) is None:
        # we have no user folder or it's not a PAS folder, do nothing
        return
    cookie_auth = uf._getOb('credentials_cookie_auth', None)
    if cookie_auth is None:
        # there's no cookie auth object, do nothing
        return
    current_login_form = cookie_auth.getProperty('login_path')
    if current_login_form != 'login_form':
        # it's customized already, do nothing
        return
    cookie_auth.manage_changeProperties(login_path='require_login')


def addRolesToPlugIn(p):
    """
    XXX This is horrible.. need to switch PlonePAS to a GenericSetup
    based install so this doesn't need to happen.

    Have to manually register the roles from the 'rolemap' step
    with the roles plug-in.
    """
    uf = getToolByName(p, 'acl_users')
    rmanager = uf.portal_role_manager
    roles = ('Reviewer', 'Member')
    existing = rmanager.listRoleIds()
    for role in roles:
        if role not in existing:
            rmanager.addRole(role)


def setupGroups(site):
    """
    Create Plone's default set of groups.
    """
    uf = getToolByName(site, 'acl_users')
    gtool = getToolByName(site, 'portal_groups')
    if not uf.searchGroups(id='Administrators'):
        gtool.addGroup(
            'Administrators',
            title='Administrators',
            roles=['Manager']
        )

    if not uf.searchGroups(id='Site Administrators'):
        gtool.addGroup(
            'Site Administrators',
            title='Site Administrators',
            roles=['Site Administrator']
        )

    if not uf.searchGroups(id='Reviewers'):
        gtool.addGroup('Reviewers', title='Reviewers', roles=['Reviewer'])


def installPAS(portal):
    # Add user folder
    portal.manage_addProduct['PluggableAuthService'].addPluggableAuthService()

    # Configure Challenge Chooser plugin if available
    challenge_chooser_setup(portal)

    # A bunch of general configuration settings
    registerPluginTypes(portal.acl_users)
    setupPlugins(portal)

    # XXX Why are we doing this?
    # According to Sidnei, "either cookie or basic auth for a user in the root
    # folder doesn't work
    # if it's not a PAS UF when you sign in to Plone. IIRC."
    # See: http://twitter.com/#!/sidneidasilva/status/14030732112429056
    # And here's the original commit:
    # http://dev.plone.org/collective/changeset/10720/PlonePAS/trunk/Extensions/Install.py
    if aq_parent(portal):
        migrate_root_uf(portal)


def setupPlonePAS(context):
    """
    Setup PlonePAS step.
    """
    # Only run step if a flag file is present (e.g. not an extension profile)
    if context.readDataFile('plone-pas.txt') is None:
        return
    site = context.getSite()
    if 'acl_users' not in site:
        installPAS(site)
        addRolesToPlugIn(site)
        setupGroups(site)
        setLoginFormInCookieAuth(site)
