from App.class_init import InitializeClass
import Acquisition
from Products.PluggableAuthService.plugins.BasePlugin import BasePlugin
from Products.PluggableAuthService.interfaces.plugins import IGroupEnumerationPlugin
from Products.PluggableAuthService.interfaces.plugins import IGroupsPlugin
from Products.PluggableAuthService.utils import classImplements
from Products.PlonePAS.interfaces.group import IGroupIntrospection


from Products.PageTemplates.PageTemplateFile import PageTemplateFile

manage_addAutoGroupForm = PageTemplateFile("../zmi/AutoGroupForm", globals())

def manage_addAutoGroup(self, id, title='', group='', description='', RESPONSE=None):
    """Add an Auto Group plugin."""

    plugin = AutoGroup(id, title, group, description)
    self._setObject(id, plugin)

    if RESPONSE is not None:
        return RESPONSE.redirect("%s/manage_workspace?manage_tabs_message=AutoGroup+plugin+added" %
                self.absolute_url())


class VirtualGroup(Acquisition.Implicit):
    def __init__(self, id, description):
        self.id = id
        self.title = description

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

    def allowed(self, object, obect_roles=None):
        return 0

    def getDomains(self):
        return []

    def isGroup(self):
        return True




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
            { 'id'      : 'description',
              'label'   : 'Description',
              'type'    : 'string',
              'mode'    : 'w',
            },
            )
                

    def __init__(self, id, title='', group=None, description=''):
        self._setId(id)
        self.title = title
        self.group = group
        self.description = description

    # IGroupEnumerationPlugin implementation
    def enumerateGroups(self, id=None, exact_match=False, sort_by=None, max_results=None, **kw):
        if kw:
            return []

        if id:
            id = id.lower()
            mygroup = self.group.lower()

            if exact_match and id!=mygroup:
                return []

            if not exact_match and id not in mygroup:
                return []

        return [ { 'id' : self.group,
                   'groupid' : self.group,
                   'title' : self.description,
                   'pluginid' : self.getId(),
               } ]


    # IGroupsPlugin implementation
    def getGroupsForPrincipal(self, principal, request=None):
        return (self.group,)


    # IGroupIntrospection implementation
    def getGroupById(self, group_id):
        if group_id != self.group:
            return None

        return VirtualGroup(self.group, self.description)


    def getGroups(self):
        return [self.getGroupById(id) for id in self.getGroupIds()]


    def getGroupIds(self):
        return [ self.group ]


    def getGroupMembers(self, group_id):
        return ()

classImplements(AutoGroup, IGroupEnumerationPlugin, IGroupsPlugin, IGroupIntrospection)
InitializeClass(AutoGroup)

