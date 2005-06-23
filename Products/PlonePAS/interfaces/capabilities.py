##############################################################################
#
# Copyright (c) 2005 Enfold Systems, LLC
# Reserved.
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
Define certain interfaces that a plugin must meet if it is to allow
certain operations to be done by the Plone UI.

$Id: capabilities.py,v 1.2 2005/06/23 21:01:57 jccooper Exp $
"""

from Interface import Interface

class IDeleteCapability(Interface):
    """Interface for plugin to say if it allows for deletion of a user.
    Expected to be found on IUserManagement plugins.
    For Plone UI.
    """

    def allowDeleteUser(self, user_id):
        """True iff this plugin can delete a certain user."""

class IPasswordSetCapability(Interface):
    """Interface for plugin to say if it allows for setting the password of a user.
    Expected to be found on IUserManagement plugins.
    For Plone UI.
    """

    def allowPasswordSetUser(self, user_id):
        """True iff this plugin can set the password of a certain user."""


#class IPasswordClearCapability(Interface):
#    """Interface for plugin to say if it allows for deletion of a user.
#    For Plone UI.
#    """
#
#    def passwordInClear(self, user_id):
#        """True iff this plugin provides a clear-text password for a certain user."""

class IGroupCapability(Interface):
    """Interface for plugin to say if it allows for deletion of a user.
    For Plone UI.
    """

    def allowGroupAdd(self, user_id, group_id):
        """True iff this plugin will allow adding a certain user to a certain group."""
    
    def allowGroupRemove(self, user_id, group_id):
        """True iff this plugin will allow removing a certain user from a certain group."""
    

class IAssignRoleCapability(Interface):
    """Interface for plugin to say if it allows for deletion of a user.
    For Plone UI.
    """

    def allowRoleAssign(self, user_id, role):
        """True iff this plugin will allo assigning a certain user a certain role."""



class IManageCapabilities(Interface):
    """Interface for MemberData/GroupData to provide information as to whether or not
    the member can be deleted, reset password, modify a property.
    """

    def canDelete(self):
        """True iff user can be removed from the Plone UI."""

    def canPasswordSet(self):
        """True iff user can change password."""

    def passwordInClear(self):
        """True iff password can be retrieved in the clear (not hashed.)"""

    def canWriteProperty(self, prop_name):
        """True iff the member/group property named in 'prop_name'
        can be changed.
        """

    def canAddToGroup(self, group_id):
        """True iff member can be added to group."""

    def canRemoveFromGroup(self, group_id):
        """True iff member can be removed from group."""

    def canAssignRole(self, role):
        """True iff member can be assigned role."""