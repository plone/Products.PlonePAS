# -*- coding: utf-8 -*-
from Products.CMFCore.permissions import setDefaultRoles

AddGroups = 'Add Groups'
setDefaultRoles(AddGroups, ('Manager',))

ManageGroups = 'Manage Groups'
setDefaultRoles(ManageGroups, ('Manager',))

ViewGroups = 'View Groups'
setDefaultRoles(ViewGroups, ('Manager', 'Owner', 'Member'))

DeleteGroups = 'Delete Groups'
setDefaultRoles(DeleteGroups, ('Manager', ))

SetGroupOwnership = 'Set Group Ownership'
setDefaultRoles(SetGroupOwnership, ('Manager', 'Owner'))
