"""
local roles blocking api, maintains compatibility with gruf from instance
space pov, moves api to plone tool (plone_utils).

patches for memberdata to allow for delegation to pas property providers,
falling back to default impl else.

$Id: plone.py,v 1.3 2005/02/24 15:13:31 k_vertigo Exp $
"""

from AccessControl import getSecurityManager, Permissions
from Products.CMFPlone.PloneTool import PloneTool
from Products.CMFCore.MemberDataTool import MemberData
from Products.CMFCore.utils import getToolByName
from Products.PluggableAuthService.interfaces.authservice import IPluggableAuthService
from Products.PlonePAS.interfaces.propertysheets import IMutablePropertySheet

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

    if IPluggableAuthService.isImplementedBy(self.acl_users):
        user = self.getUser()
        sheets = user.getOrderedPropertySheets()

        # xxx track values set to defer to default impl
        # property routing
        for k,v in mapping.items():
            for sheet in sheets:
                if sheet.hasProperty( k ):
                    if IMutablePropertySheet.isImplementedBy(sheet):
                        sheet.setProperty( k, v )
                    else:
                        raise RuntimeError("mutable property provider shadowed by read only provider")
        self.notifyModified()
        return

    # defer to base impl in absence of pas
    return self.baseSetProperties( mapping )

MemberData.baseSetProperties__roles__ = ()
MemberData.baseSetProperties = MemberData.setMemberProperties
MemberData.setMemberProperties = setMemberProperties

def getProperty(self, id):
    if PluggableAuthService.isImplementedBy( self.acl_users ):
        user = self.getUser()
        for sheet in user.getOrderedPropertySheets():
            if sheet.hasProperty( id ):
                return sheet.getProperty( id )
    return self.baseGetProperty( id )

MemberData.baseGetProperty__roles__ = ()
MemberData.baseGetProperty = MemberData.getProperty
MemberData.getProperty = getProperty


def searchFulltextForMembers(self, s):
    """
    """
    acl_users = getToolByName( self, 'acl_users')
    return acl_users.searchUsers( name=s, exact_match=False)
