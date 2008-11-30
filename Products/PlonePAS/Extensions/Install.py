from StringIO import StringIO

from Products.CMFCore.utils import getToolByName

from Products.PluggableAuthService.interfaces.authservice \
        import IPluggableAuthService
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

from plone.session.plugins.session import manage_addSessionPlugin


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


def setupTools(portal, out):
    print >> out, "\nTools:"


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


def addPAS(portal, out):
    print >> out, " - Adding PAS user folder"
    portal.manage_addProduct['PluggableAuthService'].addPluggableAuthService()


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
         import _PLUGIN_TYPE_INFO

    pas = getToolByName(self, 'acl_users')
    if not IPluggableAuthService.providedBy(pas):
        print >> out, 'PAS UF not found, skipping PAS fixup'
        return

    plugins = pas['plugins']

    plugin_types = list(set(plugins._plugin_types))
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

    # Fix possible missing PAS plugins registration.
    pas_fixup(self, out)

    # Register PAS Plugin Types
    registerPluginTypes(uf)

    if not EXISTING_UF:
        addPAS(portal, out)

    # Configure Challenge Chooser plugin if available
    challenge_chooser_setup(self, out)

    configurePlonePAS(portal, out)

    setupTools(portal, out)

    # We need to do this, as we cannot inherit users from a non-PAS folder
    migrate_root_uf(self, out)

    print >> out, "\nSuccessfully installed %s." % config.PROJECTNAME
    return out.getvalue()
