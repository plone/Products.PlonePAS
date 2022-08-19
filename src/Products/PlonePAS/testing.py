from plone.app.contenttypes.testing import PLONE_APP_CONTENTTYPES_FIXTURE
from plone.app.testing import applyProfile
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PloneSandboxLayer
from plone.app.testing import TEST_USER_ID
from plone.testing import zope as zope_testing

import Products.PlonePAS


class ProductsPlonepasLayer(PloneSandboxLayer):

    defaultBases = (PLONE_APP_CONTENTTYPES_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        # Load any other ZCML that is required for your tests.
        # The z3c.autoinclude feature is disabled in the Plone fixture base
        # layer.
        self.loadZCML(package=Products.PlonePAS)
        zope_testing.installProduct(app, "Products.PlonePAS")

    def setUpPloneSite(self, portal):
        applyProfile(portal, "Products.PlonePAS:PlonePAS")
        # setRoles(portal, TEST_USER_ID, ['Manager'])
        from Products.CMFPlone.utils import _createObjectByType

        _createObjectByType("Folder", portal, id="Members")
        mtool = portal.portal_membership
        if not mtool.getMemberareaCreationFlag():
            mtool.setMemberareaCreationFlag()
        mtool.createMemberArea(TEST_USER_ID)
        if mtool.getMemberareaCreationFlag():
            mtool.setMemberareaCreationFlag()

        _createObjectByType("Folder", portal, id="folder")


PRODUCTS_PLONEPAS_FIXTURE = ProductsPlonepasLayer()


PRODUCTS_PLONEPAS_INTEGRATION_TESTING = IntegrationTesting(
    bases=(PRODUCTS_PLONEPAS_FIXTURE,),
    name="ProductsPlonepasLayer:IntegrationTesting",
)


PRODUCTS_PLONEPAS_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(PRODUCTS_PLONEPAS_FIXTURE,),
    name="ProductsPlonepasLayer:FunctionalTesting",
)
