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
$Id: plonetool.py,v 1.5 2005/06/29 17:27:46 jccooper Exp $
"""
from Globals import InitializeClass

from Products.CMFPlone.PloneTool import PloneTool as BasePloneTool


class PloneTool(BasePloneTool):
    """PAS-based customization of PloneTool. Uses CMFPlone's as base."""

    meta_type = "PlonePAS Utilities Tool"

    def acquireLocalRoles(self, folder, status):
        """
        Enable or disable local role acquisition on the specified folder.
        If status is true, roles will not be acquired. if false or None (default )
        they will be.
        """
        # Perform security check on destination folder
        if not getSecurityManager().checkPermission(Permissions.change_permissions, folder):
            raise Unauthorized(name = "acquireLocalRoles")

        status = not not status
        status = status or None
        folder.__ac_local_roles_block__ = status

        return self._acquireLocalRoles(folder, status)

    def isLocalRoleAcquired(self, folder):
        """Return true if the specified folder allows local role acquisition.
        """
        if getattr(folder, '__ac_local_roles_block__', None):
            return 0
        return 1

InitializeClass(PloneTool)
