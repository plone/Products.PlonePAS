##############################################################################
#
# PlonePAS - Adapt PluggableAuthService for use in Plone
# Copyright (C) 2005 Enfold Systems, Kapil Thangavelu, et al
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this
# distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""
$Id$
"""

from Products.PlonePAS.patch import call, wrap_method
from Products.PlonePAS.plugins.group import PloneGroup
from Products.LDAPUserFolder.utils import GROUP_MEMBER_MAP
from Products.LDAPUserFolder.LDAPDelegate import filter_format
from Products.LDAPMultiPlugins.LDAPPluginBase import LDAPPluginBase

GROUP_PROPERTY_MAP = {
    # target property: ((possible key, as-is),)
    'title': (('name', False),
              ('displayName', False),
              ('cn', False)),
    'description': (('description', False),),
    'email': (('mail', False),),
    }

KNOWN_ATTRS = []
for attrs in GROUP_PROPERTY_MAP.values():
    for attr, as_is in attrs:
        if attr in KNOWN_ATTRS:
            continue
        KNOWN_ATTRS.append(attr)

def getPropertiesForUser(self, user, request=None):
    """Fullfill PropertiesPlugin requirements
    """

    if not isinstance(user, PloneGroup):
        # It's not a PloneGroup, continue as usual
        return call(self, 'getPropertiesForUser', user=user, request=request)

    # We've got a PloneGroup.
    acl = self._getLDAPUserFolder()

    if acl is None:
        return ()

    group_filter = [filter_format('(%s=%s)', ('objectClass', o))
                    for o in GROUP_MEMBER_MAP.keys()]
    search_str = '(|%s)' % ''.join(group_filter)

    name = getattr(self, 'groupid_attr', 'cn')
    value = user.getId()
    search_str = '(&%s%s)' % (search_str, filter_format('(%s=%s)', (name, value)))

    delegate = acl._delegate

    if acl._binduid_usage > 0:
        bind_dn = acl._binduid
        bind_pwd = acl._bindpwd
    else:
        bind_dn = bind_pwd = ''

    R = delegate.search(acl.getProperty('groups_base'),
                        acl.getProperty('groups_scope'),
                        filter=search_str,
                        attrs=KNOWN_ATTRS,
                        bind_dn=bind_dn,
                        bind_pwd=bind_pwd)

    if R['exception']:
        raise RuntimeError, R['exception']

    groups = R['results']

    properties = {}
    # XXX Should we assert there's only one group?
    for group in groups:
        for pname, attrs in GROUP_PROPERTY_MAP.items():
            for attr, as_is in attrs:
                if not group.has_key(attr):
                    continue
                value = group[attr]
                if not as_is:
                    value = value[0]
                if value:
                    # Break on first found
                    properties[pname] = value
                    break

    return properties

wrap_method(LDAPPluginBase, 'getPropertiesForUser', getPropertiesForUser)
