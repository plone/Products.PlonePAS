# -*- coding: utf-8 -*-
from App.class_init import InitializeClass
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from Products.PlonePAS.interfaces.group import IGroupIntrospection
from Products.PluggableAuthService.PropertiedUser import PropertiedUser
from Products.PluggableAuthService.interfaces.plugins import \
    IGroupEnumerationPlugin
from Products.PluggableAuthService.interfaces.plugins import IGroupsPlugin
from Products.PluggableAuthService.interfaces.plugins import IPropertiesPlugin
from Products.PluggableAuthService.plugins.BasePlugin import BasePlugin
from zope.interface import implementer

manage_addAutoGroupForm = PageTemplateFile("../zmi/AutoGroupForm", globals())


def manage_addAutoGroup(self, id, title='', group='', description='',
                        RESPONSE=None):
    """Add an Auto Group plugin."""

    plugin = AutoGroup(id, title, group, description)
    self._setObject(id, plugin)

    if RESPONSE is not None:
        return RESPONSE.redirect(
            "%s/manage_workspace?manage_tabs_message=AutoGroup+plugin+added"
            % self.absolute_url())


class VirtualGroup(PropertiedUser):
    def __init__(self, id, title='', description=''):
        super(VirtualGroup, self).__init__(id)
        self.id = id
        self.title = title
        self.description = description

    def getId(self):
        return self.id

    def getUserName(self):
        return self.id

    def getName(self):
        return self.id

    def getMemberIds(self, transitive=1):
        return []

    def getRolesInContext(self, context):
        return []

    def getRoles(self):
        return []

    def allowed(self, object, object_roles=None):
        return 0

    def getDomains(self):
        return []

    def isGroup(self):
        return True


@implementer(
    IGroupEnumerationPlugin,
    IGroupsPlugin,
    IGroupIntrospection,
    IPropertiesPlugin
)
class AutoGroup(BasePlugin):
    meta_type = "Automatic Group Plugin"

    _properties = (
        {'id': 'title',
         'label': 'Title',
         'type': 'string',
         'mode': 'w'},
        {'id': 'group',
         'label': 'Group',
         'type': 'string',
         'mode': 'w'},
        {'id': 'description',
         'label': 'Description',
         'type': 'string',
         'mode': 'w'},
    )

    def __init__(self, id, title='', group=None, description=''):
        self._setId(id)
        self.title = title
        self.group = group
        self.description = description

    # IGroupEnumerationPlugin implementation
    def enumerateGroups(self, id=None, exact_match=False, sort_by=None,
                        max_results=None, **kw):
        if kw:
            return []

        if id:
            id = id.lower()
            mygroup = self.group.lower()

            if exact_match and id != mygroup:
                return []

            if not exact_match and id not in mygroup:
                return []

        return [{'id': self.group,
                 'groupid': self.group,
                 'title': self.title,
                 'pluginid': self.getId()}]

    # IGroupsPlugin implementation
    def getGroupsForPrincipal(self, principal, request=None):
        if principal.getUserName() == self.group:
            return ()

        return (self.group,)

    # IGroupIntrospection implementation
    def getGroupById(self, group_id):
        if group_id != self.group:
            return None

        return VirtualGroup(self.group, title=self.title,
                            description=self.description)

    def getGroups(self):
        return [self.getGroupById(id) for id in self.getGroupIds()]

    def getGroupIds(self):
        return [self.group]

    def getGroupMembers(self, group_id):
        return ()

    # IPropertiesPlugin:
    def getPropertiesForUser(self, user, request=None):
        if user == self.group:
            return {'title': self.title,
                    'description': self.description}
        else:
            return {}


InitializeClass(AutoGroup)
