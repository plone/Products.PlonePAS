from warnings import warn
import logging
from cStringIO import StringIO

import transaction
from zope import event
from zope.component import getUtility
from zope.interface import implements
from zope.site.hooks import getSite

from DateTime import DateTime
from App.class_init import InitializeClass
from App.Dialogs import MessageDialog
from App.special_dtml import DTMLFile
from OFS.Image import Image
from Persistence import PersistentMapping

from AccessControl import ClassSecurityInfo
from AccessControl import getSecurityManager
from AccessControl import Unauthorized
from AccessControl.SecurityManagement import noSecurityManager
from AccessControl.requestmethod import postonly
from AccessControl.User import nobody
from Acquisition import aq_base
from Acquisition import aq_get
from Acquisition import aq_inner
from Acquisition import aq_parent
from zExceptions import BadRequest
from ZODB.POSException import ConflictError

from Products.CMFCore.interfaces import ISiteRoot
from Products.CMFCore.permissions import ChangeLocalRoles
from Products.CMFCore.permissions import ManagePortal
from Products.CMFCore.permissions import ManageUsers
from Products.CMFCore.permissions import SetOwnProperties
from Products.CMFCore.permissions import SetOwnPassword
from Products.CMFCore.permissions import View
from Products.CMFCore.permissions import ListPortalMembers
from Products.CMFCore.utils import getToolByName
from Products.CMFCore.utils import registerToolInterface

from Products.PlonePAS.events import UserLoggedInEvent
from Products.PlonePAS.events import UserInitialLoginInEvent
from Products.PlonePAS.events import UserLoggedOutEvent
from Products.PlonePAS.interfaces.membership import IMembershipTool
from Products.PlonePAS.utils import cleanId
from Products.PlonePAS.utils import scale_image

default_portrait = 'defaultUser.png'
logger = logging.getLogger('PlonePAS')


class MembershipTool(object):
    """PAS-based customization of MembershipTool.
    """

    implements(IMembershipTool)

    personal_id = '.personal'
    portrait_id = 'MyPortrait'
    default_portrait = 'defaultUser.gif'
    memberarea_type = 'Folder'
    membersfolder_id = 'Members'
    memberareaCreationFlag = False
    security = ClassSecurityInfo()

    user_search_keywords = ('login', 'fullname', 'email', 'exact_match',
                            'sort_by', 'max_results')

    _properties = (({'id': 'user_search_keywords',
                     'type': 'lines',
                     'mode': 'rw',
                     },))

    manage_options=( ({ 'label' : 'Configuration'
                     , 'action' : 'manage_mapRoles'
                     },) +
                   ( { 'label' : 'Overview'
                     , 'action' : 'manage_overview'
                     },) +
                   ( { 'label': 'Portraits'
                     , 'action': 'manage_portrait_fix'},))

    security.declareProtected(ManagePortal, 'manage_mapRoles')
    manage_mapRoles = DTMLFile('../zmi/membershipRolemapping', globals())

    security.declareProtected(ManagePortal, 'manage_portrait_fix')
    manage_portrait_fix = DTMLFile('../zmi/portrait_fix', globals())

    @property
    def acl_users(self):
        return getToolByName(getSite(), 'acl_users')

    @security.protected(ManagePortal)
    def manage_setMemberAreaType(self, type_name, REQUEST=None):
        """ ZMI method to set the home folder type by its type name.
        """
        self.setMemberAreaType(type_name)
        if REQUEST is not None:
            REQUEST['RESPONSE'].redirect(self.absolute_url()
                    + '/manage_mapRoles'
                    + '?manage_tabs_message=Member+area+type+changed.')

    @security.protected(ManagePortal)
    def manage_setMembersFolderById(self, id, REQUEST=None):
        """ ZMI method to set the members folder object by its id.
        """
        self.setMembersFolderById(id)
        if REQUEST is not None:
            REQUEST['RESPONSE'].redirect(self.absolute_url()
                    + '/manage_mapRoles'
                    + '?manage_tabs_message=Members+folder+id+changed.')

    @security.protected(ManagePortal)
    def setMemberAreaType(self, type_name):
        """ Sets the portal type to use for new home folders.
        """
        # No check for folderish since someone somewhere may actually want
        # members to have objects instead of folders as home "directory".
        self.memberarea_type = str(type_name).strip()

    @security.protected(ManagePortal)
    def setMembersFolderById(self, id=''):
        """ Set the members folder object by its id.
        """
        self.membersfolder_id = id.strip()

    @security.public
    def getMembersFolder(self):
        """ Get the members folder object.
        """
        site = getSite()
        members = getattr(site, self.membersfolder_id, None)
        return members

    @security.private
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

    @security.protected(ListPortalMembers)
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

        Simple name searches are "fast".
        """
        logger.debug('searchForMembers: started.')

        acl_users = getToolByName(getSite(), "acl_users")

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

        user_search = dict([x for x in searchmap.items()
                               if x[0] in self.user_search_keywords and x[1]])

        fullname = searchmap.get('fullname', None)
        email = searchmap.get('email', None)
        roles = searchmap.get('roles', None)
        last_login_time = searchmap.get('last_login_time', None)
        before_specified_time = searchmap.get('before_specified_time', None)
        groupname = searchmap.get('groupname', '').strip()

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

        getUserById = acl_users.getUserById

        def dedupe(seq):
            # Thanks http://www.peterbe.com/plog/uniqifiers-benchmark
            seen = set()
            seen_add = seen.add
            # nice trick! set.add() does always return None
            return [x for x in seq if x not in seen and not seen_add(x)]

        uf_users = dedupe(uf_users)
        members = [getUserById(userid) for userid in uf_users]
        members = [member for member in members if member is not None]

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

        for member in members:
            if groupname and groupname not in member.getGroupIds():
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

    @security.protected(ManagePortal)
    def getMemberareaCreationFlag(self):
        """
        Returns the flag indicating whether the membership tool
        will create a member area if an authenticated user from
        an underlying user folder logs in first without going
        through the join process
        """
        return self.memberareaCreationFlag

    @security.protected(ManagePortal)
    def setMemberareaCreationFlag(self):
        """
        sets the flag indicating whether the membership tool
        will create a member area if an authenticated user from
        an underlying user folder logs in first without going
        through the join process
        """
        if not hasattr(self, 'memberareaCreationFlag'):
            self.memberareaCreationFlag = 0

        if self.memberareaCreationFlag == 0:
            self.memberareaCreationFlag = 1
        else:
            self.memberareaCreationFlag = 0

        return MessageDialog(
               title='Member area creation flag changed',
               message='Member area creation flag has been updated',
               action='manage_mapRoles')

    @security.public
    def createMemberArea(self, member_id=None, minimal=None):
        """
        Create a member area for 'member_id' or the authenticated
        user, but don't assume that member_id is url-safe.
        """
        if not self.getMemberareaCreationFlag():
            return None
        membership = getUtility(IMembershipTool)
        members = self.getMembersFolder()

        if not member_id:
            # member_id is optional (see CMFCore.interfaces.portal_membership:
            #     Create a member area for 'member_id' or authenticated user.)
            member = membership.getAuthenticatedMember()
            member_id = member.getId()

        if hasattr(members, 'aq_explicit'):
            members = members.aq_explicit

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

        # Create member area without security checks
        typesTool = getToolByName(members, 'portal_types')
        fti = typesTool.getTypeInfo(self.memberarea_type)
        member_folder = fti._constructInstance(members, safe_member_id)

        # Get the user object from acl_users
        acl_users = getToolByName(getSite(), "acl_users")
        user = acl_users.getUserById(member_id)
        if user is not None:
            user = user.__of__(acl_users)
        else:
            user = getSecurityManager().getUser()
            # check that we do not do something wrong
            if user.getId() != member_id:
                raise NotImplementedError(
                        'cannot get user for member area creation')

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

        ## Hook to allow doing other things after memberarea creation.
        notify_script = getattr(member_folder, 'notifyMemberAreaCreated', None)
        if notify_script is not None:
            notify_script()

    @security.protected(ManageUsers)
    @postonly
    def deleteMemberArea(self, member_id, REQUEST=None):
        """ Delete member area of member specified by member_id.
        """
        members = self.getMembersFolder()
        if not members:
            return 0
        if hasattr(aq_base(members), member_id):
            members.manage_delObjects(member_id)
            return 1
        else:
            return 0

    @security.public
    def isAnonymousUser(self):
        '''
        Returns 1 if the user is not logged in.
        '''
        u = getSecurityManager().getUser()
        if u is None or u.getUserName() == 'Anonymous User':
            return 1
        return 0

    @security.public
    def checkPermission(self, permissionName, object, subobjectName=None):
        '''
        Checks whether the current user has the given permission on
        the given object or subobject.
        '''
        if subobjectName is not None:
            object = getattr(object, subobjectName)
        return getSecurityManager().checkPermission(permissionName, object)

    @security.public
    def credentialsChanged(self, password, REQUEST=None):
        '''
        Notifies the authentication mechanism that this user has changed
        passwords.  This can be used to update the authentication cookie.
        Note that this call should *not* cause any change at all to user
        databases.
        '''
        # XXX: this method violates the rules for tools/utilities:
        # it depends on self.REQUEST
        if REQUEST is None:
            REQUEST = getSite().REQUEST
            warn("credentialsChanged should be called with 'REQUEST' as "
                 "second argument. The BBB code will be removed in CMF 2.3.",
                 DeprecationWarning, stacklevel=2)

        if not self.isAnonymousUser():
            user = getSecurityManager().getUser()
            name = user.getUserName()
            # this really does need to be the user name, and not the user id,
            # because we're dealing with authentication credentials
            p = getattr(REQUEST, '_credentials_changed_path', None)
            if p is not None:
                # Use an interface provided by CookieCrumbler.
                change = self.restrictedTraverse(p)
                change(user, name, password)

    @security.protected(ManageUsers)
    def getMemberById(self, id):
        '''
        Returns the given member.
        '''
        user = self._huntUser(id, self)
        if user is not None:
            user = self.wrapUser(user)
        return user

    @security.public
    def getMemberInfo(self, memberId=None):
        # Return 'harmless' Memberinfo of any member, such as Full name,
        # Location, etc
        if not memberId:
            member = self.getAuthenticatedMember()
        else:
            member = self.getMemberById(memberId)

        if member is None:
            return None

        memberinfo = {'fullname': member.getProperty('fullname'),
                      'description': member.getProperty('description'),
                      'location': member.getProperty('location'),
                      'language': member.getProperty('language'),
                      'home_page': member.getProperty('home_page'),
                      'username': member.getUserName(),
                      'has_email': bool(member.getProperty('email')),
                     }

        return memberinfo

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

    @security.public
    def getHomeFolder(self, id=None, verifyPermission=0):
        """ Return a member's home folder object, or None.

        Specially instrumented for URL-quoted-member-id folder
        names.
        """
        safe_id = self._getSafeMemberId(id)
        if safe_id is None:
            member = self.getAuthenticatedMember()
            if not hasattr(member, 'getMemberId'):
                return None
            safe_id = member.getMemberId()
        members = self.getMembersFolder()
        if members:
            try:
                folder = members._getOb(safe_id)
                if verifyPermission and not getSecurityManager().checkPermission(View, folder):
                    # Don't return the folder if the user can't get to it.
                    return None
                return folder
            # KeyError added to deal with btree member folders
            except (AttributeError, KeyError, TypeError):
                pass
        return None

    def getHomeUrl(self, id=None, verifyPermission=0):
        """ Return the URL to a member's home folder, or None.
        """
        home = self.getHomeFolder(id, verifyPermission)
        if home is not None:
            return home.absolute_url()
        else:
            return None

    def _huntUserFolder(self, member_id, context):
        """Find userfolder containing user in the hierarchy
           starting from context
        """
        uf = context.acl_users
        while uf is not None:
            user = uf.getUserById(member_id)
            if user is not None:
                return uf
            container = aq_parent(aq_inner(uf))
            parent = aq_parent(aq_inner(container))
            uf = getattr(parent, 'acl_users', None)
        return None

    def _huntUser(self, member_id, context):
        """Find user in the hierarchy of userfolders
           starting from context
        """
        uf = self._huntUserFolder(member_id, context)
        if uf is not None:
            return uf.getUserById(member_id)

    def __getPUS(self):
        """ Retrieve the nearest user folder
        """
        warn('__getPUS is deprecated and will be removed in CMF 2.4, '
             'please acquire "acl_users" instead.', DeprecationWarning,
             stacklevel=2)
        return self.acl_users

    @security.protected(ListPortalMembers)
    def searchMembers(self, search_param, search_term):
        """ Search the membership """
        # XXX: this method violates the rules for tools/utilities:
        # it depends on a non-utility tool
        md = getToolByName(getSite(), 'portal_memberdata')

        return md.searchMemberData(search_param, search_term)

    @security.protected(View)
    @postonly
    def setLocalRoles(self, obj, member_ids, member_role, reindex=1,
                      REQUEST=None):
        """ Add local roles on an item.
        """
        if (getSecurityManager().checkPermission(ChangeLocalRoles, obj)
             and member_role in self.getCandidateLocalRoles(obj)):
            for member_id in member_ids:
                roles = list(obj.get_local_roles_for_userid(userid=member_id))

                if member_role not in roles:
                    roles.append(member_role)
                    obj.manage_setLocalRoles(member_id, roles)

        if reindex and hasattr(aq_base(obj), 'reindexObjectSecurity'):
            obj.reindexObjectSecurity()

    @security.protected(View)
    @postonly
    def deleteLocalRoles(self, obj, member_ids, reindex=1, recursive=0,
                         REQUEST=None):
        """ Delete local roles of specified members.
        """
        if getSecurityManager().checkPermission(ChangeLocalRoles, obj):
            for member_id in member_ids:
                if obj.get_local_roles_for_userid(userid=member_id):
                    obj.manage_delLocalRoles(userids=member_ids)
                    break

        if recursive and hasattr(aq_base(obj), 'contentValues'):
            for subobj in obj.contentValues():
                self.deleteLocalRoles(subobj, member_ids, 0, 1)

        if reindex and hasattr(aq_base(obj), 'reindexObjectSecurity'):
            # reindexObjectSecurity is always recursive
            obj.reindexObjectSecurity()

    @security.protected(ManageUsers)
    @postonly
    def deleteMembers(self, member_ids, delete_memberareas=1,
                      delete_localroles=1, REQUEST=None):
        """ Delete members specified by member_ids.
        """
        # XXX: this method violates the rules for tools/utilities:
        # it depends on a non-utility tool

        # Delete members in acl_users.
        acl_users = self.acl_users
        if getSecurityManager().checkPermission(ManageUsers, acl_users):
            if isinstance(member_ids, basestring):
                member_ids = (member_ids,)
            member_ids = list(member_ids)
            for member_id in member_ids[:]:
                if not acl_users.getUserById(member_id, None):
                    member_ids.remove(member_id)
            try:
                acl_users.userFolderDelUsers(member_ids)
            except (AttributeError, NotImplementedError):
                raise NotImplementedError('The underlying User Folder '
                                         'doesn\'t support deleting members.')
        else:
            raise Unauthorized('You need the \'Manage users\' '
                                 'permission for the underlying User Folder.')

        # Delete member data in portal_memberdata.
        mdtool = getToolByName(getSite(), 'portal_memberdata', None)
        if mdtool is not None:
            for member_id in member_ids:
                mdtool.deleteMemberData(member_id)

        # Delete members' home folders including all content items.
        if delete_memberareas:
            for member_id in member_ids:
                self.deleteMemberArea(member_id)

        # Delete members' local roles.
        if delete_localroles:
            self.deleteLocalRoles(getUtility(ISiteRoot), member_ids,
                                   reindex=1, recursive=1)

        return tuple(member_ids)

    @security.public
    def getPersonalFolder(self, member_id=None):
        """
        returns the Personal Item folder for a member
        if no Personal Folder exists will return None
        """
        home = self.getHomeFolder(member_id)
        personal = None
        if home:
            personal = getattr(home, self.personal_id, None)
        return personal

    @security.public
    def getPersonalPortrait(self, id=None, verifyPermission=0):
        """Return a members personal portait.

        Modified from CMFPlone version to URL-quote the member id.
        """
        if not id:
            id = self.getAuthenticatedMember().getId()
        safe_id = self._getSafeMemberId(id)
        membertool = getToolByName(getSite(), 'portal_memberdata')
        portrait = membertool._getPortrait(safe_id)
        if isinstance(portrait, str):
            portrait = None
        if portrait is not None:
            if verifyPermission and not getSecurityManager().checkPermission('View', portrait):
                # Don't return the portrait if the user can't get to it
                portrait = None
        if portrait is None:
            portal = getToolByName(getSite(), 'portal_url').getPortalObject()
            portrait = getattr(portal, default_portrait, None)

        return portrait

    @security.protected(SetOwnProperties)
    def deletePersonalPortrait(self, id=None):
        """deletes the Portait of a member.
        """
        authenticated_id = self.getAuthenticatedMember().getId()
        if not id:
            id = authenticated_id
        safe_id = self._getSafeMemberId(id)
        if id != authenticated_id and not getSecurityManager().checkPermission(
                ManageUsers, getSite()):
            raise Unauthorized

        membertool = getToolByName(getSite(), 'portal_memberdata')
        return membertool._deletePortrait(safe_id)

    @security.protected(SetOwnProperties)
    def changeMemberPortrait(self, portrait, id=None):
        """update the portait of a member.

        We URL-quote the member id if needed.

        Note that this method might be called by an anonymous user who
        is getting registered.  This method will then be called from
        plone.app.users and this is fine.  When called from restricted
        python code or with a curl command by a hacker, the
        declareProtected line will kick in and prevent use of this
        method.
        """
        authenticated_id = self.getAuthenticatedMember().getId()
        if not id:
            id = authenticated_id
        safe_id = self._getSafeMemberId(id)
        if authenticated_id and id != authenticated_id:
            # Only Managers can change portraits of others.
            if not getSecurityManager().checkPermission(ManageUsers, getSite()):
                raise Unauthorized
        if portrait and portrait.filename:
            scaled, mimetype = scale_image(portrait)
            portrait = Image(id=safe_id, file=scaled, title='')
            membertool = getToolByName(getSite(), 'portal_memberdata')
            membertool._setPortrait(portrait, safe_id)

    @security.protected(ManageUsers)
    def listMembers(self):
        '''Gets the list of all members.
        THIS METHOD MIGHT BE VERY EXPENSIVE ON LARGE USER FOLDERS AND MUST
        BE USED WITH CARE! We plan to restrict its use in the future (ie.
        force large requests to use searchForMembers instead of listMembers,
        so that it will not be possible anymore to have a method returning
        several hundred of users :)
        '''
        return map(self.wrapUser, self.acl_users.getUsers())

    @security.protected(ManageUsers)
    def listMemberIds(self):
        '''Lists the ids of all members.  This may eventually be
        replaced with a set of methods for querying pieces of the
        list rather than the entire list at once.
        '''
        return self.acl_users.getUserIds()

    @security.protected(SetOwnPassword)
    def testCurrentPassword(self, password):
        """ test to see if password is current """
        REQUEST = getattr(self, 'REQUEST', {})
        member = self.getAuthenticatedMember()
        acl_users = self._findUsersAclHome(member.getUserId())
        if not acl_users:
            return 0
        return acl_users.authenticate(member.getUserName(), password, REQUEST)

    def _findUsersAclHome(self, userid):
        portal = getToolByName(getSite(), 'portal_url').getPortalObject()
        acl_users = portal.acl_users
        parent = acl_users
        while parent:
            if acl_users.aq_explicit.getUserById(userid, None) is not None:
                break
            parent = aq_parent(aq_inner(parent)).aq_parent
            acl_users = getattr(parent, 'acl_users')
        if parent:
            return acl_users
        else:
            return None

    @security.protected(SetOwnPassword)
    def setPassword(self, password, domains=None, REQUEST=None):
        '''Allows the authenticated member to set his/her own password.
        '''
        registration = getToolByName(getSite(), 'portal_registration', None)
        if not self.isAnonymousUser():
            member = self.getAuthenticatedMember()
            #self.acl_users
            acl_users = self._findUsersAclHome(member.getUserId())
            if not acl_users:
                # should not possibly ever happen
                raise BadRequest('did not find current user in any '
                                 'user folder')
            if registration:
                failMessage = registration.testPasswordValidity(password)
                if failMessage is not None:
                    raise BadRequest(failMessage)

            if domains is None:
                domains = []
            user = acl_users.getUserById(member.getUserId(), None)
            # we must change the users password trough grufs changepassword
            # to keep her  group settings
            if hasattr(user, 'changePassword'):
                user.changePassword(password)
            else:
                acl_users._doChangeUser(member.getUserId(), password,
                                        member.getRoles(), domains)
            if REQUEST is None:
                REQUEST = aq_get(self, 'REQUEST', None)
            self.credentialsChanged(password, REQUEST=REQUEST)
        else:
            raise BadRequest('Not logged in.')
    setPassword = postonly(setPassword)

    @security.public
    def getAuthenticatedMember(self):
        '''
        Returns the currently authenticated member object
        or the Anonymous User.  Never returns None.
        '''
        u = getSecurityManager().getUser()
        if u is None:
            u = nobody
        return self.wrapUser(u)

    security.declarePrivate('wrapUser')
    def wrapUser(self, u, wrap_anon=0):
        """ Set up the correct acquisition wrappers for a user object.

        Provides an opportunity for a portal_memberdata tool to retrieve and
        store member data independently of the user object.
        """
        # XXX: this method violates the rules for tools/utilities:
        # it depends on a non-utility tool
        b = getattr(u, 'aq_base', None)
        if b is None:
            # u isn't wrapped at all.  Wrap it in self.acl_users.
            b = u
            u = u.__of__(self.acl_users)
        if (b is nobody and not wrap_anon) or hasattr(b, 'getMemberId'):
            # This user is either not recognized by acl_users or it is
            # already registered with something that implements the
            # member data tool at least partially.
            return u

        # Apply any role mapping if we have it
        if hasattr(self, 'role_map'):
            for portal_role in self.role_map.keys():
                if (self.role_map.get(portal_role) in u.roles and
                        portal_role not in u.roles):
                    u.roles.append(portal_role)

        mdtool = getToolByName(getSite(), 'portal_memberdata', None)
        if mdtool is not None:
            try:
                u = mdtool.wrapUser(u)
            except ConflictError:
                raise
            except:
                logger.exception("Error during wrapUser")
        return u

    @security.protected(View)
    def getPortalRoles(self):
        """
        Return all local roles defined by the portal itself,
        which means roles that are useful and understood
        by the portal object
        """
        parent = self.aq_inner.aq_parent
        roles = list(parent.userdefined_roles())

        # This is *not* a local role in the portal but used by it
        roles.append('Manager')
        roles.append('Owner')

        return roles

    @security.protected(ManagePortal)
    @postonly
    def setRoleMapping(self, portal_role, userfolder_role, REQUEST=None):
        """
        set the mapping of roles between roles understood by
        the portal and roles coming from outside user sources
        """
        if not hasattr(self, 'role_map'): 
            self.role_map = PersistentMapping()

        if len(userfolder_role) < 1:
            del self.role_map[portal_role]
        else:
            self.role_map[portal_role] = userfolder_role

        return MessageDialog(
               title ='Mapping updated',
               message='The Role mappings have been updated',
               action ='manage_mapRoles')

    @security.protected(ManagePortal)
    def getMappedRole(self, portal_role):
        """
        returns a role name if the portal role is mapped to
        something else or an empty string if it is not
        """
        if hasattr(self, 'role_map'):
            return self.role_map.get(portal_role, '')
        else:
            return ''

    @security.protected(View)
    def getCandidateLocalRoles(self, obj):
        """ What local roles can I assign?
            Override the CMFCore version so that we can see the local roles on
            an object, and so that local managers can assign all roles locally.
        """
        member = self.getAuthenticatedMember()
        # Use getRolesInContext as someone may be a local manager
        if 'Manager' in member.getRolesInContext(obj):
            # Use valid_roles as we may want roles defined only on a subobject
            local_roles = [r for r in obj.valid_roles() if r not in
                            ('Anonymous', 'Authenticated', 'Shared')]
        else:
            local_roles = [role for role in member.getRolesInContext(obj)
                                if role not in ('Member', 'Authenticated')]
        local_roles.sort()
        return tuple(local_roles)

    @security.protected(View)
    def loginUser(self, REQUEST=None):
        """ Handle a login for the current user.

        This method takes care of all the standard work that needs to be
        done when a user logs in:
        - clear the copy/cut/paste clipboard
        - PAS credentials update
        - sending a logged-in event
        - storing the login time
        - create the member area if it does not exist
        """
        user = getSecurityManager().getUser()
        if user is None:
            return

        if self.setLoginTimes():
            event.notify(UserInitialLoginInEvent(user))
        else:
            event.notify(UserLoggedInEvent(user))

        if REQUEST is None:
            REQUEST = getattr(self, 'REQUEST', None)
        if REQUEST is None:
            return

        # Expire the clipboard
        if REQUEST.get('__cp', None) is not None:
            REQUEST.RESPONSE.expireCookie('__cp', path='/')

        self.createMemberArea()

        try:
            pas = getToolByName(getSite(), 'acl_users')
            pas.credentials_cookie_auth.login()
        except AttributeError:
            # The cookie plugin may not be present
            pass

    @security.protected(View)
    def logoutUser(self, REQUEST=None):
        """Process a user logout.

        This takes care of all the standard logout work:
        - ask the user folder to logout
        - expire a skin selection cookie
        - invalidate a Zope session if there is one
        """
        # Invalidate existing sessions, but only if they exist.
        sdm = getToolByName(getSite(), 'session_data_manager', None)
        if sdm is not None:
                session = sdm.getSessionData(create=0)
                if session is not None:
                            session.invalidate()

        if REQUEST is None:
            REQUEST = getattr(self, 'REQUEST', None)
        if REQUEST is not None:
            pas = getToolByName(getSite(), 'acl_users')
            try:
                pas.logout(REQUEST)
            except:
                # XXX Bare except copied from logout.cpy. This should be
                # changed in the next Plone release.
                pass

            # Expire the skin cookie if it is not configured to persist
            st = getToolByName(getSite(), "portal_skins")
            skinvar = st.getRequestVarname()
            if skinvar in REQUEST and not st.getCookiePersistence():
                    portal = getToolByName(getSite(), "portal_url") \
                                .getPortalObject()
                    path = '/' + portal.absolute_url(1)
                    # XXX check if this path is sane
                    REQUEST.RESPONSE.expireCookie(skinvar, path=path)

        user = getSecurityManager().getUser()
        if user is not None:
            event.notify(UserLoggedOutEvent(user))

    @security.protected(View)
    def immediateLogout(self):
        """ Log the current user out immediately.  Used by logout.py so that
            we do not have to do a redirect to show the logged out status. """
        noSecurityManager()

    @security.public
    def setLoginTimes(self):
        """ Called by logged_in to set the login time properties
            even if members lack the "Set own properties" permission.

            The return value indicates if this is the first logged
            login time.
        """
        res = False
        if not self.isAnonymousUser():
            member = self.getAuthenticatedMember()
            default = DateTime('2000/01/01')
            login_time = member.getProperty('login_time', default)
            if login_time == default:
                res = True
                login_time = DateTime()
            member.setProperties(login_time=self.ZopeTime(),
                                 last_login_time=login_time)
        return res

    @security.protected(ManagePortal)
    def getBadMembers(self):
        """Will search for members with bad images in the portal_memberdata
        delete their portraits and return their member ids"""
        memberdata = getToolByName(getSite(), 'portal_memberdata')
        portraits = getattr(memberdata, 'portraits', None)
        if portraits is None:
            return []
        bad_member_ids = []
        TXN_THRESHOLD = 50
        counter = 1
        for member_id in tuple(portraits.keys()):
            portrait = portraits[member_id]
            portrait_data = str(portrait.data)
            if portrait_data == '':
                continue
            try:
                import PIL
            except ImportError:
                raise RuntimeError('No Python Imaging Libraries (PIL) found. '
                    'Unable to validate profile image.')
            try:
                img = PIL.Image.open(StringIO(portrait_data))
            except ConflictError:
                pass
            except:
                # Anything else we have a bad bad image and we destroy it
                # and ask questions later.
                portraits._delObject(member_id)
                bad_member_ids.append(member_id)
            if not counter % TXN_THRESHOLD:
                transaction.savepoint(optimistic=True)
            counter = counter + 1

        return bad_member_ids

InitializeClass(MembershipTool)
registerToolInterface('portal_membership', IMembershipTool)