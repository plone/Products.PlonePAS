"""
local roles blocking api, maintains compatibility with gruf from instance
space pov, moves api to plone tool (plone_utils)

$Id: plone.py,v 1.2 2005/02/19 20:03:48 k_vertigo Exp $
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


def setMemberProperties( self, mapping):
        # Sets the properties given in the MemberDataTool.
        tool = self.getTool()
        for id in tool.propertyIds():
            if mapping.has_key(id):
                if not self.__class__.__dict__.has_key(id):
                    value = mapping[id]
                    if type(value)==type(''):
                        proptype = tool.getPropertyType(id) or 'string'
                        if type_converters.has_key(proptype):
                            value = type_converters[proptype](value)
                    setattr(self, id, value)
        # Hopefully we can later make notifyModified() implicit.
        self.notifyModified()


def getProperty(self, id):
    pass
