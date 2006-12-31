"""
PlonePAS setup handlers.
"""

from StringIO import StringIO

from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.migrations.v2_5.two51_two52 import \
    setLoginFormInCookieAuth

from Products.PlonePAS.Extensions.Install import challenge_chooser_setup
from Products.PlonePAS.Extensions.Install import migrate_root_uf
from Products.PlonePAS.Extensions.Install import registerPluginTypes
from Products.PlonePAS.Extensions.Install import setupPlugins


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


def setupGroups(p):
    """
    Create Plone's default set of groups.
    """
    gtool = getToolByName(p, 'portal_groups')
    existing = gtool.listGroupIds()
    if 'Administrators' not in existing:
        gtool.addGroup('Administrators', roles=['Manager'])
    if 'Reviewers' not in existing:
        gtool.addGroup('Reviewers', roles=['Reviewer'])


def installPAS(portal):
    out = StringIO()
    
    # Add user folder
    portal.manage_addProduct['PluggableAuthService'].addPluggableAuthService()

    # Configure Challenge Chooser plugin if available
    challenge_chooser_setup(portal, out)

    # A bunch of general configuration settings
    registerPluginTypes(portal.acl_users)
    setupPlugins(portal, out)

    # TODO: This is highly questionable behaviour. Replacing the UF at the root.
    migrate_root_uf(portal, out)


def setupPlonePAS(context):
    """
    Setup PlonePAS step.
    """
    # Only run step if a flag file is present (e.g. not an extension profile)
    if context.readDataFile('plone-pas.txt') is None:
        return
    out = []
    site = context.getSite()
    installPAS(site)
    addRolesToPlugIn(site)
    setupGroups(site)

    setLoginFormInCookieAuth(site, out)
