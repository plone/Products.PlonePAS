import logging
from cStringIO import StringIO

import transaction
from zope import event
from zope.interface import implements

from DateTime import DateTime
from App.class_init import InitializeClass
from App.special_dtml import DTMLFile
from OFS.Image import Image

from AccessControl import ClassSecurityInfo
from AccessControl import getSecurityManager
from AccessControl import Unauthorized
from AccessControl.SecurityManagement import noSecurityManager
from AccessControl.requestmethod import postonly
from Acquisition import aq_get
from Acquisition import aq_inner
from Acquisition import aq_parent
from zExceptions import BadRequest
from ZODB.POSException import ConflictError

from Products.CMFCore.permissions import ManagePortal
from Products.CMFCore.permissions import ManageUsers
from Products.CMFCore.permissions import SetOwnProperties
from Products.CMFCore.permissions import SetOwnPassword
from Products.CMFCore.permissions import View
from Products.CMFCore.utils import _checkPermission
from Products.CMFCore.utils import getToolByName
from Products.CMFCore.MembershipTool import MembershipTool as BaseTool

from Products.PlonePAS.events import UserLoggedInEvent
from Products.PlonePAS.events import UserInitialLoginInEvent
from Products.PlonePAS.events import UserLoggedOutEvent
from Products.PlonePAS.interfaces import membership
from Products.PlonePAS.utils import cleanId
from Products.PlonePAS.utils import scale_image

default_portrait = 'defaultUser.png'
logger = logging.getLogger('PlonePAS')


class MembershipTool(BaseTool):
    """PAS-based customization of MembershipTool.
    """

    implements(membership.IMembershipTool)

    meta_type = "PlonePAS Membership Tool"
    toolicon = 'tool.gif'
    personal_id = '.personal'
    portrait_id = 'MyPortrait'
    default_portrait = 'defaultUser.gif'
    memberarea_type = 'Folder'
    membersfolder_id = 'Members'
    memberareaCreationFlag = False
    security = ClassSecurityInfo()

    user_search_keywords = ('login', 'fullname', 'email', 'exact_match',
                            'sort_by', 'max_results')

    _properties = (getattr(BaseTool, '_properties', ()) +
                   ({'id': 'user_search_keywords',
                     'type': 'lines',
                     'mode': 'rw',
                     },))

    manage_options = (BaseTool.manage_options +
                      ( { 'label' : 'Portraits'
                     , 'action' : 'manage_portrait_fix'
                     },))

    # TODO I'm not quite sure why getPortalRoles is declared 'Managed'
    #    in CMFCore.MembershipTool - but in Plone we are not so anal ;-)
    security.declareProtected(View, 'getPortalRoles')

    security.declareProtected(ManagePortal, 'manage_mapRoles')
    manage_mapRoles = DTMLFile('../zmi/membershipRolemapping', globals())

    security.declareProtected(ManagePortal, 'manage_portrait_fix')
    manage_portrait_fix = DTMLFile('../zmi/portrait_fix', globals())

    security.declareProtected(ManagePortal, 'manage_setMemberAreaType')
    def manage_setMemberAreaType(self, type_name, REQUEST=None):
        """ ZMI method to set the home folder type by its type name.
        """
        self.setMemberAreaType(type_name)
        if REQUEST is not None:
            REQUEST['RESPONSE'].redirect(self.absolute_url()
                    + '/manage_mapRoles'
                    + '?manage_tabs_message=Member+area+type+changed.')

    security.declareProtected(ManagePortal, 'manage_setMembersFolderById')
    def manage_setMembersFolderById(self, id, REQUEST=None):
        """ ZMI method to set the members folder object by its id.
        """
        self.setMembersFolderById(id)
        if REQUEST is not None:
            REQUEST['RESPONSE'].redirect(self.absolute_url()
                    + '/manage_mapRoles'
                    + '?manage_tabs_message=Members+folder+id+changed.')

    security.declareProtected(ManagePortal, 'setMemberAreaType')
    def setMemberAreaType(self, type_name):
        """ Sets the portal type to use for new home folders.
        """
        # No check for folderish since someone somewhere may actually want
        # members to have objects instead of folders as home "directory".
        self.memberarea_type = str(type_name).strip()

    security.declareProtected(ManagePortal, 'setMembersFolderById')
    def setMembersFolderById(self, id=''):
        """ Set the members folder object by its id.
        """
        self.membersfolder_id = id.strip()

    security.declarePublic('getMembersFolder')
    def getMembersFolder(self):
        """ Get the members folder object.
        """
        parent = aq_parent( aq_inner(self) )
        members = getattr(parent, self.membersfolder_id, None)
        return members

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
        - before_specified_time
        - roles (any role will cause a match)
        - groupname

        This is an 'AND' request.

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
    def createMemberarea(self, member_id=None, minimal=None):
        """
        Create a member area for 'member_id' or the authenticated
        user, but don't assume that member_id is url-safe.
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

        # Create member area without security checks
        typesTool = getToolByName(members, 'portal_types')
        fti = typesTool.getTypeInfo(self.memberarea_type)
        member_folder = fti._constructInstance(members, safe_member_id)

        # Get the user object from acl_users
        acl_users = getToolByName(self, "acl_users")
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

        ## Hook to allow doing other things after memberarea creation.
        notify_script = getattr(member_folder, 'notifyMemberAreaCreated', None)
        if notify_script is not None:
            notify_script()

     # deal with ridiculous API change in CMF
    security.declarePublic('createMemberArea')
    createMemberArea = createMemberarea

    security.declarePublic('getMemberInfo')
    def getMemberInfo(self, memberId=None):
        """
        Return 'harmless' Memberinfo of any member, such as Full name,
        Location, etc
        """
        if not memberId:
            member = self.getAuthenticatedMember()
        else:
            member = self.getMemberById(memberId)

        if member is None:
            return None

        memberinfo = { 'fullname'    : member.getProperty('fullname'),
                       'description' : member.getProperty('description'),
                       'location'    : member.getProperty('location'),
                       'language'    : member.getProperty('language'),
                       'home_page'   : member.getProperty('home_page'),
                       'username'    : member.getUserName(),
                       'has_email'   : bool(member.getProperty('email')),
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


    security.declarePublic('getHomeFolder')
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
                if verifyPermission and not _checkPermission(View, folder):
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


    security.declarePublic('getPersonalFolder')
    def getPersonalFolder(self, member_id=None):
        """
        returns the Personal Item folder for a member
        if no Personal Folder exists will return None
        """
        home=self.getHomeFolder(member_id)
        personal=None
        if home:
            personal=getattr( home
                            , self.personal_id
                            , None )
        return personal


    security.declarePublic('getPersonalPortrait')
    def getPersonalPortrait(self, id=None, verifyPermission=0):
        """Return a members personal portait.

        Modified from CMFPlone version to URL-quote the member id.
        """
        safe_id = self._getSafeMemberId(id)
        membertool   = getToolByName(self, 'portal_memberdata')

        if not safe_id:
            safe_id = self.getAuthenticatedMember().getId()

        portrait = membertool._getPortrait(safe_id)
        if isinstance(portrait, str):
            portrait = None
        if portrait is not None:
            if verifyPermission and not _checkPermission('View', portrait):
                # Don't return the portrait if the user can't get to it
                portrait = None
        if portrait is None:
            portal = getToolByName(self, 'portal_url').getPortalObject()
            portrait = getattr(portal, default_portrait, None)

        return portrait


    security.declareProtected(SetOwnProperties, 'deletePersonalPortrait') 
    def deletePersonalPortrait(self, id=None):
        """deletes the Portait of a member.

        Modified from CMFPlone version to URL-quote the member id.
        """
        safe_id = self._getSafeMemberId(id)
        authenticated_id = self.getAuthenticatedMember().getId()
        if not safe_id:
            safe_id = authenticated_id
        if safe_id != authenticated_id and not _checkPermission(
                ManageUsers, self):
            raise Unauthorized

        membertool = getToolByName(self, 'portal_memberdata')
        return membertool._deletePortrait(safe_id)


    security.declareProtected(SetOwnProperties, 'changeMemberPortrait')
    def changeMemberPortrait(self, portrait, id=None):
        """update the portait of a member.

        Modified from CMFPlone version to URL-quote the member id.
        """
        safe_id = self._getSafeMemberId(id)
        authenticated_id = self.getAuthenticatedMember().getId()
        if not safe_id:
            safe_id = authenticated_id
        if safe_id != authenticated_id and not _checkPermission(
                ManageUsers, self):
            raise Unauthorized
        if portrait and portrait.filename:
            scaled, mimetype = scale_image(portrait)
            portrait = Image(id=safe_id, file=scaled, title='')
            membertool = getToolByName(self, 'portal_memberdata')
            membertool._setPortrait(portrait, safe_id)


    security.declareProtected(ManageUsers, 'listMembers')
    def listMembers(self):
        '''Gets the list of all members.
        THIS METHOD MIGHT BE VERY EXPENSIVE ON LARGE USER FOLDERS AND MUST BE USED
        WITH CARE! We plan to restrict its use in the future (ie. force large requests
        to use searchForMembers instead of listMembers, so that it will not be
        possible anymore to have a method returning several hundred of users :)
        '''
        return BaseTool.listMembers(self)


    security.declareProtected(ManageUsers, 'listMemberIds')
    def listMemberIds(self):
        '''Lists the ids of all members.  This may eventually be
        replaced with a set of methods for querying pieces of the
        list rather than the entire list at once.
        '''
        return self.acl_users.getUserIds()


    security.declareProtected(SetOwnPassword, 'testCurrentPassword')
    def testCurrentPassword(self, password):
        """ test to see if password is current """
        REQUEST=getattr(self, 'REQUEST', {})
        userid=self.getAuthenticatedMember().getUserId()
        acl_users = self._findUsersAclHome(userid)
        if not acl_users:
            return 0
        return acl_users.authenticate(userid, password, REQUEST)


    def _findUsersAclHome(self, userid):
        portal = getToolByName(self, 'portal_url').getPortalObject()
        acl_users=portal.acl_users
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


    security.declareProtected(SetOwnPassword, 'setPassword')
    def setPassword(self, password, domains=None, REQUEST=None):
        '''Allows the authenticated member to set his/her own password.
        '''
        registration = getToolByName(self, 'portal_registration', None)
        if not self.isAnonymousUser():
            member = self.getAuthenticatedMember()
            acl_users = self._findUsersAclHome(member.getUserId())#self.acl_users
            if not acl_users:
                # should not possibly ever happen
                raise BadRequest, 'did not find current user in any user folder'
            if registration:
                failMessage = registration.testPasswordValidity(password)
                if failMessage is not None:
                    raise BadRequest, failMessage

            if domains is None:
                domains = []
            user = acl_users.getUserById(member.getUserId(), None)
            # we must change the users password trough grufs changepassword
            # to keep her  group settings
            if hasattr(user, 'changePassword'):
                user.changePassword(password)
            else:
                acl_users._doChangeUser(member.getUserId(), password, member.getRoles(), domains)
            if REQUEST is None:
                REQUEST = aq_get(self, 'REQUEST', None)
            self.credentialsChanged(password, REQUEST=REQUEST)
        else:
            raise BadRequest, 'Not logged in.'
    setPassword = postonly(setPassword)


    security.declareProtected(View, 'getCandidateLocalRoles')
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
            local_roles = [ role for role in member.getRolesInContext(obj)
                            if role not in ('Member', 'Authenticated') ]
        local_roles.sort()
        return tuple(local_roles)


    security.declareProtected(View, 'loginUser')
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
        user=getSecurityManager().getUser()
        if user is None:
            return

        if self.setLoginTimes():
            event.notify(UserInitialLoginInEvent(user))
        else:
            event.notify(UserLoggedInEvent(user))

        if REQUEST is None:
            REQUEST=getattr(self, 'REQUEST', None)
        if REQUEST is None:
            return

        # Expire the clipboard
        if REQUEST.get('__cp', None) is not None:
            REQUEST.RESPONSE.expireCookie('__cp', path='/')

        self.createMemberArea()

        try:
            pas = getToolByName(self, 'acl_users')
            pas.credentials_cookie_auth.login()
        except AttributeError:
            # The cookie plugin may not be present
            pass


    security.declareProtected(View, 'logoutUser')
    def logoutUser(self, REQUEST=None):
        """Process a user logout.

        This takes care of all the standard logout work:
        - ask the user folder to logout
        - expire a skin selection cookie
        - invalidate a Zope session if there is one
        """
        # Invalidate existing sessions, but only if they exist.
        sdm = getToolByName(self, 'session_data_manager', None)
        if sdm is not None:
                session = sdm.getSessionData(create=0)
                if session is not None:
                            session.invalidate()

        if REQUEST is None:
            REQUEST=getattr(self, 'REQUEST', None)
        if REQUEST is not None:
            pas = getToolByName(self, 'acl_users')
            try:
                pas.logout(REQUEST)
            except:
                # XXX Bare except copied from logout.cpy. This should be
                # changed in the next Plone release.
                pass

            # Expire the skin cookie if it is not configured to persist
            st = getToolByName(self, "portal_skins")
            skinvar = st.getRequestVarname()
            if skinvar in REQUEST and not st.getCookiePersistence():
                    portal = getToolByName(self, "portal_url").getPortalObject()
                    path = '/' + portal.absolute_url(1)
                    # XXX check if this path is sane
                    REQUEST.RESPONSE.expireCookie(skinvar, path=path)

        user=getSecurityManager().getUser()
        if user is not None:
            event.notify(UserLoggedOutEvent(user))


    security.declareProtected(View, 'immediateLogout')
    def immediateLogout(self):
        """ Log the current user out immediately.  Used by logout.py so that
            we do not have to do a redirect to show the logged out status. """
        noSecurityManager()


    security.declarePublic('setLoginTimes')
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


    security.declareProtected(ManagePortal, 'getBadMembers')
    def getBadMembers(self):
        """Will search for members with bad images in the portal_memberdata
        delete their portraits and return their member ids"""
        memberdata = getToolByName(self, 'portal_memberdata')
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
            if not counter%TXN_THRESHOLD:
                transaction.savepoint(optimistic=True)
            counter = counter + 1

        return bad_member_ids


InitializeClass(MembershipTool)
