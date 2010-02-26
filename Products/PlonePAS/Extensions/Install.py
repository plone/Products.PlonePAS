from Products.CMFCore.utils import getToolByName

from Products.PluggableAuthService.interfaces.authservice \
        import IPluggableAuthService
from Products.PluggableAuthService.interfaces.plugins \
     import ICredentialsResetPlugin
from Products.PluggableAuthService.interfaces.plugins \
     import IChallengePlugin
from Products.PluggableAuthService.Extensions.upgrade \
     import replace_acl_users
from Products.PluggableAuthService.plugins.RecursiveGroupsPlugin \
     import IRecursiveGroupsPlugin, addRecursiveGroupsPlugin

from Products.PlonePAS import config
from Products.PlonePAS.interfaces.plugins import IUserManagement
from Products.PlonePAS.interfaces.plugins import IUserIntrospection
from Products.PlonePAS.interfaces.plugins import ILocalRolesPlugin
from Products.PlonePAS.interfaces import group as igroup

from plone.session.plugins.session import manage_addSessionPlugin

import logging
logger = logging.getLogger('PlonePAS setup')


def activatePluginInterfaces(portal, plugin, disable=[]):
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
        plone_pas.manage_addAutoGroup('auto_group', "Authenticated Users (Virtual Group)",
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
        addRecursiveGroupsPlugin(plone_pas, 'recursive_groups', "Recursive Groups Plugin")
        activatePluginInterfaces(portal, 'recursive_groups')
        logger.debug("Added Recursive Groups plugin.")


def setupAuthPlugins(portal, pas, plone_pas,
                     deactivate_basic_reset=True,
                     deactivate_cookie_challenge=False):
    uf = portal.acl_users
    logger.debug("Cookie plugin setup")

    login_path = 'login_form'
    logout_path = 'logged_out'
    cookie_name = '__ac'

    crumbler = getToolByName(portal, 'cookie_authentication', None)
    if crumbler is not None:
        login_path = crumbler.auto_login_page
        logout_path = crumbler.logout_page
        cookie_name = crumbler.auth_cookie

    found = uf.objectIds(['Extended Cookie Auth Helper'])
    if not found:
        plone_pas.manage_addExtendedCookieAuthHelper('credentials_cookie_auth',
                                                     cookie_name=cookie_name)
    logger.debug("Added Extended Cookie Auth Helper.")
    if deactivate_basic_reset:
        disable=['ICredentialsResetPlugin', 'ICredentialsUpdatePlugin']
    else:
        disable=[]
    activatePluginInterfaces(portal, 'credentials_cookie_auth',
            disable=disable)

    credentials_cookie_auth = uf._getOb('credentials_cookie_auth')
    if 'login_form' in credentials_cookie_auth:
        credentials_cookie_auth.manage_delObjects(ids=['login_form'])
        logger.debug("Removed default login_form from credentials cookie auth.")
    credentials_cookie_auth.cookie_name = cookie_name
    credentials_cookie_auth.login_path = login_path

    # remove cookie crumbler(s)
    if 'cookie_authentication' in portal:
        portal.manage_delObjects(['cookie_authentication'])
    logger.debug("Removed old Cookie Crumbler")

    found = uf.objectIds(['HTTP Basic Auth Helper'])
    if not found:
        pas.addHTTPBasicAuthHelper('credentials_basic_auth',
                               title="HTTP Basic Auth")
    logger.debug("Added Basic Auth Helper.")
    activatePluginInterfaces(portal, 'credentials_basic_auth')

    if deactivate_basic_reset:
        uf.plugins.deactivatePlugin(ICredentialsResetPlugin,
                                     'credentials_basic_auth')
    if deactivate_cookie_challenge:
        uf.plugins.deactivatePlugin(IChallengePlugin,
                                     'credentials_cookie_auth')


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
    plugins = uf['plugins']
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
        plugin.manage_updateProtocolMapping(mapping=config.DEFAULT_PROTO_MAPPING)
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
