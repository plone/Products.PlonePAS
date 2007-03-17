from zope.interface import Interface

class IPASInfoView(Interface):

    def hasLoginPasswordExtractor():
        """Check if a login & password extraction plugin is active.

        Check if there is a plugin with an enabled
        ILoginPasswordExtractionPlugin interface. This can be used to
        conditionally show username & password logins.
        """

    def hasOpenIDdExtractor():
        """Check if an OpenID extraction plugin is active.
        """


class IPASSearchView(Interface):

    def searchUsers(exact_match=False, **critertia):
        """Search for users matching a set of criteria.

        The criteria are a dictionary mapping user properties to values. 
        """


    def searchUsersByRequest(request):
        """Search for users matching a set of criteria found in a request.

        This method will look remove any obvious values from the request
        which are not search criteria. It will also remove any fields
        which have an empty string value.
        """


    def searchGroups(exact_match=False, **critertia):
        """Search for groups matching a set of criteria.

        The criteria are a dictionary mapping group properties to values. 
        """


    def searchGroupsByRequest(request):
        """Search for groups matching a set of criteria found in a request.

        This method will look remove any obvious values from the request
        which are not search criteria. It will also remove any fields
        which have an empty string value.
        """
