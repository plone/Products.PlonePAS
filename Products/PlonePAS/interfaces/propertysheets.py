##############################################################################
#
# Copyright (c) 2005 Kapil Thangavelu
# Reserved.
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


    def setProperty(  id, value ):
        """
        """

    def setProperties( mapping ):
        """
        """
        
    def _getPropertyProvider( context ):
        """
        return the property provider that was the origin for this property
        sheet.
        """
        

class ISchemaMutablePropertySheet( IMutablePropertySheet ):
    pass
        
        
