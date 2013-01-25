from zope.component import getUtility
from zope.interface import implements
from zope.publisher.browser import BrowserView
from plone.memoize.instance import memoize

from Products.PlonePAS.interfaces.browser import IPASMemberView
from Products.PlonePAS.interfaces.membership import IMembershipTool


class PASMemberView(BrowserView):
    implements(IPASMemberView)

    @memoize
    def info(self, userid=None):
        pm = getUtility(IMembershipTool)
        result = pm.getMemberInfo(memberId=userid)
        if result is None:
            # No such member: removed?  We return something useful anyway.
            return {'username': userid, 'description': '', 'language': '',
                    'home_page': '', 'name_or_id': userid, 'location': '',
                    'fullname': ''}
        result['name_or_id'] = result.get('fullname') or \
            result.get('username') or userid
        return result
