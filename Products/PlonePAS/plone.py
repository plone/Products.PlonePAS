"""
local roles blocking api, maintains compatibility with gruf from instance
space pov, moves api to plone tool (plone_utils).

patches for memberdata to allow for delegation to pas property providers,
falling back to default impl else.

$Id: plone.py,v 1.6 2005/04/20 23:45:24 jccooper Exp $
"""

from AccessControl import getSecurityManager, Permissions
from Products.CMFPlone.PloneTool import PloneTool
from Products.CMFPlone.MemberDataTool import MemberData, MemberDataTool
from Products.CMFPlone.MembershipTool import MembershipTool
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


def getProperty(self, id, default=None):
    if IPluggableAuthService.isImplementedBy(self.acl_users):
        user = self.getUser()
        for sheet in user.getOrderedPropertySheets():
            if sheet.hasProperty( id ):
                return sheet.getProperty( id )
    return self.baseGetProperty( id )

MemberData.baseGetProperty__roles__ = ()
MemberData.baseGetProperty = MemberData.getProperty
MemberData.getProperty = getProperty


def searchFulltextForMembers(self, s):
    """PAS-specific search for members by id, email, full name.
    """
    acl_users = getToolByName( self, 'acl_users')
    return acl_users.searchUsers( name=s, exact_match=False)
    # I don't think this is right: we need to return Members

MemberDataTool.baseSearchFulltextForMembers = MemberDataTool.searchFulltextForMembers
MemberDataTool.searchFulltextForMembers = searchFulltextForMembers


def searchForMembers(self, REQUEST=None, **kw):
    """Hacked up version of Plone searchForMembers. Only takes 'name' as keyword
    (or in REQUEST) and searches on Full name and id.
    """
    acl_users = self.acl_users
    md = self.portal_memberdata
    groups_tool = self.portal_groups
    if REQUEST:
        dict = REQUEST
    else:
        dict = kw

    name = dict.get('name', None)
    if name:
        name = name.strip().lower()

    is_manager = self.checkPermission('Manage portal', self)

    md_users = None
    uf_users = None
    if name:
        # We first find in MemberDataTool users whose _full_ name match what we want.
        lst = md.searchMemberDataContents('fullname', name)
        md_users = [ x['username'] for x in lst]

        # This will allow us to retreive users by their _id_ (not name).
        uf_users = acl_users.searchUsers(name=name)

    # build final list
    members = []
    wrap = self.wrapUser
    getUser = acl_users.getUser

    for userid in md_users:
        members.append(wrap(getUser(userid)))
    for user in uf_users:
        userid = user['userid']
        if userid in md_users:
            continue             # Kill dupes
        members.append(wrap(getUser(userid)))
    
    return members

MembershipTool.baseSearchForMembers = MembershipTool.searchForMembers
MembershipTool.searchForMembers = searchForMembers


def addMember(self, id, password, roles, domains, properties=None):
    """Adds a new member to the user folder.  Security checks will have
    already been performed.  Called by portal_registration.
    This one specific to PAS. PAS ignores domains. Adding members with login_name
    also not yet supported.
    """
    acl_users = self.acl_users
    acl_users._doAddUser(id, password, roles, domains)

    if properties is not None:
        member = self.getMemberById(id)
        member.setMemberProperties(properties)

MembershipTool.baseAddMember = MembershipTool.addMember
MembershipTool.addMember = addMember