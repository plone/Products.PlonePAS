#
# PlonePASTestCase
#

# $Id: PlonePASTestCase.py 18188 2006-01-19 20:48:45Z wichert $

from Testing import ZopeTestCase
from Products.PloneTestCase import PloneTestCase
PloneTestCase.setupPloneSite()

from Products.PloneTestCase.PloneTestCase import FunctionalTestCase

# Stub test case just in case we need custom stuff at some point
class PlonePASTestCase(PloneTestCase.PloneTestCase):
    '''TestCase for Plone testing'''
