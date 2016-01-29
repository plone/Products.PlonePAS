# -*- coding: utf-8 -*-
from zope.deferredimport import deprecated


deprecated(
    "Import from Products.PluggableAuthService.events instead",
    UserLoggedInEvent="Products.PluggableAuthService.events:"
                      "UserLoggedIn",
    )

deprecated(
    "Import from Products.CMFPlone.events instead",
    UserInitialLoginInEvent="Products.CMFPlone.events:UserInitialLoginInEvent",
    )

deprecated(
    "Import from Products.PluggableAuthService.events instead",
    UserLoggedOutEvent="Products.PluggableAuthService.events:"
                       "UserLoggedOut",
    )
