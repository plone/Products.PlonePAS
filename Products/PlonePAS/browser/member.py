from plone.memoize.instance import memoize
from zope.interface import implements
from zope.publisher.browser import BrowserView

from AccessControl.SecurityManagement import getSecurityManager
from AccessControl.User import nobody
from Products.CMFCore.utils import _getAuthenticatedUser
from Products.CMFCore.utils import getToolByName

from Products.PlonePAS.interfaces.browser import IPASMemberView


class PASMemberView(BrowserView):
    implements(IPASMemberView)

    @memoize
    def info(self, userid=None):
        if userid is None:
            userid = getSecurityManager().getUser()
            if userid is None:
                userid = nobody

        pm = getToolByName(self.context, 'portal_membership')
        result = pm.getMemberInfo(memberId=userid)
        name = result.get('fullname')
        if not name:
            name = userid
        result['name_or_id'] = name
        return result
