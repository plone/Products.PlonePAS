from Globals import InitializeClass
from Products.PluggableAuthService.plugins.BasePlugin import BasePlugin
from Products.PluggableAuthService.interfaces.plugins import IGroupEnumerationPlugin
from Products.PluggableAuthService.interfaces.plugins import IGroupsPlugin
from Products.PluggableAuthService.utils import classImplements

from Products.PageTemplates.PageTemplateFile import PageTemplateFile

manage_addAutoGroupForm = PageTemplateFile("../zmi/AutoGroupForm", globals())

def manage_addAutoGroup(self, id, title='', group='', RESPONSE=None):
    """Add an Auto Group plugin."""

    plugin = AutoGroup(id, title, group)
    self._setObject(id, plugin)

    if RESPONSE is not None:
        return RESPONSE.redirect("%s/manage_workspace?manage_tabs_message=AutoGroup+plugin+added" %
                self.absolute_url())


class AutoGroup(BasePlugin):
    meta_type = "Automatic Group Plugin"

    _properties = (
            { 'id'      : 'title',
              'label'   : 'Title',
              'type'    : 'string',
              'mode'    : 'w',
            },
            { 'id'      : 'group',
              'label'   : 'Group',
              'type'    : 'string',
              'mode'    : 'w',
            },
            )
                

    def __init__(self, id, title=None, group=None):
        self._setId(id)
        self.title = title
        self.group = group

    # IGroupEnumerationPlugin implementation
    def enumerateGroups(self, id, exact_match=False, sort_by=None, max_results=None, **kw):
        if kw:
            return []

        if exact_match and id!=self.group:
            return []

        if not exact_match and id not in self.group:
            return []

        return [ { 'id' : self.group,
                   'plugin_id' : self.getId(),
               } ]


    # IGroupsPlugin implementation
    def getGroupsForPrincipal(self, principal, request=None):
        return (self.group,)

classImplements(AutoGroup, IGroupEnumerationPlugin, IGroupsPlugin)
InitializeClass(AutoGroup)

