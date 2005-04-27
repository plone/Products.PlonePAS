"""
$Id: groupdata.py,v 1.1 2005/04/27 23:45:47 jccooper Exp $
"""
from Globals import InitializeClass
from Acquisition import aq_base

from Products.CMFPlone.GroupDataTool import GroupDataTool as BaseGroupDataTool
from Products.GroupUserFolder.GroupDataTool import GroupData as BaseGroupData   # we must do this until Plone does it

try:
    from Products.CMFCore.MemberDataTool import CleanupTemp
    _have_cleanup_temp = 1
except:
    _have_cleanup_temp = None

class GroupDataTool(BaseGroupDataTool):
    """PAS-specific implementation of groupdata tool. Uses Plone GroupDataTool as a base."""

    #### an exact copy from the base, so that we pick up the new GroupData.
    #### wrapGroup should have a GroupData factory method to over-ride (or even
    #### set at run-time!) so that we don't have to do this.
    def wrapGroup(self, g):
        """Returns an object implementing the GroupData interface."""

        id = g.getId()
        members = self._members
        if not members.has_key(id):
            # Get a temporary member that might be
            # registered later via registerMemberData().
            temps = self._v_temps
            if temps is not None and temps.has_key(id):
                portal_group = temps[id]
            else:
                base = aq_base(self)
                portal_group = GroupData(base, id)
                if temps is None:
                    self._v_temps = {id:portal_group}
                    if hasattr(self, 'REQUEST'):
                        # No REQUEST during tests.
                        # XXX jcc => CleanupTemp doesn't seem to work on Plone 1.0.3.
                        # Have to find a way to pass around...
                        if _have_cleanup_temp:
                            self.REQUEST._hold(CleanupTemp(self))
                else:
                    temps[id] = portal_group
        else:
            portal_group = members[id]
        # Return a wrapper with self as containment and
        # the user as context.
        return portal_group.__of__(self).__of__(g)
    

InitializeClass(GroupDataTool)


class GroupData(BaseGroupData):

    def _getGroup(self):
        """Get the underlying group object in a PAS-acceptable way.
        (I don't even know why there's the two different ways for GRUF. Speed?)
        """
        return self.getGroup()


InitializeClass(GroupData)
