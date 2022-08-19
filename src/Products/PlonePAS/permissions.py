from AccessControl.Permission import addPermission


AddGroups = "Add Groups"
addPermission(AddGroups, default_roles=("Manager",))

ManageGroups = "Manage Groups"
addPermission(ManageGroups, default_roles=("Manager",))

ViewGroups = "View Groups"
addPermission(ViewGroups, default_roles=("Manager", "Owner", "Member"))

DeleteGroups = "Delete Groups"
addPermission(DeleteGroups, default_roles=("Manager",))

SetGroupOwnership = "Set Group Ownership"
addPermission(SetGroupOwnership, default_roles=("Manager", "Owner"))
