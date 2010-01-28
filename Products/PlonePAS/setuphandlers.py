from Products.CMFCore.utils import getToolByName

from Products.PlonePAS.Extensions.Install import challenge_chooser_setup
from Products.PlonePAS.Extensions.Install import migrate_root_uf
from Products.PlonePAS.Extensions.Install import registerPluginTypes
from Products.PlonePAS.Extensions.Install import setupPlugins


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
        gtool.addGroup('Administrators', title='Administrators', roles=['Manager'])
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

    # TODO: This is highly questionable behaviour. Replacing the UF at the root.
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
