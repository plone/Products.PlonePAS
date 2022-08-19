from Products.PluggableAuthService.interfaces.propertysheets import IPropertySheet


class IMutablePropertySheet(IPropertySheet):
    def canWriteProperty(object, id):
        """Check if a property can be modified."""

    def setProperty(object, id, value):
        """ """

    def setProperties(object, mapping):
        """ """


class ISchemaMutablePropertySheet(IMutablePropertySheet):
    pass
