from Interface import Interface

class IUserDeleterPlugin( Interface ):

    """ Delet a user record in a User Manager
    """

    def doDelUser( login ):

        """ Remove a user record from a User Manager, with the given login
            and password

        o Return a Boolean indicating whether a user was removed or not
        """
