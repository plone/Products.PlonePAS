"""
$Id: __init__.py,v 1.10 2005/02/04 07:56:59 k_vertigo Exp $
"""

from AccessControl.Permissions import add_user_folders
from Products.CMFCore.DirectoryView import registerDirectory
from Products.PluggableAuthService import registerMultiPlugin

from plugins import GroupAwareRoleManager
from plugins import GRUFBridge
from plugins import UserManager    # plugins
import pas                              # pas monkies

registerDirectory('skins', globals())

try:
    registerMultiPlugin( GRUFBridge.GRUFBridge.meta_type )
    registerMultiPlugin( UserManager.UserManager.meta_type )
    registerMultiPlugin( GroupAwareRoleManager.GroupAwareRoleManager.meta_type )
except RuntimeError:
    # make refresh users happy
    pass

def initialize(context):
    context.registerClass( GroupAwareRoleManager.GroupAwareRoleManager,
                           permission = add_user_folders,
                           constructors = ( GroupAwareRoleManager.manage_addGroupAwareRoleManagerForm,
                                            GroupAwareRoleManager.manage_addGroupAwareRoleManager ),
                           visibility = None
                           )
    
    context.registerClass( GRUFBridge.GRUFBridge,
                           permission = add_user_folders,
                           constructors = ( GRUFBridge.manage_addGRUFBridgeForm,
                                            GRUFBridge.manage_addGRUFBridge ),
                           visibility = None
                           )

    context.registerClass( UserManager.UserManager,
                           permission = add_user_folders,
                           constructors = ( UserManager.manage_addUserManagerForm,
                                            UserManager.manage_addUserManager ),
                           visibility = None
                           )
