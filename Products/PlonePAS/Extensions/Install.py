from StringIO import StringIO
from Products.CMFCore.utils import getToolByName
from Products.PlonePAS import config
from Products.Archetypes.Extensions.utils import install_subskin

from Acquisition import aq_base

def activatePluginInterfaces(portal, plugin, out):
    pas = portal.acl_users
    plugin_obj = pas[plugin]

    interfaces = plugin_obj.listInterfaces()

    activatable = []

    for info in plugin_obj.plugins.listPluginTypeInfo():
        interface = info['interface']
        interface_name = info['id']
        if plugin_obj.testImplements(interface):
            activatable.append(interface_name)
            print >> out, "  Activating: " + info['title']
    plugin_obj.manage_activateInterfaces(activatable)
    print >> out, plugin + " activated."

def configurePlonePAS(portal, out):
    """Add the necessary objects to make a usable PAS instance"""
    setupPlugins( portal )
    setupRoles( portal )

def setupRoles( portal ):
    rmanager = portal.acl_users.role_manager
    rmanager.addRole('Member', title="portal member")
    rmanager.addRole('Reviewer', title="content reviewer")

def setupPlugins( portal ):
    pas = portal.acl_users
    pas.manage_addProduct['PluggableAuthService'].addCookieAuthHelper('cookie_auth', cookie_name='__ac')
    pas.cookie_auth.manage_activateInterfaces( pas.cookie_auth.listInterfaces() )
    activatePluginInterfaces(portal, 'cookie_auth', out)    
    print >> out, "Added Cookie Auth Helper."

    
    pas.manage_addProduct['PluggableAuthService'].addZODBUserManager('zodb_users')
    pas.zodb_users.manage_activateInterfaces( pas.zodb_users.listInterfaces() )
    activatePluginInterfaces(portal, 'zodb_users', out)    
    print >> out, "Added ZODB User Manager."

    
    pas.manage_addProduct['PluggableAuthService'].addZODBRoleManager('role_manager')
    pas.role_mgr.manage_activateInterfaces( pas.role_mgr.listInterfaces() )
    activatePluginInterfaces(portal, 'role_mgr', out)
    print >> out, "Added ZODB Role Manager."

    pas.manage_addProduct['PluggableAuthService'].addZODBGroupManager('zodb_groups')
    pas.zodb_groups.manage_activateInterfaces( pas.zodb_groups.listInterfaces() )
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
