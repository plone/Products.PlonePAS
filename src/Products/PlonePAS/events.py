# -*- coding: utf-8 -*-
from Products.PlonePAS.interfaces.events import IUserInitialLoginInEvent
from Products.PluggableAuthService.events import PASEvent
from Products.PluggableAuthService.interfaces.events import IUserLoggedInEvent
from Products.PluggableAuthService.interfaces.events import IUserLoggedOutEvent
from zope.interface import implementer


@implementer(IUserLoggedInEvent)
class UserLoggedInEvent(PASEvent):
    """Plone Implementation of the logged in event

    PAS Event
    """


@implementer(IUserInitialLoginInEvent)
class UserInitialLoginInEvent(UserLoggedInEvent):
    """Implementation of the initial logged in event

    Plone only event!
    """


@implementer(IUserLoggedOutEvent)
class UserLoggedOutEvent(PASEvent):
    """Plone Implementation of the logged out event

    PAS Event
    """
