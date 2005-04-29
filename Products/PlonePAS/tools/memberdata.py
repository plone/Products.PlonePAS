"""
$Id: memberdata.py,v 1.1 2005/04/29 21:16:40 jccooper Exp $
"""
from Globals import InitializeClass
from Acquisition import aq_base

from Products.CMFPlone.MemberDataTool import MemberDataTool as BaseMemberDataTool
from Products.CMFPlone.MemberDataTool import MemberData as BaseMemberData   # this actually isn't used in Plone

from Products.CMFCore.utils import getToolByName

from Products.PluggableAuthService.interfaces.authservice import IPluggableAuthService
from Products.PluggableAuthService.interfaces.plugins import IPropertiesPlugin
from Products.PlonePAS.interfaces.propertysheets import IMutablePropertySheet


class MemberDataTool(BaseMemberDataTool):
    """PAS-specific implementation of memberdata tool. Uses Plone MemberDataTool as a base."""

    #### an exact copy from the base, so that we pick up the new MemberData.
    #### wrapUser should have a MemberData factory method to over-ride (or even
    #### set at run-time!) so that we don't have to do this.
    def wrapUser(self, u):
        '''
        If possible, returns the Member object that corresponds
        to the given User object.
        We override this to ensure OUR MemberData class is used
        '''
        id = u.getId()
        members = self._members
        if not members.has_key(id):
            # Get a temporary member that might be
            # registered later via registerMemberData().
            temps = self._v_temps
            if temps is not None and temps.has_key(id):
                m = temps[id]
            else:
                base = aq_base(self)
                m = MemberData(base, id)
                if temps is None:
                    self._v_temps = {id:m}
                    if hasattr(self, 'REQUEST'):
                        # No REQUEST during tests.
                        self.REQUEST._hold(CleanupTemp(self))
                else:
                    temps[id] = m
        else:
            m = members[id]
        # Return a wrapper with self as containment and
        # the user as context.
        return m.__of__(self).__of__(u)

    def searchFulltextForMembers(self, s):
        """PAS-specific search for members by id, email, full name.
        """
        acl_users = getToolByName( self, 'acl_users')
        return acl_users.searchUsers( name=s, exact_match=False)
        # I don't think this is right: we need to return Members

InitializeClass(MemberDataTool)


class MemberData(BaseMemberData):

    ## XXX: should we also have setProperties?

    def setMemberProperties(self, mapping):
        # Sets the properties given in the MemberDataTool.
        tool = self.getTool()

        if IPluggableAuthService.isImplementedBy(self.acl_users):
            user = self.getUser()
            if hasattr(user, 'getOrderedPropertySheets'):        # we won't always have PlonePAS users, due to acquisition
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
        return BaseMemberData.setProperties(self, mapping)

    def getProperty(self, id, default=None):
        if IPluggableAuthService.isImplementedBy(self.acl_users):
            user = self.getUser()
            if hasattr(user, 'getOrderedPropertySheets'):        # we won't always have PlonePAS users, due to acquisition
                for sheet in user.getOrderedPropertySheets():
                    if sheet.hasProperty(id):
                        return sheet.getProperty(id)
        return BaseMemberData.getProperty(self, id)

InitializeClass(MemberData)
