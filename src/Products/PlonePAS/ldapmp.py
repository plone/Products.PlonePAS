from Products.PlonePAS.patch import call
from Products.PlonePAS.patch import wrap_method
from Products.PlonePAS.plugins.group import PloneGroup


GROUP_PROPERTY_MAP = {
    # target property: (possible key, ...)
    "title": (
        "name",
        "displayName",
        "cn",
    ),
    "description": ("description",),
    "email": ("mail",),
}

KNOWN_ATTRS = set()
for attrs in GROUP_PROPERTY_MAP.values():
    for attr in attrs:
        KNOWN_ATTRS.add(attr)


def getPropertiesForUser(self, user, request=None):
    """Fullfill PropertiesPlugin requirements"""

    if not isinstance(user, PloneGroup):
        # It's not a PloneGroup, continue as usual
        return call(self, "getPropertiesForUser", user=user, request=request)

    # We've got a PloneGroup.
    # Search for groups instead of users
    groups = self.enumerateGroups(id=user.getId(), exact_match=True)
    # XXX Should we assert there's only one group?
    properties = {}
    for group in groups:
        for pname, attrs in GROUP_PROPERTY_MAP.items():
            for attr in attrs:
                value = group.get(attr)
                if value:
                    # Break on first found
                    properties[pname] = value
                    break

    return properties


def getGroupsForPrincipal(self, user, request=None, attr=None):
    """Fulfill GroupsPlugin requirements, but don't return any groups for
    groups"""

    if not isinstance(user, PloneGroup):
        # It's not a PloneGroup, continue as usual
        return call(self, "getGroupsForPrincipal", user, request=request, attr=attr)

    return ()


def patch_ldapmp():
    from Products.LDAPMultiPlugins.LDAPPluginBase import LDAPPluginBase

    wrap_method(LDAPPluginBase, "getPropertiesForUser", getPropertiesForUser)

    from Products.LDAPMultiPlugins.LDAPMultiPlugin import LDAPMultiPlugin

    wrap_method(LDAPMultiPlugin, "getGroupsForPrincipal", getGroupsForPrincipal)
