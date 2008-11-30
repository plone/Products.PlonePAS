from Testing import ZopeTestCase
from Products.PloneTestCase import PloneTestCase
PloneTestCase.setupPloneSite()

from Products.PloneTestCase.PloneTestCase import FunctionalTestCase

# Stub test case just in case we need custom stuff at some point
class PlonePASTestCase(PloneTestCase.PloneTestCase):
    '''TestCase for Plone testing'''
