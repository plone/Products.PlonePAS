from Products.PluggableAuthService.interfaces.events import IUserLoggedInEvent
from Products.PluggableAuthService.interfaces.events import IUserLoggedOutEvent
from Products.PlonePAS.interfaces.events import IUserInitialLoginInEvent
from Products.PluggableAuthService.events import PASEvent
from zope.interface import implements

class UserLoggedInEvent(PASEvent):
    implements(IUserLoggedInEvent)


class UserInitialLoginInEvent(UserLoggedInEvent):
    implements(IUserInitialLoginInEvent)


class UserLoggedOutEvent(PASEvent):
    implements(IUserLoggedOutEvent)


