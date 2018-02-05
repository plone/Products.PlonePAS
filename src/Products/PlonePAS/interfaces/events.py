# -*- coding: utf-8 -*-
from Products.PluggableAuthService.interfaces.events import IPASEvent
from Products.PluggableAuthService.interfaces.events import IUserLoggedInEvent


class IPrincipalBeforeDeletedEvent(IPASEvent):
    """A user is marked to be removed but still into database.
    """


class IUserInitialLoginInEvent(IUserLoggedInEvent):
    """A user logs in for the first time in the portal.
    """
