# gruf specific hacks to pas, to make it play well in gruf

import logging

from Products.PluggableAuthService.PluggableAuthService import \
          PluggableAuthService, _SWALLOWABLE_PLUGIN_EXCEPTIONS
from Products.PluggableAuthService.interfaces.plugins \
     import IAuthenticationPlugin
from Products.PlonePAS.interfaces.group import IGroupManagement
from Products.PlonePAS.interfaces.plugins import IUserIntrospection

from Products.CMFCore.utils import getToolByName

logger = logging.getLogger('PlonePAS')

def authenticate(self, name, password, request):
    """See AccessControl.User.BasicUserFolder.authenticate
    
    Products.PluggableAuthService.PluggableAuthService does not provide this 
    method, BasicUserFolder documents it as "Private UserFolder object 
    interface". GRUF does provide the method, so not marked as private.
    """

    plugins = self.plugins

    try:
        authenticators = plugins.listPlugins(IAuthenticationPlugin)
    except _SWALLOWABLE_PLUGIN_EXCEPTIONS:
        logger.info('PluggableAuthService: Plugin listing error', exc_info=1)
        authenticators = ()

    credentials = {'login': name,
                   'password': password}

    user_id = None

    for authenticator_id, auth in authenticators:
        try:
            uid_and_name = auth.authenticateCredentials(credentials)
            if uid_and_name is not None:
                user_id, name = uid_and_name
                break
        except _SWALLOWABLE_PLUGIN_EXCEPTIONS:
            logger.info('PluggableAuthService: AuthenticationPlugin %s error',
                    authenticator_id, exc_info=1)
            continue

    if not user_id:
        return

    return self._findUser(plugins, user_id, name, request)

PluggableAuthService.authenticate = authenticate
PluggableAuthService.authenticate__roles__ = ()


#################################
# compat code galore
def userSetGroups(self, id, groupnames):
    plugins = self.plugins
    gtool = getToolByName(self, "portal_groups")

    member = self.getUser(id)
    groupnameset = set(groupnames)

    # remove absent groups
    groups = set(gtool.getGroupsForPrincipal(member))
    rmgroups = groups - groupnameset
    for gid in rmgroups:
        try:
            gtool.removePrincipalFromGroup(id, gid)
        except KeyError:
            # We could hit a group which does not allow user removal, such as
            # created by our AutoGroup plugin.
            pass

    # add groups
    try:
        groupmanagers = plugins.listPlugins(IGroupManagement)
    except _SWALLOWABLE_PLUGIN_EXCEPTIONS:
        logger.info('PluggableAuthService: Plugin listing error', exc_info=1)
        groupmanagers = ()

    for group in groupnames:
        for gm_id, gm in groupmanagers:
            try:
                if gm.addPrincipalToGroup(id, group):
                    break
            except _SWALLOWABLE_PLUGIN_EXCEPTIONS:
                logger.info('PluggableAuthService: GroupManagement %s error',
                            gm_id, exc_info=1)

PluggableAuthService.userSetGroups = userSetGroups

#################################
# monkies for the diehard introspection.. all these should die, imho - kt

def getUserIds(self):
    plugins = self.plugins

    try:
        introspectors = plugins.listPlugins(IUserIntrospection)
    except _SWALLOWABLE_PLUGIN_EXCEPTIONS:
        logger.info('PluggableAuthService: Plugin listing error', exc_info=1)
        introspectors = ()

    results = []
    for introspector_id, introspector in introspectors:
        try:
            results.extend(introspector.getUserIds())
        except _SWALLOWABLE_PLUGIN_EXCEPTIONS:
            logger.info('PluggableAuthService: UserIntrospection %s error',
                    introspector_id, exc_info=1)

    return results


def getUserNames(self):
    plugins = self.plugins

    try:
        introspectors = plugins.listPlugins(IUserIntrospection)
    except _SWALLOWABLE_PLUGIN_EXCEPTIONS:
        logger.info('PluggableAuthService: Plugin listing error', exc_info=1)
        introspectors = ()

    results = []
    for introspector_id, introspector in introspectors:
        try:
            results.extend(introspector.getUserNames())
        except _SWALLOWABLE_PLUGIN_EXCEPTIONS:
            logger.info('PluggableAuthService: UserIntroSpection plugin %s error',
                    introspector_id, exc_info=1)

    return results

PluggableAuthService.getUserIds = getUserIds
PluggableAuthService.getUserNames = getUserNames
