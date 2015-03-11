# -*- coding: utf-8 -*-
from Acquisition import aq_inner
from Products.CMFCore.utils import getToolByName
from Products.Five import BrowserView
from Products.PlonePAS.interfaces.browser import IPASInfoView
from Products.PluggableAuthService.interfaces.plugins import IExtractionPlugin
from Products.PluggableAuthService.interfaces.plugins \
    import ILoginPasswordExtractionPlugin
from plone.memoize.instance import memoize
from zope.interface import implementer


@implementer(IPASInfoView)
class PASInfoView(BrowserView):

    def checkExtractorForInterface(self, interface):
        acl = getToolByName(aq_inner(self.context), "acl_users")
        plugins = acl.plugins.listPlugins(IExtractionPlugin)

        for plugin in plugins:
            if interface.providedBy(plugin[1]):
                return True

        return False

    @memoize
    def hasLoginPasswordExtractor(self):
        return self.checkExtractorForInterface(ILoginPasswordExtractionPlugin)

    @memoize
    def hasOpenIDExtractor(self):
        try:
            from plone.openid.interfaces import IOpenIdExtractionPlugin
        except ImportError:
            return False

        return self.checkExtractorForInterface(IOpenIdExtractionPlugin)

    def hasOpenIDdExtractor(self):
        # BBB Keeping method name with typo for backwards compatibility.
        return self.hasOpenIDExtractor()
