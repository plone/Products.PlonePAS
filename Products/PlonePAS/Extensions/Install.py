from StringIO import StringIO
from Products.CMFCore.utils import getToolByName
from Products.PlonePAS import config
from Products.Archetypes.Extensions.utils import install_subskin
from Products.PluginRegistry.PluginRegistry import PluginRegistry
from Products.PluggableAuthService.PluggableAuthService import _PLUGIN_TYPE_INFO
from Products.PlonePAS.interfaces.plugins import IUserDeleterPlugin

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
                print >> out, "  Activating: " + info['title']
    except AttributeError:
        print >> out, "It looks like you have a non-PAS acl_users folder. "
        print >> out, "Please remove it before installing PlonePAS."
    plugin_obj.manage_activateInterfaces(activatable)
    print >> out, plugin + " activated."

def configurePlonePAS(portal, out):
    """Add the necessary objects to make a usable PAS instance"""
    setupPlugins( portal, out )
#    setupRoles( portal )

def setupRoles( portal ):
    rmanager = portal.acl_users.role_manager
    rmanager.addRole('Member', title="portal member")
    rmanager.addRole('Reviewer', title="content reviewer")

def setupPlugins( portal, out ):
    pas = portal.acl_users
    pas.plugins._plugin_type_info[IUserDeleterPlugin] = \
        { 'id': 'IUserDeleterPlugin'
        , 'title': 'user_deleter'
        , 'description': "User Deleter plugins allow the Pluggable Auth " +\
                         "Service to delete users."
        }
    pas.plugins._plugin_types.append(IUserDeleterPlugin)

    pas.manage_addProduct['PluggableAuthService'].addCookieAuthHelper('cookie_auth', cookie_name='__ac')
    activatePluginInterfaces(portal, 'cookie_auth', out)
    print >> out, "Added Cookie Auth Helper."

    pas.manage_addProduct['PlonePAS'].addPloneUserManager('plone_users')
    activatePluginInterfaces(portal, 'plone_users', out)
    print >> out, "Added Plone User Manager."

    pas.manage_addProduct['PluggableAuthService'].addZODBRoleManager('role_manager')
    activatePluginInterfaces(portal, 'role_manager', out)
    print >> out, "Added ZODB Role Manager."

    pas.manage_addProduct['PluggableAuthService'].addZODBGroupManager('zodb_groups')
    print >> out, "Added ZODB Group Manager."
    activatePluginInterfaces(portal, 'zodb_groups', out)


def install(self):
    out = StringIO()
    portal = getToolByName(self, 'portal_url').getPortalObject()

    install_subskin(self, out, config.GLOBALS)
    print >> out, "Installed skins."

    if not hasattr(aq_base(portal), 'acl_users'):
        portal.manage_addProduct['PluggableAuthService'].addPluggableAuthService()

    configurePlonePAS(portal, out)


    print >> out, "Successfully installed %s." % config.PROJECTNAME
    return out.getvalue()
