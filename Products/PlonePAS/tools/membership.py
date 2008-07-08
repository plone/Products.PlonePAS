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
"""

import logging
from DateTime import DateTime

from Globals import InitializeClass

from Products.CMFCore.utils import getToolByName

# for createMemberArea...
from AccessControl import getSecurityManager, ClassSecurityInfo

from Products.CMFPlone.MembershipTool import MembershipTool as BaseMembershipTool

from Products.CMFPlone.utils import _createObjectByType
from Products.PlonePAS.utils import cleanId

from zope.deprecation import deprecate

logger = logging.getLogger('Plone')

class MembershipTool(BaseMembershipTool):
    """PAS-based customization of MembershipTool.

    Uses CMFPlone's as base.
    """

    meta_type = "PlonePAS Membership Tool"
    toolicon = 'tool.gif'
    security = ClassSecurityInfo()

    user_search_keywords = ('login', 'fullname', 'email', 'exact_match',
                            'sort_by', 'max_results')

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
    @deprecate("portal_membership.searchForMembers is deprecated and will "
               "be removed in Plone 4.0. Use PAS searchUsers instead")
    def searchForMembers(self, REQUEST=None, **kw):
        """Hacked up version of Plone searchForMembers.

        The following properties can be provided:
        - name
        - email
        - last_login_time
        - before_specified_time
        - roles (any role will cause a match)
        - groupname

        This is an 'AND' request.

        When it takes 'name' as keyword (or in REQUEST) it  searches on
        Full name and id.

        Simple name searches are "fast".
        """
        logger.debug('searchForMembers: started.')

        acl_users = getToolByName(self, "acl_users")
        md = getToolByName(self, "portal_memberdata")
        groups_tool = getToolByName(self, "portal_groups")

        if REQUEST is not None:
            searchmap = REQUEST
        else:
            searchmap = kw

        # While the parameter is called name it is actually used to search a
        # users name, which is stored in the fullname property. We need to fix
        # that here so the right name is used when calling into PAS plugins.
        if 'name' in searchmap:
            searchmap['fullname'] = searchmap['name']
            del searchmap['name']

        user_search = dict([ x for x in searchmap.items() 
                                if x[0] in self.user_search_keywords and x[1]])

        fullname = searchmap.get('fullname', None)
        email = searchmap.get('email', None)
        roles = searchmap.get('roles', None)
        last_login_time = searchmap.get('last_login_time', None)
        before_specified_time = searchmap.get('before_specified_time', None)
        groupname = searchmap.get('groupname', '').strip()
        is_manager = self.checkPermission('Manage portal', self)

        if fullname:
            fullname = fullname.strip().lower()
        if not fullname:
            fullname = None
        if email:
            email = email.strip().lower()
        if not email:
            email = None

        uf_users = []

        logger.debug(
            'searchForMembers: searching PAS '
            'with arguments %r.' % user_search)
        for user in acl_users.searchUsers(**user_search):
            uid = user['userid']
            uf_users.append(uid)

        if not uf_users:
            return []

        wrap = self.wrapUser
        getUserById = acl_users.getUserById

        members = [ getUserById(userid) for userid in set(uf_users)]
        members = [ member for member in members if member is not None ]

        if (not email and
            not fullname and
            not roles and
            not groupname and
            not last_login_time):
            logger.debug(
                'searchForMembers: searching users '
                'with no extra filter, immediate return.')
            return members


        # Now perform individual checks on each user
        res = []
        portal = getToolByName(self, 'portal_url').getPortalObject()

        for member in members:
            if groupname and groupname not in member.getGroupIds():
                continue

            if not (member.getProperty('listed', False) or is_manager):
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
                last_login = member.getProperty('last_login_time', '')

                if isinstance(last_login, basestring):
                    # value is a string when member hasn't yet logged in
                   last_login = DateTime(last_login or '2000/01/01')
                   
                if before_specified_time:
                    if last_login >= last_login_time:
                        continue
                elif last_login < last_login_time:
                    continue

            res.append(member)

        logger.debug('searchForMembers: finished.')
        return res

    #############
    ## sanitize home folders (we may get URL-illegal ids)

    security.declarePublic('createMemberarea')
    def createMemberarea(self, member_id=None, minimal=True):
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
            logger.debug('createMemberarea: members area does not exist.')
            return

        safe_member_id = cleanId(member_id)
        if hasattr(members, safe_member_id):
            # has already this member
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

        _createObjectByType(self.memberarea_type, members, id=safe_member_id)

        # Get the user object from acl_users
        acl_users = self.__getPUS()
        user = acl_users.getUserById(member_id)
        if user is not None:
            user = user.__of__(acl_users)
        else:
            user = getSecurityManager().getUser()
            # check that we do not do something wrong
            if user.getId() != member_id:
                raise NotImplementedError, \
                    'cannot get user for member area creation'

        member_object = self.getMemberById(member_id)

        ## Modify member folder
        member_folder = self.getHomeFolder(member_id)
        # Grant Ownership and Owner role to Member
        member_folder.changeOwnership(user)
        member_folder.__ac_local_roles__ = None
        member_folder.manage_setLocalRoles(member_id, ['Owner'])
        # We use ATCT now use the mutators
        fullname = member_object.getProperty('fullname')
        member_folder.setTitle(fullname or member_id)
        member_folder.reindexObject()

        if not minimal:
            ## add homepage text
            # get the text from portal_skins automagically
            homepageText = getattr(self, 'homePageText', None)
            if homepageText:
                portal = getToolByName(self, "portal_url").getPortalObject()
                # call the page template
                content = homepageText(member=member_object, portal=portal).strip()
                _createObjectByType('Document', member_folder, id='index_html')
                hpt = getattr(member_folder, 'index_html')
                # edit title, text and format
                hpt.setTitle(fullname or member_id)
                if hpt.meta_type == 'Document':
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

