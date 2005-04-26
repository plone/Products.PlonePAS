import os, sys
import unittest
from sets import Set
import traceback

if __name__ == '__main__':
    execfile(os.path.join(os.path.dirname(sys.argv[0]), 'framework.py'))

from Testing                 import ZopeTestCase
from Products.CMFCore.utils  import getToolByName
from Products.PloneTestCase import PloneTestCase
from PloneTestCase import PloneTestCase, setupPloneSite

##for product in ('PlonePAS',
##                ):
##    PloneTestCase.installProduct(product)
##del product

from Products.PluggableAuthService.interfaces.authservice import IPluggableAuthService

class BasicOpsTestCase(PloneTestCase):

    def afterSetUp(self):
        self.loginPortalOwner()
        self.acl_users = self.portal.acl_users

    def compareRoles(self, target, user, roles):
        """
        compareRoles(self, target, user, roles) => do not raise if user has exactly the specified roles.
        If target is None, test user roles (no local roles)
        """
        u = self.acl_users.getUser(user)
        if not u:
            raise RuntimeError, "compareRoles: Invalid user: '%s'" % user
        if target is None:
            actual_roles = filter(lambda x: x not in ('Authenticated', 'Anonymous', ''), list(u.getRoles()))
        else:
            actual_roles = filter(lambda x: x not in ('Authenticated', 'Anonymous', ''), list(u.getRolesInContext(target)))
        actual_roles.sort()
        wished_roles = list(roles)
        wished_roles.sort()
        if actual_roles == wished_roles:
            return 1
        raise RuntimeError, "User %s: Whished roles: %s BUT current roles: %s" % (user, wished_roles, actual_roles)

    def createUser(self, name="created_user", password="secret",
                   roles=[], groups=[], domains=()):
        self.acl_users.userFolderAddUser(
            name,
            password,
            roles = roles,
            groups = groups,
            domains = domains,
            )

    def test_installed(self):
        self.failUnless(IPluggableAuthService.isImplementedBy(self.acl_users))

    def test_add(self):
        self.createUser()
        self.failUnless(self.acl_users.getUser("created_user"))

    def test_edit(self):
        self.createUser()
        self.compareRoles(None, "created_user", [], )
        self.acl_users.userFolderEditUser(
            "created_user", # name 
            "secret2", # password
            roles = ["Member", ],
            groups = ["g1", ],
            domains = (),
            )
        self.compareRoles(None, "created_user", ['Member',], )

    def test_edit_userDefinedRole(self):
        self.portal._addRole('r1')
        self.createUser()
        self.compareRoles(None, "created_user", [], )
        self.acl_users.userFolderEditUser(
            "created_user", # name 
            "secret2", # password
            roles = ["r1", ],
            groups = ["g1", ],
            domains = (),
            )
        self.compareRoles(None, "created_user", ['r1',], )

    def test_del(self):
        self.createUser()
        self.failUnless(self.acl_users.getUser("created_user"))
        self.acl_users.userFolderDelUsers(['created_user', ])
        self.failIf(self.acl_users.getUser("created_user"))

    def test_search(self):
        self.createUser()
        mt = self.portal.portal_membership
        retlist = mt.searchForMembers(REQUEST=None, name="created_user")
        usernames = [user.getUserName() for user in retlist]
        self.failUnless("created_user" in usernames,
                        "'created_user' not in %s" % usernames)

    def test_getpw(self):
        # both pw reset functionality in control panel and "mail me my
        # pw" on the mail_password_form (accessible from the login
        # form) use MemberData.getPassword() to mail the password the
        # user already has. This is wrong, as some user sources don't
        # have the ability to recover a user password (think
        # /etc/passwd or /etc/shadow, for starters), but this is what Plone
        # does so here is a test
        self.createUser()
        mt = self.portal.portal_membership
        member = mt.getMemberById("created_user")
        self.assertEquals("secret", member.getPassword())

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(BasicOpsTestCase))
    return suite

if __name__ == '__main__':
    framework()
