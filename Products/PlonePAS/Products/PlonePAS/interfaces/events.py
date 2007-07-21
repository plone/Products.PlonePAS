from Products.PluggableAuthService.interfaces.events import IUserLoggedInEvent

class IUserInitialLoginInEvent(IUserLoggedInEvent):
    """A user logs in for the first time in the portal.
    """
