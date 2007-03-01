from zope.interface import implements
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.utils import BrowserView, context
from Products.PlonePAS.interfaces.browser import IPASSearchView


class PASSearchView(BrowserView):
    implements(IPASSearchView)

    def __init__(self, context, request):
        super(PASSearchView, self).__init__(context, request)


    def searchUsers(self, **criteria):
        self.pas = getToolByName(context(self), "acl_users")
        return self.pas.searchUsers(**criteria)

    
    def searchUsersByRequest(self, request):
        criteria=request.form.copy()

        for key in [ "form.submitted", "submit" ]:
            if key in criteria:
                del criteria[key]

        for (key, value) in criteria.items():
            if not value:
                del criteria[key]


        return self.searchUsers(**criteria)

