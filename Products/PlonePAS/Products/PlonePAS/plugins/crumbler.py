##############################################################################
#
# PlonePAS - Adapt PluggableAuthService for use in Plone
# Copyright (C) 2005 Enfold Systems
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this
# distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
""" Class: CookieCrumblingPlugin

Acts as auth plugin, but injects cookie form credentials as HTTPBasicAuth.
This allows form logins to fall through to parent user folders.

"""
from Acquisition import aq_base
from AccessControl.SecurityInfo import ClassSecurityInfo
from Globals import InitializeClass, DTMLFile
from OFS.Folder import Folder

from Products.PluggableAuthService.utils import classImplements
from Products.PluggableAuthService.plugins.BasePlugin import BasePlugin
from Products.PluggableAuthService.interfaces.plugins import IExtractionPlugin

from Products.CMFCore.CookieCrumbler import manage_addCC

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

manage_addCookieCrumblingPluginForm = DTMLFile("../zmi/CookieCrumblingPluginForm", globals())

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

    security.declarePrivate('extractCredentials')
    def extractCredentials(self, request):
        """ Extract basic auth credentials from 'request'.
        """

        try:
            self._getCC().modifyRequest(request, request.RESPONSE)

        except Exception, e:
            import logging
            logger = logging.getLogger('Plone')
            logger.error("PlonePAS error: %s", e, exc_info=1)

        return {}

classImplements(CookieCrumblingPlugin,
                IExtractionPlugin)

InitializeClass(CookieCrumblingPlugin)
