"""
Minimalist GRUF Migration
"""
from StringIO import StringIO
from Products.CMFCore.utils import getToolByName
from Install import install, activatePluginInterfaces

def migrate(self):
    """
    """
    gruf = self.acl_users
    out = StringIO()

    log = install( self )
    out.write( log )

    pas = self.acl_users
    pas.manage_addProduct['PlonePAS'].manage_addGRUFBridge(
        "gruf_bridge"
        )

    bridge = pas.gruf_bridge
    bridge.manage_delObject(['acl_users'])
    bridge._setObject('acl_users', gruf)
    self.__allow_groups__ = pas


    return "GRUF Bridge Installed"
