from Products.PloneTestCase import ptc

from Products.PlonePAS.tests.layer import PlonePASLayer

ptc.setupPloneSite()


class TestCase(ptc.PloneTestCase):
    '''TestCase for PlonePAS'''

    layer = PlonePASLayer


class FunctionalTestCase(ptc.FunctionalTestCase):
    '''TestCase for PlonePAS'''

    layer = PlonePASLayer

