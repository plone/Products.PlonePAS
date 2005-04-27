"""
$Id: plonetool.py,v 1.1 2005/04/27 23:45:47 jccooper Exp $
"""
from Globals import InitializeClass

from Products.CMFPlone.PloneTool import PloneTool as BasePloneTool


class PloneTool(BasePloneTool):
    """PAS-based customization of PloneTool. Uses CMFPlone's as base."""

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
