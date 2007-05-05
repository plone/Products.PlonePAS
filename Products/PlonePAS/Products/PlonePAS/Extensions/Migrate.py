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
Minimalist GRUF Migration
"""
from StringIO import StringIO
from Install import install

def migrate(self):
    """
    """
    gruf = self.acl_users
    out = StringIO()

    log = install( self )
    out.write( log )

    pas = self.acl_users
    pas.manage_addProduct['PlonePAS'].manage_addGRUFBridge(
        "gruf_bridge"
        )

    bridge = pas.gruf_bridge
    bridge.manage_delObject(['acl_users'])
    bridge._setObject('acl_users', gruf)
    self.__allow_groups__ = pas


    return "GRUF Bridge Installed"
