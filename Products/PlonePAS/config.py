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

PROJECTNAME = 'PlonePAS'
GLOBALS = globals()

PAS_INSIDE_GRUF = True

DEFAULT_CHALLENGE_PROTOCOL = ['http']
DEFAULT_PROTO_MAPPING = {'WebDAV': DEFAULT_CHALLENGE_PROTOCOL,
                         'FTP': DEFAULT_CHALLENGE_PROTOCOL,
                         'XML-RPC': DEFAULT_CHALLENGE_PROTOCOL}

