"""
$Id: plonetool.py,v 1.2 2005/05/06 18:40:07 jccooper Exp $
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

InitializeClass(PloneTool)
