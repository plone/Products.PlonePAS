# -*- coding: utf-8 -*-
from Products.PluggableAuthService.events import PASEvent
from Products.PluggableAuthService.interfaces.events import IUserLoggedInEvent
from Products.PluggableAuthService.interfaces.events import IUserLoggedOutEvent
from zope.deferredimport import deprecated
from zope.interface import implementer


@implementer(IUserLoggedInEvent)
class UserLoggedInEvent(PASEvent):
    """Plone Implementation of the logged in event

    PAS Event
    """


deprecated(
    "Import from Products.CMFPlone.events instead",
    UserInitialLoginInEvent="Products.CMFPlone.events:UserInitialLoginInEvent,"
    )


@implementer(IUserLoggedOutEvent)
class UserLoggedOutEvent(PASEvent):
    """Plone Implementation of the logged out event

    PAS Event
    """
