"""
$Id: __init__.py,v 1.9 2005/02/03 19:28:42 k_vertigo Exp $
"""

from AccessControl.Permissions import add_user_folders
from Products.CMFCore.DirectoryView import registerDirectory
from Products.PluggableAuthService import registerMultiPlugin

from plugins import GroupAwareRoleManager
from plugins import GRUFBridge
from plugins import PloneUserManager    # plugins
import pas                              # pas monkies

registerDirectory('skins', globals())

try:
    registerMultiPlugin( GRUFBridge.GRUFBridge.meta_type )
    registerMultiPlugin( PloneUserManager.PloneUserManager.meta_type )
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

    context.registerClass( PloneUserManager.PloneUserManager,
                           permission = add_user_folders,
                           constructors = ( PloneUserManager.manage_addPloneUserManagerForm,
                                            PloneUserManager.addPloneUserManager ),
                           visibility = None
                           )
