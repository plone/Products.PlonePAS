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

    def searchUsers(sort_by=None, **criteria):
        """Search for users matching a set of criteria.

        The criteria are a dictionary mapping user properties to values.
        Duplicate results returned by PAS are filtered so only the first
        result remains in the result set. The results can be sorted on
        sort_bys (case insensitive).
        """


    def searchUsersByRequest(request, sortKey=None):
        """Search for users matching a set of criteria found in a request.

        This method will look remove any obvious values from the request
        which are not search criteria. It will also remove any fields
        which have an empty string value.
        Duplicate results returned by PAS are filtered so only the first
        result remains in the result set. The results can be sorted on
        sort_by (case insensitive).
        """


    def searchGroups(**criteria):
        """Search for groups matching a set of criteria.

        The criteria are a dictionary mapping group properties to values. 
        """


    def searchGroupsByRequest(request):
        """Search for groups matching a set of criteria found in a request.

        This method will look remove any obvious values from the request
        which are not search criteria. It will also remove any fields
        which have an empty string value.
        """
