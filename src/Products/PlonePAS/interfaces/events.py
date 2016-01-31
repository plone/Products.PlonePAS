# -*- coding: utf-8 -*-
from zope.deferredimport import deprecated

deprecated(
    "Import from Products.CMFPlone.interfaces.events instead",
    IUserInitialLoginInEvent="Products.CMFPlone.interfaces.events:"
                             "IUserInitialLoginInEvent",
)
