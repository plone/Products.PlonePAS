"""
Minimalist GRUF Migration
"""

from Products.CMFCore.utils import getToolByName
from Install import install

def migrate(self):
    
    gruf = self.acl_users
    install( self )

    pas = self.acl_users
    pas.manage_addProduct['PlonePAS'].manage_addGRUFBridge(
        "gruf_bridge"
        )
    bridge = pas.gruf_bridge
    bridge.manage_delObject(['acl_users'])
    bridge._setObject('acl_users', gruf)
        

    return "GRUF Bridge Installed"
