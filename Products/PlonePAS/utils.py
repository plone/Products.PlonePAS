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

from Products.CMFCore.utils import getToolByName
from urllib import quote as url_quote
from urllib import unquote as url_unquote

def unique(iterable):
    d = {}
    for i in iterable:
        d[i] = None
    return d.keys()

def getCharset(context):
    """Returns the site default charset, or utf-8.
    """
    properties = getToolByName(context, "portal_properties")
    site_properties = getattr(properties, 'site_properties', None)
    if site_properties is not None:
        return site_properties.getProperty('default_charset')
    return 'utf-8'

def cleanId(id):
    """'url_quote' turns strange chars into '%xx', which is not a valid char
    for ObjectManager. Here we encode '%' into '-' (and '-' into '--' as escaping).
    De-clean is possible; see 'decleanId'.
    Assumes that id can start with non-alpha(numeric), which is true.
    """
    __traceback_info__ = (id,)
    if id:
        # note: we provide the 'safe' param to get '/' encoded
        return url_quote(id, '').replace('-','--').replace('%','-')
    return ''

def decleanId(id):
   """Reverse cleanId."""
   if id:
       id = id.replace('--', '\x00').replace('-', '%').replace('\x00', '-')
       return url_unquote(id)
   return ''
