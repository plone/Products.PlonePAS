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
    pas = portal.acl_users
    pas.manage_addProduct['PluggableAuthService'].addCookieAuthHelper('cookie_auth', cookie_name='__ac')
    print >> out, "Added Cookie Auth Helper."
    activatePluginInterfaces(portal, 'cookie_auth', out)
    
    pas.manage_addProduct['PluggableAuthService'].addZODBUserManager('zodb_users')
    print >> out, "Added ZODB User Manager."
    activatePluginInterfaces(portal, 'zodb_users', out)
    
    pas.manage_addProduct['PluggableAuthService'].addZODBRoleManager('role_mgr')
    print >> out, "Added ZODB Role Manager."
    activatePluginInterfaces(portal, 'role_mgr', out)
    
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
