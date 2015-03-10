# -*- coding: utf-8 -*-
""" Class: CookieCrumblingPlugin

Acts as auth plugin, but injects cookie form credentials as HTTPBasicAuth.
This allows form logins to fall through to parent user folders.

"""
from AccessControl.SecurityInfo import ClassSecurityInfo
from Acquisition import aq_base
from App.class_init import InitializeClass
from App.special_dtml import DTMLFile
from OFS.Folder import Folder
from Products.CMFCore.CookieCrumbler import manage_addCC
from Products.PluggableAuthService.interfaces.plugins import IExtractionPlugin
from Products.PluggableAuthService.plugins.BasePlugin import BasePlugin
from zope.interface import implementer
import logging

logger = logging.getLogger('PlonePAS')

CC_ID = 'cookie_auth'


def manage_addCookieCrumblingPlugin(self, id, title='',
                                    RESPONSE=None, **kw):
    """
    Create an instance of a cookie crumbling plugin.
    """
    self = self.this()

    o = CookieCrumblingPlugin(id, title, **kw)
    self._setObject(o.getId(), o)
    o = getattr(aq_base(self), id)

    manage_addCC(o, CC_ID)

    if RESPONSE is not None:
        RESPONSE.redirect('manage_workspace')

manage_addCookieCrumblingPluginForm = \
    DTMLFile("../zmi/CookieCrumblingPluginForm", globals())


@implementer(IExtractionPlugin)
class CookieCrumblingPlugin(Folder, BasePlugin):
    """Multi-plugin for injecting HTTP Basic Authentication
    credentials from form credentials.
    """
    meta_type = 'Cookie Crumbling Plugin'

    security = ClassSecurityInfo()

    def __init__(self, id, title=None):
        self._setId(id)
        self.title = title

    def _getCC(self):
        return getattr(aq_base(self), CC_ID, None)

    @security.private
    def extractCredentials(self, request):
        """ Extract basic auth credentials from 'request'.
        """

        try:
            self._getCC().modifyRequest(request, request.RESPONSE)

        except Exception, e:
            logger.error("PlonePAS error: %s", e, exc_info=1)

        return {}

InitializeClass(CookieCrumblingPlugin)
