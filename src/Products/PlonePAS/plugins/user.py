"""
ZODB based user manager with introspection and management interfaces.
"""
from AccessControl import ClassSecurityInfo
from AccessControl.class_init import InitializeClass
from AccessControl.Permissions import manage_users as ManageUsers
from App.special_dtml import DTMLFile
from AuthEncoding import AuthEncoding
from Products.PlonePAS.interfaces.capabilities import IDeleteCapability
from Products.PlonePAS.interfaces.capabilities import IPasswordSetCapability
from Products.PlonePAS.interfaces.plugins import IUserIntrospection
from Products.PlonePAS.interfaces.plugins import IUserManagement
from Products.PluggableAuthService.events import CredentialsUpdated
from Products.PluggableAuthService.plugins.ZODBUserManager import (
    ZODBUserManager as BasePlugin,
)
from Products.PluggableAuthService.utils import createViewName
from zope.event import notify
from zope.interface import implementer


manage_addUserManagerForm = DTMLFile("../zmi/UserManagerForm", globals())


def manage_addUserManager(dispatcher, id, title=None, REQUEST=None):
    """Add a UserManager to a Pluggable Auth Service."""

    pum = UserManager(id, title)
    dispatcher._setObject(pum.getId(), pum)

    if REQUEST is not None:
        REQUEST["RESPONSE"].redirect(
            "%s/manage_workspace"
            "?manage_tabs_message="
            "UserManager+added." % dispatcher.absolute_url()
        )


@implementer(
    IUserManagement, IUserIntrospection, IDeleteCapability, IPasswordSetCapability
)
class UserManager(BasePlugin):
    """PAS plugin for managing users. (adds write API)"""

    meta_type = "User Manager"
    security = ClassSecurityInfo()

    @security.protected(ManageUsers)
    def addUser(self, user_id, login_name, password):
        """Original ZODBUserManager.addUser, modified to check if
        incoming password is already encypted.

        This support clean migration from default user source.
        Should go into PAS.
        """
        if self._user_passwords.get(user_id) is not None:
            raise KeyError("Duplicate user ID: %s" % user_id)

        if self._login_to_userid.get(login_name) is not None:
            raise KeyError("Duplicate login name: %s" % login_name)

        if not AuthEncoding.is_encrypted(password):
            password = AuthEncoding.pw_encrypt(password)
        self._user_passwords[user_id] = password
        self._login_to_userid[login_name] = user_id
        self._userid_to_login[user_id] = login_name

        # enumerateUsers return value has changed
        view_name = createViewName("enumerateUsers")
        self.ZCacheable_invalidate(view_name=view_name)

    # User Management interface

    @security.private
    def doDeleteUser(self, userid):
        """Given a user id, delete that user"""
        return self.removeUser(userid)

    @security.private
    def doChangeUser(self, principal_id, password):
        """Change a user's password"""
        if self._user_passwords.get(principal_id) is None:
            raise RuntimeError("User does not exist: %s" % principal_id)
        self._user_passwords[principal_id] = AuthEncoding.pw_encrypt(password)
        notify(CredentialsUpdated(self.getUserById(principal_id), password))

    # implement interfaces IDeleteCapability, IPasswordSetCapability

    @security.public
    def allowDeletePrincipal(self, principal_id):
        """True iff this plugin can delete a certain user/group.
        This is true if this plugin manages the user.
        """
        if self._user_passwords.get(principal_id) is not None:
            return 1
        return 0

    @security.public
    def allowPasswordSet(self, principal_id):
        """True iff this plugin can set the password a certain user.
        This is true if this plugin manages the user.
        """
        return self.allowDeletePrincipal(principal_id)

    # User Introspection interface

    @security.protected(ManageUsers)
    def getUserIds(self):
        """
        Return a list of user ids
        """
        return self.listUserIds()

    @security.protected(ManageUsers)
    def getUserNames(self):
        """
        Return a list of usernames
        """
        return [x["login_name"] for x in self.listUserInfo()]

    @security.protected(ManageUsers)
    def getUsers(self):
        """
        Return a list of users
        """
        uf = self.acl_users
        return [uf.getUserById(x) for x in self.getUserIds()]


InitializeClass(UserManager)
