"""
$Id: __init__.py,v 1.4 2005/02/01 02:42:40 webmaven Exp $
"""

from AccessControl.Permissions import add_user_folders
from Products.CMFCore.DirectoryView import registerDirectory
from Products.PluggableAuthService import registerMultiPlugin
import gruf

registerDirectory('skins', globals())
try:
    
    registerMultiPlugin( gruf.GRUFBridge.meta_type ) 
except RuntimeError:
    # make refresh users happy
    pass

def initialize(context):

    context.registerClass( gruf.GRUFBridge,
                           permission = add_user_folders,
                           constructors = ( gruf.manage_addGRUFBridgeForm,
                                            gruf.manage_addGRUFBridge ),
                           visibility = None
                           )


