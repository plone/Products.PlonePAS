"""
local roles blocking api, maintains compatibility with gruf from instance
space pov, moves api to plone tool (plone_utils)

$Id: plone.py,v 1.1 2005/02/04 23:23:30 k_vertigo Exp $
"""

from AccessControl import getSecurityManager, Permissions
from Products.CMFPlone import PloneTool

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

PloneTool.acquireLocalRoles = acquireLocalRoles
