""" this script returns a boolean depending on whether our PAS implementation
is able to list all users
"""
pas = context.acl_users

# Do we have multiple user plugins?
if len(pas.listPlugins('IUserEnumerationPlugin')) > 1:
    return False

# Does our single user enumerator support the needed API?
for method in ['countAllUsers',
               'getUsers',
               'getUserNames']
    if not hasattr(pas, method):
        return False

return True