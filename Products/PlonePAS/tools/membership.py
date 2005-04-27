"""
$Id: membership.py,v 1.1 2005/04/27 23:45:47 jccooper Exp $
"""
from Globals import InitializeClass

from Products.CMFPlone.MembershipTool import MembershipTool as BaseMembershipTool


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

InitializeClass(MembershipTool)
