"""
$Id: plugins.py,v 1.2 2005/02/04 07:57:00 k_vertigo Exp $
"""

from Products.PluggableAuthService.interfaces import plugins

class IUserManagement( plugins.IUserAdderPlugin ):

    """ Manage users 
    """

    def doChangeUser( login, password, **kw):
        """
        change a user's password ( differs from role )
        roles are set in the pas engine api for
        the same but are set via a role manager )
        """

    def doDeleteUser( login ):

        """ Remove a user record from a User Manager, with the given login
            and password

        o Return a Boolean indicating whether a user was removed or not
        """
