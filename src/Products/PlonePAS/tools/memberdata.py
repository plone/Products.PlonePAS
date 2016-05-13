# -*- coding: utf-8 -*-
from AccessControl import ClassSecurityInfo
from AccessControl.requestmethod import postonly
from Acquisition import aq_base
from App.class_init import InitializeClass
from Products.BTreeFolder2.BTreeFolder2 import BTreeFolder2
from Products.CMFCore.MemberDataTool import _marker
from Products.CMFCore.MemberDataTool import MemberData as BaseMemberData
from Products.CMFCore.MemberDataTool import MemberDataTool as BaseTool
from Products.CMFCore.permissions import ManagePortal
from Products.CMFCore.utils import getToolByName
from Products.PlonePAS.interfaces.capabilities import IAssignRoleCapability
from Products.PlonePAS.interfaces.capabilities import IDeleteCapability
from Products.PlonePAS.interfaces.capabilities import IGroupCapability
from Products.PlonePAS.interfaces.capabilities import IManageCapabilities
from Products.PlonePAS.interfaces.capabilities import IPasswordSetCapability
from Products.PlonePAS.interfaces.group import IGroupManagement
from Products.PlonePAS.interfaces.plugins import IUserManagement
from Products.PlonePAS.interfaces.propertysheets import IMutablePropertySheet
from Products.PluggableAuthService.interfaces.authservice import \
    IPluggableAuthService
from Products.PluggableAuthService.interfaces.plugins import IPropertiesPlugin
from Products.PluggableAuthService.interfaces.plugins import \
    IRoleAssignerPlugin
from zope.interface import implementer


class MemberDataTool(BaseTool):
    """PAS-specific implementation of memberdata tool.
    """

    meta_type = "PlonePAS MemberData Tool"
    security = ClassSecurityInfo()
    toolicon = 'tool.gif'

    def __init__(self):
        BaseTool.__init__(self)
        self.portraits = BTreeFolder2(id='portraits')

    def _getPortrait(self, member_id):
        "return member_id's portrait if you can "
        return self.portraits.get(member_id, None)

    def _setPortrait(self, portrait, member_id):
        " store portrait which must be a raw image in _portrais "
        if member_id in self.portraits:
            self.portraits._delObject(member_id)
        self.portraits._setObject(id=member_id, object=portrait)

    def _deletePortrait(self, member_id):
        " remove member_id's portrait "
        if member_id in self.portraits:
            self.portraits._delObject(member_id)

    @security.private
    def pruneMemberDataContents(self):
        '''
        Compare the user IDs stored in the member data
        tool with the list in the actual underlying acl_users
        and delete anything not in acl_users
        '''
        BaseTool.pruneMemberDataContents(self)
        membertool = getToolByName(self, 'portal_membership')
        portraits = self.portraits
        user_list = membertool.listMemberIds()

        for tuple in portraits.items():
            member_id = tuple[0]
            if member_id not in user_list:
                self.portraits._delObject(member_id)

    @security.protected(ManagePortal)
    def purgeMemberDataContents(self):
        '''
        Delete ALL MemberData information. This is required for us as we change
        the MemberData class.
        '''
        members = self._members

        for tuple in members.items():
            member_name = tuple[0]
            del members[member_name]

        return "Done."

    @security.private
    def updateMemberDataContents(self,):
        """Update former MemberData objects to new MemberData objects
        """
        count = 0
        members = self._members
        properties = self.propertyIds()

        # Scan members for old MemberData
        for member_name, member_obj in members.items():
            values = {}
            if getattr(member_obj, "_is_new_kind", None):
                continue        # Do not have to upgrade that object

            # Have to upgrade. Create the values mapping.
            for pty_name in properties:
                user_value = getattr(member_obj, pty_name, _marker)
                if user_value is not _marker:
                    values[pty_name] = user_value

            # Wrap a new user object of the RIGHT class
            u = self.acl_users.getUserById(member_name, None)
            if not u:
                continue                # User is not in main acl_users anymore
            self.wrapUser(u)

            # Set its properties
            mbr = self._members.get(member_name, None)
            if not mbr:
                raise RuntimeError(
                    "Error while upgrading user '{0}'.".format(member_name)
                )
            mbr.setProperties(values, force_local=1)
            count += 1

        return count

    @security.private
    def searchMemberDataContents(self, search_param, search_term):
        """
        Search members.
        This is the same as CMFCore except that it doesn't check term case.
        """
        res = []

        search_term = search_term.strip().lower()

        if search_param == 'username':
            search_param = 'id'

        mtool = getToolByName(self, 'portal_membership')

        for member_id in self._members.keys():
            user_wrapper = mtool.getMemberById(member_id)

            if user_wrapper is not None:
                memberProperty = user_wrapper.getProperty
                searched = memberProperty(search_param, None)

                if searched is not None:
                    if searched.strip().lower().find(search_term) != -1:

                        res.append({'username': memberProperty('id'),
                                    'email': memberProperty('email', '')})
        return res

    @security.public
    def searchFulltextForMembers(self, s):
        # Note: do NOT add a docstring to this method: it is okay if the method
        # is public, but it must not be published through the web, which is
        # what a docstring would do.
        #
        # Search for members which do have string 's' in name, email or full
        # name (if defined).  This is mainly used for the localrole form.
        s = s.strip().lower()
        mu = getToolByName(self, 'portal_membership')

        res = []
        for member in mu.listMembers():
            u = member.getUser()
            if u.getUserName().lower().find(s) != -1 \
               or member.getProperty('fullname').lower().find(s) != -1 \
               or member.getProperty('email').lower().find(s) != -1:
                res.append(member)
        return res

    # check to see if we can add users. Need to be careful here
    # so we do not write on read
    def canAddMemberData(self):
        try:
            if self.REQUEST.REQUEST_METHOD != 'POST':
                return False
            if getattr(self, '_p_jar', None) and \
                    len(self._p_jar._registered_objects) > 0:
                # XXX do not write on read
                return True
        except AttributeError:
            pass
        return False

    # an exact copy from the base, so that we pick up the new MemberData.
    # wrapUser should have a MemberData factory method to over-ride (or even
    # set at run-time!) so that we don't have to do this.
    def wrapUser(self, u):
        '''
        If possible, returns the Member object that corresponds
        to the given User object.
        We override this to ensure OUR MemberData class is used
        '''
        user_id = u.getId()
        members = self._members
        if user_id not in members:
            base = aq_base(self)
            md = MemberData(base, user_id)
            if self.canAddMemberData():
                # XXX do not write on read
                members[user_id] = md
            return md.__of__(self).__of__(u)
        else:
            # Return a wrapper with self as containment and
            # the user as context.
            return members[user_id].__of__(self).__of__(u)

    @postonly
    def deleteMemberData(self, member_id, REQUEST=None):
        """ Delete member data of specified member.
        """
        if IPluggableAuthService.providedBy(self.acl_users):
            # It's a PAS! Whee!
            # XXX: can we safely assume that user name == member_id
            plugins = self._getPlugins()
            prop_managers = plugins.listPlugins(IPropertiesPlugin)
            for mid, prop_manager in prop_managers:
                # Not all PropertiesPlugins support user deletion
                try:
                    prop_manager.deleteUser(member_id)
                except AttributeError:
                    pass

        # we won't always have PlonePAS users, due to acquisition,
        # nor are guaranteed property sheets
        members = self._members
        if member_id in members:
            del members[member_id]
            return 1
        else:
            return 0

    # plugin getter
    def _getPlugins(self):
        return self.acl_users.plugins

InitializeClass(MemberDataTool)


@implementer(IManageCapabilities)
class MemberData(BaseMemberData):

    security = ClassSecurityInfo()

    # setProperties uses setMemberProperties. no need to override.

    def setMemberProperties(self, mapping, force_local=0, force_empty=False):
        """PAS-specific method to set the properties of a
        member. Ignores 'force_local', which is not reliably present.
        """
        sheets = None

        # We could pay attention to force_local here...
        if not IPluggableAuthService.providedBy(self.acl_users):
            # Defer to base impl in absence of PAS, a PAS user, or
            # property sheets
            return BaseMemberData.setMemberProperties(self, mapping)
        else:
            # It's a PAS! Whee!
            user = self.getUser()
            sheets = getattr(user, 'getOrderedPropertySheets', lambda: None)()

            # We won't always have PlonePAS users, due to acquisition,
            # nor are guaranteed property sheets
            if not sheets:
                # Defer to base impl if we have a PAS but no property
                # sheets.
                return BaseMemberData.setMemberProperties(self, mapping)

        # If we got this far, we have a PAS and some property sheets.
        # XXX track values set to defer to default impl
        # property routing?
        modified = False
        for k, v in mapping.items():
            if v is None and not force_empty:
                continue
            for sheet in sheets:
                if not sheet.hasProperty(k):
                    continue
                if IMutablePropertySheet.providedBy(sheet):
                    sheet.setProperty(user, k, v)
                    modified = True
                else:
                    break
        if modified:
            self.notifyModified()

    def getProperty(self, id, default=_marker):
        """PAS-specific method to fetch a user's properties. Looks
        through the ordered property sheets.
        """
        sheets = None
        if not IPluggableAuthService.providedBy(self.acl_users):
            return BaseMemberData.getProperty(self, id)
        else:
            # It's a PAS! Whee!
            user = self.getUser()
            sheets = getattr(user, 'getOrderedPropertySheets', lambda: None)()

            # we won't always have PlonePAS users, due to acquisition,
            # nor are guaranteed property sheets
            if not sheets:
                try:
                    return BaseMemberData.getProperty(self, id, default)
                except ValueError:
                    # Zope users don't have PropertySheets,
                    # return an empty string for them if the property
                    # doesn't exists.
                    return ''

        # If we made this far, we found a PAS and some property sheets.
        for sheet in sheets:
            if sheet.hasProperty(id):
                # Return the first one that has the property.
                value = sheet.getProperty(id)
                if isinstance(value, unicode):
                    # XXX Temporarily work around the fact that
                    # property sheets blindly store and return
                    # unicode. This is sub-optimal and should be
                    # dealed with at the property sheets level by
                    # using Zope's converters.
                    return value.encode('utf-8')
                return value

        # Couldn't find the property in the property sheets. Try to
        # delegate back to the base implementation.
        return BaseMemberData.getProperty(self, id, default)

    def getPassword(self):
        """Returns None. Present to avoid NotImplementedError."""
        return None

    # IManageCapabilities methods

    def canDelete(self):
        """True iff user can be removed from the Plone UI."""
        # IUserManagement provides doDeleteUser
        plugins = self._getPlugins()
        managers = plugins.listPlugins(IUserManagement)
        for mid, manager in managers:
            if (IDeleteCapability.providedBy(manager) and
                    manager.allowDeletePrincipal(self.getId())):
                return True
        return False

    def canPasswordSet(self):
        """True iff user can change password."""
        # IUserManagement provides doChangeUser
        plugins = self._getPlugins()
        managers = plugins.listPlugins(IUserManagement)
        for mid, manager in managers:
            if (IPasswordSetCapability.providedBy(manager) and
                    manager.allowPasswordSet(self.getId())):
                return True
        return False

    def passwordInClear(self):
        """True iff password can be retrieved in the clear (not hashed.)

        False for PAS. It provides no API for getting passwords,
        though it would be possible to add one in the future.
        """
        return 0

    def _memberdataHasProperty(self, prop_name):
        mdata = getToolByName(self, 'portal_memberdata', None)
        if mdata:
            return mdata.hasProperty(prop_name)
        return 0

    def canWriteProperty(self, prop_name):
        """True iff the member/group property named in 'prop_name'
        can be changed.
        """
        if not IPluggableAuthService.providedBy(self.acl_users):
            # not PAS; Memberdata is writable
            return self._memberdataHasProperty(prop_name)
        else:
            # it's PAS
            user = self.getUser()
            sheets = getattr(user, 'getOrderedPropertySheets', lambda: None)()
            if not sheets:
                return self._memberdataHasProperty(prop_name)

            for sheet in sheets:
                if not sheet.hasProperty(prop_name):
                    continue
                if IMutablePropertySheet.providedBy(sheet):
                    # BBB for plugins implementing an older version of
                    # IMutablePropertySheet
                    if hasattr(sheet, 'canWriteProperty'):
                        return sheet.canWriteProperty(user, prop_name)
                    return True
                else:
                    break  # shadowed by read-only
        return False

    def canAddToGroup(self, group_id):
        """True iff member can be added to group."""
        # IGroupManagement provides IGroupCapability
        plugins = self._getPlugins()
        managers = plugins.listPlugins(IGroupManagement)
        for mid, manager in managers:
            if (IGroupCapability.providedBy(manager) and
                    manager.allowGroupAdd(self.getId(), group_id)):
                return True
        return False

    def canRemoveFromGroup(self, group_id):
        """True iff member can be removed from group."""
        # IGroupManagement provides IGroupCapability
        plugins = self._getPlugins()
        managers = plugins.listPlugins(IGroupManagement)
        for mid, manager in managers:
            if (IGroupCapability.providedBy(manager) and
                    manager.allowGroupRemove(self.getId(), group_id)):
                return True
        return False

    def canAssignRole(self, role_id):
        """True iff member can be assigned role. Role id is string."""
        # IRoleAssignerPlugin provides IAssignRoleCapability
        plugins = self._getPlugins()
        managers = plugins.listPlugins(IRoleAssignerPlugin)
        for mid, manager in managers:
            if (IAssignRoleCapability.providedBy(manager) and
                    manager.allowRoleAssign(self.getId(), role_id)):
                return True
        return False

    @security.private
    def setSecurityProfile(self, password=None, roles=None, domains=None):
        """Set the user's basic security profile"""
        u = self.getUser()

        # The Zope User API is stupid, it should check for None.
        if roles is None:
            roles = list(u.getRoles())
            if 'Authenticated' in roles:
                roles.remove('Authenticated')
        if domains is None:
            domains = u.getDomains()

        u.userFolderEditUser(u.getUserId(), password, roles, domains)

    # plugin getters

    @security.private
    def _getPlugins(self):
        return self.acl_users.plugins


InitializeClass(MemberData)
