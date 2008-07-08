##############################################################################
#
# PlonePAS - Adapt PluggableAuthService for use in Plone
# Copyright (C) 2005 Enfold Systems, Kapil Thangavelu, et al
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
"""
"""

from zope.deprecation import deprecated

from Globals import InitializeClass
from Products.CMFPlone.PloneTool import PloneTool as BasePloneTool

class PloneTool(BasePloneTool):
    """PAS-based customization of PloneTool. Uses CMFPlone's as base."""

    meta_type = "PlonePAS Utilities Tool"


deprecated('PloneTool', 'Please use the standard CMFPlone PloneTool. '
           'PlonePAS.tools.plonetool will be removed in Plone(PAS) 4.0')

InitializeClass(PloneTool)
