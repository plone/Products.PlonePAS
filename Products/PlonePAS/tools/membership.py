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

from Products.CMFPlone.MembershipTool import MembershipTool as BaseMembershipTool
from urllib import quote as url_quote
from urllib import unquote as url_unquote

# for createMemberArea...
from AccessControl import getSecurityManager, ClassSecurityInfo
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.PloneUtilities import _createObjectByType
from Products.CMFPlone.PloneUtilities import translate


class MembershipTool(BaseMembershipTool):
    """PAS-based customization of MembershipTool.

    Uses CMFPlone's as base.
    """

    meta_type = "PlonePAS Membership Tool"
    security = ClassSecurityInfo()

    security.declarePrivate('addMember')
    def addMember(self, id, password, roles, domains, properties=None):
        """Adds a new member to the user folder.

        Security checks will have already been performed.  Called by
        portal_registration.  This one specific to PAS. PAS ignores
        domains. Adding members with login_name also not yet
        supported.
        """
        acl_users = self.acl_users
        acl_users._doAddUser(id, password, roles, domains)

        if properties is not None:
            member = self.getMemberById(id)
            member.setMemberProperties(properties)


    security.declarePublic('searchForMembers')
    def searchForMembers(self, REQUEST=None, **kw):
        """Hacked up version of Plone searchForMembers.

        The following properties can be provided:
        - name
        - email
        - last_login_time
        - roles
        - groupname

        This is an 'AND' request.

        When it takes 'name' as keyword (or in REQUEST) and searches on
        Full name and id.

        Simple name searches are "fast".
        """
        acl_users = self.acl_users
        md = self.portal_memberdata
        groups_tool = self.portal_groups
        if REQUEST:
            dict = REQUEST
        else:
            dict = kw

        name = dict.get('name', None)
        email = dict.get('email', None)
        roles = dict.get('roles', None)
        last_login_time = dict.get('last_login_time', None)
        groupname = dict.get('groupname', '').strip()
        is_manager = self.checkPermission('Manage portal', self)

        if name:
            name = name.strip().lower()
        if not name:
            name = None
        if email:
            email = email.strip().lower()
        if not email:
            email = None

        md_users = []
        uf_users = []

        if name:
            # We first find in MemberDataTool users whose _full_ name
            # match what we want.
            lst = md.searchMemberDataContents('fullname', name)
            md_users = [ x['username'] for x in lst]

            # This will allow us to retrieve users by their id or name
            uf_users = acl_users.searchUsers(name=name)

            # PAS allows search to return dupes. We must winnow...
            uf_users_new = []
            for user in uf_users:
                if user not in uf_users_new:
                    uf_users_new.append(user)
            uf_users = uf_users_new

        members = []
        g_userids, g_members = [], []

        if groupname:
            groups = groups_tool.searchForGroups(title=groupname) + \
                     groups_tool.searchForGroups(name=groupname)

            for group in groups:
                for member in group.getGroupMembers():
                    if member not in g_members and not groups_tool.isGroup(member):
                        g_members.append(member)
            g_userids = map(lambda x: x.getMemberId(), g_members)
        if groupname and not g_userids:
            return []


        # build final list
        #if md_users is not None and uf_users is not None:   # original. I think this is broken.
                                                             # does anybody actually use this?
        if md_users or uf_users:
            wrap = self.wrapUser
            getUser = acl_users.getUser

            for userid in md_users:
                members.append(wrap(getUser(userid)))
            for user in uf_users:
                userid = user['userid']
                if userid in md_users:
                    continue             # Kill dupes
                members.append(wrap(getUser(userid)))

            if not email and \
                   not roles and \
                   not last_login_time:
                return members

        elif groupname:
            members = g_members
            names_checked = 0
        else:
            # If the lists are not available, we just stupidly get the members list
            # only IUserIntrospection plugins participate here.
            members = self.listMembers()
            names_checked = 0

        # Now perform individual checks on each user
        res = []
        portal = self.portal_url.getPortalObject()

        for member in members:
            #user = md.wrapUser(u)
            u = member.getUser()
            if not (member.listed or is_manager):
                continue
            if name and not names_checked:
                if (u.getUserName().lower().find(name) == -1 and
                    member.getProperty('fullname').lower().find(name) == -1):
                    continue
            if email:
                if member.getProperty('email').lower().find(email) == -1:
                    continue
            if roles:
                user_roles = member.getRoles()
                found = 0
                for r in roles:
                    if r in user_roles:
                        found = 1
                        break
                if not found:
                    continue
            if last_login_time:
                if member.last_login_time < last_login_time:
                    continue
            res.append(member)
        return res

    #############
    ## sanitize home folders (we may get URL-illegal ids)

    security.declarePublic('createMemberarea')
    def createMemberarea(self, member_id=None, minimal=0):
        """
        Create a member area for 'member_id' or the authenticated
        user, but don't assume that member_id is url-safe.

        Unfortunately, a pretty close copy of the (very large)
        original and only a few lines different.  Plone should
        probably do this.
        """
        catalog = getToolByName(self, 'portal_catalog')
        membership = getToolByName(self, 'portal_membership')
        members = self.getMembersFolder()

        if not member_id:
            # member_id is optional (see CMFCore.interfaces.portal_membership:
            #     Create a member area for 'member_id' or authenticated user.)
            member = membership.getAuthenticatedMember()
            member_id = member.getId()

        if hasattr(members, 'aq_explicit'):
            members=members.aq_explicit

        if members is None:
            # no members area
            # XXX exception?
            return


        safe_member_id = _cleanId(member_id)
        if hasattr(members, safe_member_id):
            # has already this member
            # XXX exception?
            return

        _createObjectByType('Folder', members, id=safe_member_id)

        # get the user object from acl_users
        # XXX what about portal_membership.getAuthenticatedMember()?
        acl_users = self.__getPUS()
        user = acl_users.getUser(member_id)
        if user is not None:
            user = user.__of__(acl_users)
        else:
            user= getSecurityManager().getUser()
            # check that we do not do something wrong
            if user.getId() != member_id:
                raise NotImplementedError, \
                    'cannot get user for member area creation'

        ## get some translations
        # before translation we must set right encodings in header to
        # make PTS happy
        properties = getToolByName(self, 'portal_properties')
        charset = properties.site_properties.getProperty('default_charset', 'utf-8')
        self.REQUEST.RESPONSE.setHeader('Content-Type', 'text/html;charset=%s' % charset)

        member_folder_title = translate(
            'plone', 'title_member_folder',
            {'member': safe_member_id}, self,
            default = "%s's Home" % safe_member_id)

        member_folder_description = translate(
            'plone', 'description_member_folder',
            {'member': safe_member_id}, self,
            default = 'Home page area that contains the items created ' \
            'and collected by %s' % safe_member_id)

        member_folder_index_html_title = translate(
            'plone', 'title_member_folder_index_html',
            {'member': safe_member_id}, self,
            default = "Home page for %s" % safe_member_id)

        personal_folder_title = translate(
            'plone', 'title_member_personal_folder',
            {'member': safe_member_id}, self,
            default = "Personal Items for %s" % safe_member_id)

        personal_folder_description = translate(
            'plone', 'description_member_personal_folder',
            {'member': safe_member_id}, self,
            default = 'contains personal workarea items for %s' % safe_member_id)

        ## Modify member folder
        member_folder = self.getHomeFolder(member_id)
        # Grant Ownership and Owner role to Member
        member_folder.changeOwnership(user)
        member_folder.__ac_local_roles__ = None
        member_folder.manage_setLocalRoles(member_id, ['Owner'])
        # set title and description (edit invokes reindexObject)
        member_folder.edit(title=member_folder_title,
                           description=member_folder_description)
        member_folder.reindexObject()

        ## Create personal folder for personal items
        _createObjectByType('Folder', member_folder, id=self.personal_id)
        personal = getattr(member_folder, self.personal_id)
        personal.edit(title=personal_folder_title,
                      description=personal_folder_description)
        # Grant Ownership and Owner role to Member
        personal.changeOwnership(user)
        personal.__ac_local_roles__ = None
        personal.manage_setLocalRoles(member_id, ['Owner'])
        # Don't add .personal folders to catalog
        catalog.unindexObject(personal)

        if minimal:
            # don't set up the index_html for unit tests to speed up tests
            return

        ## add homepage text
        # get the text from portal_skins automagically
        homepageText = getattr(self, 'homePageText', None)
        if homepageText:
            member_object = self.getMemberById(member_id)
            portal = getToolByName(self, 'portal_url')
            # call the page template
            content = homepageText(member=member_object, portal=portal).strip()
            _createObjectByType('Document', member_folder, id='index_html')
            hpt = getattr(member_folder, 'index_html')
            # edit title, text and format
            # XXX
            hpt.setTitle(member_folder_index_html_title)
            if hpt.meta_type == 'Document':
                # CMFDefault Document
                hpt.edit(text_format='structured-text', text=content)
            else:
                hpt.update(text=content)
            hpt.setFormat('structured-text')
            hpt.reindexObject()
            # Grant Ownership and Owner role to Member
            hpt.changeOwnership(user)
            hpt.__ac_local_roles__ = None
            hpt.manage_setLocalRoles(member_id, ['Owner'])

        ## Hook to allow doing other things after memberarea creation.
        notify_script = getattr(member_folder, 'notifyMemberAreaCreated', None)
        if notify_script is not None:
            notify_script()

     # deal with ridiculous API change in CMF
    security.declarePublic('createMemberArea')
    createMemberArea = createMemberarea

    security.declarePublic('getHomeFolder')
    def getHomeFolder(self, id=None, verifyPermission=0):
        """ Return a member's home folder object, or None.

        Specially instrumented to for URL-quoted-member-id folder
        names.
        """
        if id is None:
            member = self.getAuthenticatedMember()
            if not hasattr(member, 'getMemberId'):
                return None
            id = member.getMemberId()

        safe_id = _cleanId(id)
        return BaseMembershipTool.getHomeFolder(self, safe_id, verifyPermission)


InitializeClass(MembershipTool)

def _cleanId(id):
    """'url_quote' turns strange chars into '%xx', which is not a valid char
    for ObjectManager. Here we encode '%' into '-' (and '-' into '--' as escaping).
    De-clean is possible, but not quite as simple.
    Assumes that id can start with non-alpha(numeric), which is true.
    """
    __traceback_info__ = (id,)
    # note: we provide the 'safe' param to get '/' encoded
    return url_quote(id, '').replace('-','--').replace('%','-')

