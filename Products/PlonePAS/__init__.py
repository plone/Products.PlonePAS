"""
$Id: __init__.py,v 1.3 2005/02/01 01:20:16 k_vertigo Exp $
"""

from AccessControl.Permissions import add_user_folders
from Products.CMFCore.DirectoryView import registerDirectory
from Products.PluggableAuthService import registerMultiPlugin
import gruf

registerDirectory('skins', globals())
registerMultiPlugin( gruf.GRUFBridge.meta_type ) 

def initialize(context):

    context.registerClass( gruf.GRUFBridge,
                           permission = add_user_folders,
                           constructors = ( gruf.manage_addGRUFBridgeForm,
                                            gruf.manage_addGRUFBridge ),
                           visibility = None
                           )


