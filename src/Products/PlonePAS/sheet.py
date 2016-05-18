# -*- coding: utf-8 -*-
"""
Add Mutable Property Sheets and Schema Mutable Property Sheets to PAS

also a property schema type registry which is extensible.

"""
from Acquisition import aq_base
from Acquisition import aq_chain
from Acquisition import aq_inner
from Products.CMFCore.interfaces import ISiteRoot
from Products.PluggableAuthService.interfaces.authservice import \
	IPluggableAuthService  # noqa
from Products.PluggableAuthService.MutablePropertySheet import \
	MutablePropertySheet as BaseMutablePropertySheet  # noqa
from zope.component import getUtility
from zope.deferredimport import deprecated

deprecated(
    "Import from Products.PluggableAuthService.MutablePropertySheet instead.",
    validateValue='Products.PluggableAuthService.MutablePropertySheet:'
                  'validateValue'
)


class MutablePropertySheet(BaseMutablePropertySheet):
    """this class of MutablePropertySheet is what Plone used, but does
    not fullfill its own contract. After moving the implementation to
    PAS itself over there we fullfill the interfaces contract.
    In this implementation the old contract is in place. It prepend the userid
    to setProperties and setProperty in order to delegate back to the plugin.
    I doubt that this is good application design nor does it solve a problem,
    moreover this is just a workaround which should be solved in the calling
    API.
    """

    def setProperty(self, user, id, value):
        super(MutablePropertySheet, self).setProperty(id, value)

        # cascade to plugin
        provider = self._getPropertyProviderForUser(user)
        provider.setPropertiesForUser(user, self)

    def setProperties(self, user, mapping):
        """user is not part of the interface contract!
        """
        super(MutablePropertySheet, self).setProperties(mapping)

        # cascade to plugin
        provider = self._getPropertyProviderForUser(user)
        provider.setPropertiesForUser(user, self)

    def _getPropertyProviderForUser(self, user):
        """user is not part of the interface contract!
        """
        portal = getUtility(ISiteRoot)
        if IPluggableAuthService.providedBy(portal.acl_users):
            return portal.acl_users._getOb(self._id)

        raise AttributeError(
            'No acl_users found in aq_chain providing plugin {0}'.format(
                self._id
            )
        )

