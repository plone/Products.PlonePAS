"""
$Id: __init__.py,v 1.8 2005/02/03 00:09:46 k_vertigo Exp $
"""

from AccessControl.Permissions import add_user_folders
from Products.CMFCore.DirectoryView import registerDirectory
from Products.PluggableAuthService import registerMultiPlugin

from plugins import GRUFBridge          # plugins
from plugins import PloneUserManager    # plugins
import pas                              # pas monkies

registerDirectory('skins', globals())

try:
    registerMultiPlugin( GRUFBridge.GRUFBridge.meta_type )
    registerMultiPlugin( PloneUserManager.PloneUserManager.meta_type )
except RuntimeError:
    # make refresh users happy
    pass



def initialize(context):
    context.registerClass( GRUFBridge.GRUFBridge,
                           permission = add_user_folders,
                           constructors = ( GRUFBridge.manage_addGRUFBridgeForm,
                                            GRUFBridge.manage_addGRUFBridge ),
                           visibility = None
                           )

    context.registerClass( PloneUserManager.PloneUserManager,
                           permission = add_user_folders,
                           constructors = ( PloneUserManager.manage_addPloneUserManagerForm,
                                            PloneUserManager.addPloneUserManager ),
                           visibility = None
                           )
