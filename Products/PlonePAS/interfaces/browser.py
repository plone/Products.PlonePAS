from zope.interface import Interface

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

