"""
$Id$
"""

import os, sys
import unittest

if __name__ == '__main__':
    execfile(os.path.join(os.path.dirname(sys.argv[0]), 'framework.py'))

from Testing import ZopeTestCase
from Products.PloneTestCase import PloneTestCase
del PloneTestCase

from Products.CMFCore.utils import getToolByName
from Products.PlonePAS.tests.PloneTestCase import PloneTestCase

from Products.PluggableAuthService.interfaces.authservice \
     import IPluggableAuthService

class IntrospectorMethodWrapper:
    count = 0

    def __init__(self, klass, name):
        self.klass = klass
        self.name = name
        self.origname = "__introspected_%s__" % name
        method = self.genWrapper()
        old_method = getattr(klass, name)
        setattr(klass, self.origname, old_method)
        setattr(klass, name, method)

    def _getOriginalMethod(self, instance):
        return getattr(instance, self.origname)

    def genWrapper(self):
        introspector = self
        def wrapper(self, *args, **kw):
            result = introspector._getOriginalMethod(self)(*args, **kw)
            return introspector.introspect(self, args, kw, result)
        return wrapper

    def introspect(self, instance, args, kw, result):
        return result

    def __del__(self):
        setattr(self.klass, self.name, self.klass.__counted_method__)
        del self.klass.__counted_method__

class CollectResultsWrapper(IntrospectorMethodWrapper):

    def __init__(self, klass, name):
        IntrospectorMethodWrapper.__init__(self, klass, name)
        self.results = []

    def introspect(self, instance, args, kw, result):
        #self.results.append((args, kw, result))
        self.results.append(result)
        return result

class BasicOpsTestCase(PloneTestCase):

    def afterSetUp(self):
        self.loginPortalOwner()
        self.acl_users = self.portal.acl_users
        self.acl_users.ZCacheable_setManagerId('RAMCache')

    def createUser(self, name="created_user", password="secret",
                   roles=[], groups=[], domains=()):
        self.acl_users.userFolderAddUser(
            name,
            password,
            roles = roles,
            groups = groups,
            domains = domains,
            )

    def test_getUser_is_cached(self):
        # monitor the caching method
        collector = CollectResultsWrapper(self.acl_users.aq_base.__class__,
                                          'ZCacheable_get')
        
        self.assertEquals(collector.results, [])
        # creating a user already populates the cache, but it also looks
        # the user up, so we must have got only misses so far
        self.createUser()
        self.assertEquals(collector.results, [None] * len(collector.results))
        # the cache must be populated by now, the user we're getting back
        # must've come from the cache
        u = self.acl_users.getUser("created_user")
        self.assertEquals(id(collector.results[-1]), id(u.aq_base),
                          "%r is not %r" % (collector.results[-1],
                                            u.aq_base))

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(BasicOpsTestCase))
    return suite

if __name__ == '__main__':
    framework()
