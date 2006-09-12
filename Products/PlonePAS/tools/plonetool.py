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
from Globals import InitializeClass

from Products.CMFPlone.PloneTool import PloneTool as BasePloneTool
from Products.CMFCore import permissions as CMFCorePermissions
from Products.CMFCore.utils import getToolByName
from AccessControl import Unauthorized

class PloneTool(BasePloneTool):
    """PAS-based customization of PloneTool. Uses CMFPlone's as base."""

    meta_type = "PlonePAS Utilities Tool"

    def acquireLocalRoles(self, obj, status=1):
        """
        Enable or disable local role acquisition on the specified folder.
        If 'status' is 1, roles will not be acquired.
        If 0 they will not be.
        """
        mt = getToolByName(self, 'portal_membership')
        if not mt.checkPermission(CMFCorePermissions.ModifyPortalContent, obj):
            raise Unauthorized

        # Set local role status...
        # set the variable (or unset it if it's defined)
        if not status:
            obj.__ac_local_roles_block__ = 1
        else:
            if getattr(obj, '__ac_local_roles_block__', None):
                obj.__ac_local_roles_block__ = None

        # Reindex the whole stuff.
        obj.reindexObjectSecurity()

    def isLocalRoleAcquired(self, folder):
        """Return true if the specified folder allows local role acquisition.
        """
        if getattr(folder, '__ac_local_roles_block__', None):
            return 0
        return 1

InitializeClass(PloneTool)
