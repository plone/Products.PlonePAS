from zope.interface import implements
from plone.memoize.instance import memoize
from Products.CMFPlone.utils import BrowserView, context
from Products.PlonePAS.interfaces.browser import IPASInfoView
from Products.PluggableAuthService.interfaces.plugins \
                import IExtractionPlugin, ILoginPasswordExtractionPlugin
from Products.CMFCore.utils import getToolByName


class PASInfoView(BrowserView):
    implements(IPASInfoView)

    def checkExtractorForInterface(self, interface):
        acl=getToolByName(context(self), "acl_users")
        plugins=acl.plugins.listPlugins(IExtractionPlugin)

        for plugin in plugins:
            if interface.providedBy(plugin[1]):
                return True

        return False

    @memoize
    def hasLoginPasswordExtractor(self):
        return self.checkExtractorForInterface(ILoginPasswordExtractionPlugin)


    @memoize
    def hasOpenIDdExtractor(self):
        try:
            from plone.openid.interfaces import IOpenIdExtractionPlugin
        except ImportError:
            return False

        return self.checkExtractorForInterface(IOpenIdExtractionPlugin)
