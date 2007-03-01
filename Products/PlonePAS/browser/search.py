from zope.interface import implements
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.utils import BrowserView, context
from Products.PlonePAS.interfaces.browser import IPASSearchView


class PASSearchView(BrowserView):
    implements(IPASSearchView)

    def __init__(self, context, request):
        super(PASSearchView, self).__init__(context, request)


    @staticmethod
    def extractCriteriaFromRequest(request):
        criteria=request.form.copy()

        for key in [ "form.submitted", "submit" ]:
            if key in criteria:
                del criteria[key]

        for (key, value) in criteria.items():
            if not value:
                del criteria[key]

        return criteria


    def searchUsers(self, **criteria):
        self.pas = getToolByName(context(self), "acl_users")
        return self.pas.searchUsers(**criteria)

    
    def searchUsersByRequest(self, request):
        criteria=self.extractCriteriaFromRequest(request)
        return self.searchUsers(**criteria)


    def searchGroups(self, **criteria):
        self.pas = getToolByName(context(self), "acl_users")
        return self.pas.searchGroups(**criteria)

    
    def searchGroupsByRequest(self, request):
        criteria=self.extractCriteriaFromRequest(request)
        return self.searchGroups(**criteria)
