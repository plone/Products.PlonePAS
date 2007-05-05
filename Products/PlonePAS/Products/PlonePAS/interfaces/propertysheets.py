##############################################################################
#
# PlonePAS - Adapt PluggableAuthService for use in Plone
# Copyright (C) 2005 Enfold Systems, Kapil Thangavelu, et al
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this
# distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################


from Products.PluggableAuthService.interfaces.propertysheets \
    import IPropertySheet

class IMutablePropertySheet( IPropertySheet ):


    def canWriteProperty( object, id ):
        """ Check if a property can be modified.
        """

    def setProperty( object, id, value ):
        """
        """

    def setProperties( object, mapping ):
        """
        """

class ISchemaMutablePropertySheet( IMutablePropertySheet ):
    pass
