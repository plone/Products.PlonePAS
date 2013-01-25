from Products.CMFCore.interfaces import IMembershipTool


class IMembershipTool(IMembershipTool):

    def getMemberInfo(memberId=None):
        """Return 'harmless' Memberinfo of any member, such as full name,
        location, etc
        """

__all__ = (IMembershipTool, )
