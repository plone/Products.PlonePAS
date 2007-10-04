from itertools import chain

from zope.interface import implements
from Products.Five import BrowserView
from Products.CMFCore.utils import getToolByName
from Products.PlonePAS.interfaces.browser import IPASSearchView


class PASSearchView(BrowserView):
    implements(IPASSearchView)

    @staticmethod
    def extractCriteriaFromRequest(request):
        criteria=request.form.copy()

        for key in ["form.submitted", "submit"]:
            if key in criteria:
                del criteria[key]

        for (key, value) in criteria.items():
            if not value:
                del criteria[key]

        return criteria


    @staticmethod
    def merge(results, key):
        return dict([(result[key], result) for result in results]).values()


    @staticmethod
    def searchInFields(searchFunction, fields, value, **criteria):
        """Use `searchFunction` to find and return all the users/groups/whatever
        which have any field listed in `fields` matching `value` and also
        satisfy `criteria`. (If a field appears in both `criteria` and `fields`,
        the value in `criteria` trumps the one in `value`.)

        Will probably return lots of duplicates, so be sure to merge.
        """
        results = []
        for eachField in fields:
            results.append(searchFunction(**dict( [(eachField, value)] + criteria.items() )))
        return chain(*results)


    def sort(self, results, key):
        def key_func(a):
            return a.get(key, "").lower()
        results.sort(key=key_func)
        return results


    def searchUsers(self, sort_by=None, any_field=None, **criteria):
        self.pas=getToolByName(self.context, "acl_users")
        
        if any_field is None:
            results = self.pas.searchUsers(**criteria)
        else:
            results = self.searchInFields(self.pas.searchUsers, ['login', 'fullname'], any_field, **criteria)
        
        results=self.merge(results, "userid")
        if sort_by is not None:
            results=self.sort(results, sort_by)
        return results


    def searchUsersByRequest(self, request, sort_by=None):
        criteria=self.extractCriteriaFromRequest(request)
        return self.searchUsers(sort_by="userid", **criteria)


    def searchGroups(self, **criteria):
        self.pas=getToolByName(self.context, "acl_users")
        return self.pas.searchGroups(**criteria)


    def searchGroupsByRequest(self, request):
        criteria=self.extractCriteriaFromRequest(request)
        return self.searchGroups(**criteria)


    def getPhysicalPath(self):
        # We call various PAS methods which can be ZCached. The ZCache
        # infrastructure relies on getPhysicalPath on the context being
        # available, which this view does not have, it not being a
        # persistent object. So we fake things and return the physical path
        # for our context.
        return self.context.getPhysicalPath()
