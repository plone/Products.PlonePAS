"""
$Id: membership.py,v 1.2 2005/05/05 03:56:07 jccooper Exp $
"""
from Globals import InitializeClass

from Products.CMFPlone.MembershipTool import MembershipTool as BaseMembershipTool
from urllib import quote as url_quote

class MembershipTool(BaseMembershipTool):
    """PAS-based customization of MembershipTool. Uses CMFPlone's as base."""


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

        md_users = []
        uf_users = []
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

    #############
    ## sanitize home folders (we may get URL-illegal ids)

    def createMemberarea(self, member_id=None, minimal=0):
        """
        Create a member area for 'member_id' or the authenticated user.
        Specially instrumented to for URL-quoted-member-id folder names.
        """
        if not member_id:
            # member_id is optional (see CMFCore.interfaces.portal_membership:
            #     Create a member area for 'member_id' or authenticated user.)
            member = membership.getAuthenticatedMember()
            member_id = member.getId()
        member_id = url_quote(member_id, '')  # we provide the 'safe' param because want '/' encoded
        return BaseMembershipTool.createMemberarea(self, member_id, minimal)

    def getHomeFolder(self, id=None, verifyPermission=0):
        """ Return a member's home folder object, or None.
        Specially instrumented to for URL-quoted-member-id folder names.
        """
        if id is None:
            member = self.getAuthenticatedMember()
            if not hasattr(member, 'getMemberId'):
                return None
            id = member.getMemberId()
        id = url_quote(id, '')  # we provide the 'safe' param because want '/' encoded
        return BaseMembershipTool.getHomeFolder(self, id, verifyPermission)


InitializeClass(MembershipTool)
