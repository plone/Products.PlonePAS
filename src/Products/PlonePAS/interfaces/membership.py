# -*- coding: utf-8 -*-
from Products.CMFCore import interfaces


class IMembershipTool(interfaces.IMembershipTool):

    def getMemberInfo(memberId=None):
        """Return 'harmless' Memberinfo of any member, such as full name,
        location, etc
        """

__all__ = (IMembershipTool, )
