# -*- coding: utf-8 -*-
from Products.CMFCore.utils import getToolByName
from Products.PlonePAS.interfaces.browser import IPASMemberView
from plone.memoize.instance import memoize
from zope.interface import implementer
from zope.publisher.browser import BrowserView


@implementer(IPASMemberView)
class PASMemberView(BrowserView):

    @memoize
    def info(self, userid=None):
        pm = getToolByName(self.context, 'portal_membership')
        result = pm.getMemberInfo(memberId=userid)
        if result is None:
            # No such member: removed?  We return something useful anyway.
            return {
                'username': userid,
                'description': '',
                'language': '',
                'home_page': '',
                'name_or_id': userid,
                'location': '',
                'fullname': ''
            }
        result['name_or_id'] = result.get('fullname') or \
            result.get('username') or userid
        return result
