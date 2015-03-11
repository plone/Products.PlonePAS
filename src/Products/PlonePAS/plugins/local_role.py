# -*- coding: utf-8 -*-
"""
A Local Roles Plugin Implementation that respects Black Listing markers.

ie. containers/objects which denote that they do not wish to acquire local
roles from their containment structure.

"""
from AccessControl import ClassSecurityInfo
from Acquisition import aq_inner
from Acquisition import aq_parent
from App.class_init import InitializeClass
from App.special_dtml import DTMLFile
from Products.PlonePAS.interfaces.plugins import ILocalRolesPlugin
from Products.PluggableAuthService.plugins.LocalRolePlugin \
    import LocalRolePlugin
from zope.interface import implementer


def manage_addLocalRolesManager(dispatcher, id, title=None, RESPONSE=None):
    """
    add a local roles manager
    """
    lrm = LocalRolesManager(id, title)
    dispatcher._setObject(lrm.getId(), lrm)

    if RESPONSE is not None:
        RESPONSE.redirect('manage_workspace')

manage_addLocalRolesManagerForm = \
    DTMLFile('../zmi/LocalRolesManagerForm', globals())


@implementer(ILocalRolesPlugin)
class LocalRolesManager(LocalRolePlugin):
    """Class incorporating local role storage with
    PlonePAS-specific local role permission checking.
    """

    meta_type = "Local Roles Manager"
    security = ClassSecurityInfo()

    def __init__(self, id, title=None):
        self._id = self.id = id
        self.title = title

    # security.declarePrivate( 'getRolesInContext' )
    def getRolesInContext(self, user, object):
        user_id = user.getId()
        group_ids = user.getGroups()

        principal_ids = list(group_ids)
        principal_ids.insert(0, user_id)

        local = {}
        object = aq_inner(object)

        while 1:
            local_roles = getattr(object, '__ac_local_roles__', None)

            if local_roles and callable(local_roles):
                local_roles = local_roles()

            if local_roles:
                dict = local_roles

                for principal_id in principal_ids:
                    for role in dict.get(principal_id, []):
                        local[role] = 1

            inner = aq_inner(object)
            parent = aq_parent(inner)

            if getattr(object, '__ac_local_roles_block__', None):
                break

            if parent is not None:
                object = parent
                continue

            new = getattr(object, 'im_self', None)

            if new is not None:
                object = aq_inner(new)
                continue

            break

        return local.keys()

    # security.declarePrivate('checkLocalRolesAllowed')
    def checkLocalRolesAllowed(self, user, object, object_roles):
        # Still have not found a match, so check local roles. We do
        # this manually rather than call getRolesInContext so that
        # we can incur only the overhead required to find a match.
        inner_obj = aq_inner(object)
        user_id = user.getId()
        group_ids = user.getGroups()

        principal_ids = list(group_ids)
        principal_ids.insert(0, user_id)

        while 1:

            local_roles = getattr(inner_obj, '__ac_local_roles__', None)

            if local_roles and callable(local_roles):
                local_roles = local_roles()

            if local_roles:
                dict = local_roles

                for principal_id in principal_ids:
                    local_roles = dict.get(principal_id, [])

                    # local_roles is empty most of the time, where as
                    # object_roles is usually not.
                    if not local_roles:
                        continue

                    for role in object_roles:
                        if role in local_roles:
                            if user._check_context(object):
                                return 1
                            return 0

            inner = aq_inner(inner_obj)
            parent = aq_parent(inner)

            if getattr(inner_obj, '__ac_local_roles_block__', None):
                break

            if parent is not None:
                inner_obj = parent
                continue

            new = getattr(inner_obj, 'im_self', None)

            if new is not None:
                inner_obj = aq_inner(new)
                continue

            break

        return None

    def getAllLocalRolesInContext(self, context):
        roles = {}
        object = aq_inner(context)

        while True:

            local_roles = getattr(object, '__ac_local_roles__', None)

            if local_roles and callable(local_roles):
                local_roles = local_roles()

            if local_roles:

                dict = local_roles

                for principal, localroles in dict.items():
                    if principal not in roles:
                        roles[principal] = set()

                    roles[principal].update(localroles)

            inner = aq_inner(object)
            parent = aq_parent(inner)

            if getattr(object, '__ac_local_roles_block__', None):
                break

            if parent is not None:
                object = parent
                continue

            new = getattr(object, 'im_self', None)

            if new is not None:
                object = aq_inner(new)
                continue

            break

        return roles

InitializeClass(LocalRolesManager)
