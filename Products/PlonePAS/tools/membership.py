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

from sets import Set

from Globals import InitializeClass
from Products.PlonePAS.config import logger

# for createMemberArea...
from AccessControl import getSecurityManager, ClassSecurityInfo
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.MembershipTool import MembershipTool as BaseMembershipTool

try:
    # Plone 2.1
    from Products.CMFPlone.utils import utranslate as translate
    from Products.CMFPlone.utils import _createObjectByType
except ImportError:
    # Plone 2.0
    from Products.CMFPlone.PloneUtilities import translate
    from Products.CMFPlone.PloneUtilities import _createObjectByType
from Products.PlonePAS.utils import cleanId

class MembershipTool(BaseMembershipTool):
    """PAS-based customization of MembershipTool.

    Uses CMFPlone's as base.
    """

    meta_type = "PlonePAS Membership Tool"
    security = ClassSecurityInfo()

    user_search_keywords = ('name', 'exact_match')

    _properties = (getattr(BaseMembershipTool, '_properties', ()) +
                   ({'id': 'user_search_keywords',
                     'type': 'lines',
                     'mode': 'rw',
                     },))

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
        logger.debug('searchForMembers: started.')
        acl_users = self.acl_users
        md = self.portal_memberdata
        groups_tool = self.portal_groups

        if REQUEST is not None:
            dict = REQUEST
        else:
            dict = kw

        user_search = {}
        for key in self.user_search_keywords:
            value = dict.get(key, None)
            if value is None:
                continue
            user_search[key] = value

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

        uf_users = []
        members = []
        g_userids, g_members = [], []

        if groupname:
            logger.debug(
                'searchForMembers: searching groups '
                'for title|name=%r.' % groupname)
            groups = (groups_tool.searchForGroups(title=groupname) +
                      groups_tool.searchForGroups(name=groupname))

            for group in groups:
                for member in group.getGroupMembers():
                    if (member not in g_members and
                        not groups_tool.isGroup(member)):
                        g_members.append(member)
            g_userids = map(lambda x: x.getMemberId(), g_members)

        if groupname and not g_userids:
            logger.debug(
                'searchForMembers: searching for groupname '
                'found no users, immediate return.')
            return []

        if user_search:
            # We first find in MemberDataTool users whose _full_ name
            # match what we want.
            if name:
                logger.debug(
                    'searchForMembers: searching memberdata '
                    'for fullname=%r.' % name)
                lst = md.searchMemberDataContents('fullname', name)
                uf_users = [x['username'] for x in lst]

            logger.debug(
                'searchForMembers: searching PAS '
                'with arguments %r.' % user_search)
            # This will allow us to retrieve users by their id or name
            for user in acl_users.searchUsers(**user_search):
                uid = user['userid']
                uf_users.append(uid)

        if uf_users:
            names_checked = 1
            wrap = self.wrapUser
             # not getUser, we have userids here
            getUserById = acl_users.getUserById

            for userid in Set(uf_users):
                members.append(wrap(getUserById(userid)))

            if (not email and
                not roles and
                not last_login_time):
                logger.debug(
                    'searchForMembers: searching users '
                    'with no extra filter, immediate return.')
                return members

        elif groupname:
            members = g_members
            names_checked = 0

        else:
            # If the lists are not available, we just stupidly get the
            # members list. Only IUserIntrospection plugins participate
            # here.
            members = self.listMembers()
            names_checked = 0

        # Now perform individual checks on each user
        res = []
        portal = self.portal_url.getPortalObject()

        for member in members:
            # user = md.wrapUser(u)
            u = member.getUser()
            if not (member.getProperty('listed', False) or is_manager):
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
                last_login = member.getProperty('last_login_time',
                                                last_login_time)
                if last_login < last_login_time:
                    continue
            res.append(member)
        logger.debug('searchForMembers: finished.')
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
        if not self.getMemberareaCreationFlag():
            return None
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
            logger.debug('createMemberarea: members area does not exist.')
            return


        safe_member_id = cleanId(member_id)
        if hasattr(members, safe_member_id):
            # has already this member
            # XXX exception?
            logger.debug(
                'createMemberarea: member area '
                'for %r already exists.' % safe_member_id)
            return

        if not safe_member_id:
            # Could be one of two things:
            # - A Emergency User
            # - cleanId made a empty string out of member_id
            logger.debug(
                'createMemberarea: empty member id '
                '(%r, %r), skipping member area creation.' % (
                member_id, safe_member_id))
            return

        _createObjectByType('Folder', members, id=safe_member_id)

        # Get the user object from acl_users
        acl_users = self.__getPUS()
        # SdS: According to Leo, our MOTUId, we should use getUserById here.
        user = acl_users.getUserById(member_id)
        if user is not None:
            user = user.__of__(acl_users)
        else:
            user = getSecurityManager().getUser()
            # check that we do not do something wrong
            if user.getId() != member_id:
                raise NotImplementedError, \
                    'cannot get user for member area creation'

        # Get some translations
        # Before translation we must set right encodings in header to
        # make PTS happy
        putils = getToolByName(self, 'plone_utils')
        charset = putils.getSiteEncoding()

        self.REQUEST.RESPONSE.setHeader(
            'Content-Type', 'text/html;charset=%s' % charset)

        member_folder_title = translate(
            'plone', 'title_member_folder',
            {'member': member_id}, self,
            default = "%s's Home" % member_id)

        member_folder_description = translate(
            'plone', 'description_member_folder',
            {'member': member_id}, self,
            default = 'Home page area that contains the items created ' \
            'and collected by %s' % member_id)

        member_folder_index_html_title = translate(
            'plone', 'title_member_folder_index_html',
            {'member': member_id}, self,
            default = "Home page for %s" % member_id)

        personal_folder_title = translate(
            'plone', 'title_member_personal_folder',
            {'member': member_id}, self,
            default = "Personal Items for %s" % member_id)

        personal_folder_description = translate(
            'plone', 'description_member_personal_folder',
            {'member': member_id}, self,
            default = 'contains personal workarea items for %s' % member_id)

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

    def _getSafeMemberId(self, id=None):
        """Return a safe version of a member id.

        If no id is given return the id for the currently authenticated user.
        """

        if id is None:
            member = self.getAuthenticatedMember()
            if not hasattr(member, 'getMemberId'):
                return None
            id = member.getMemberId()

        return cleanId(id)


    security.declarePublic('getHomeFolder')
    def getHomeFolder(self, id=None, verifyPermission=0):
        """ Return a member's home folder object, or None.

        Specially instrumented for URL-quoted-member-id folder
        names.
        """
        safe_id = self._getSafeMemberId(id)
        return BaseMembershipTool.getHomeFolder(self, safe_id, verifyPermission)


    def getPersonalPortrait(self, id=None, verifyPermission=0):
        """Return a members personal portait.

        Modified from CMFPlone version to URL-quote the member id.
        """
        safe_id = self._getSafeMemberId(id)
        return BaseMembershipTool.getPersonalPortrait(self, safe_id, verifyPermission)


    def deletePersonalPortrait(self, id=None):
        """deletes the Portait of a member.

        Modified from CMFPlone version to URL-quote the member id.
        """
        safe_id = self._getSafeMemberId(id)
        return BaseMembershipTool.deletePersonalPortrait(self, safe_id)


    def changeMemberPortrait(self, portrait, id=None):
        """update the portait of a member.

        Modified from CMFPlone version to URL-quote the member id.
        """
        safe_id = self._getSafeMemberId(id)
        return BaseMembershipTool.changeMemberPortrait(self, portrait, safe_id)


InitializeClass(MembershipTool)

