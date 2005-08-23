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
$Id$
"""

from Products.CMFCore.utils import getToolByName

def unique(iterable):
    d = {}
    for i in iterable:
        d[i] = None
    return d.keys()

def getCharset(context):
    """Returns the site default charset, or utf-8.
    """
    properties = getToolByName(context, 'portal_properties', None)
    if properties is not None:
        site_properties = getToolByName(properties, 'site_properties', None)
        if site_properties is not None:
            return site_properties.getProperty('default_charset')
    return 'utf-8'
