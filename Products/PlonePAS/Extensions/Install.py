from StringIO import StringIO
from Products.CMFCore.utils import getToolByName
from Products.PlonePAS import config
from Products.Archetypes.Extensions.utils import install_subskin

from Acquisition import aq_base

def configurePlonePAS(portal, out):
    """Add the necessary objects to make a usable PAS instance"""
    pas = portal.acl_users
    pas.manage_addProduct['PluggableAuthService'].addCookieAuthHelper('cookie_auth', cookie_name='__ac')
    print >> out, "Added Cookie Auth Helper."
    pas.manage_addProduct['PluggableAuthService'].addZODBUserManager('zodb_users')
    print >> out, "Added ZODB User Manager."
    pas.manage_addProduct['PluggableAuthService'].addZODBRoleManager('role_mgr')
    print >> out, "Added ZODB Role Manager."
    pas.manage_addProduct['PluggableAuthService'].addZODBGroupManager('zodb_groups')
    print >> out, "Added ZODB Group Manager."
    pas.manage_addProduct['PluggableAuthService'].addLocalRolePlugin('local_roles')
    print >> out, "Added Local Role Plugin."
    pas.manage_addProduct['PluggableAuthService'].addScriptablePlugin('scriptables')
    print >> out, "Added Scriptable Plugin."


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
