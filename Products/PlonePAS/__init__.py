"""
$Id: __init__.py,v 1.13 2005/02/16 23:52:10 k_vertigo Exp $
"""

from AccessControl.Permissions import add_user_folders
from Products.CMFCore.DirectoryView import registerDirectory
from Products.PluggableAuthService import registerMultiPlugin
from Products.CMFPlone import PloneUtilities as plone_utils

#################################
# plugins
from plugins import GRUFBridge
from plugins import UserManager
from plugins import GroupManager
from plugins import GroupAwareRoleManager
from plugins import LocalRolesManager
from plugins import PloneUserFactory
#################################
# pas monkies
import pas                              

#################################
# plone monkies
import plone

#################################
# new groups tool
from tools.groups import GroupsTool


registerDirectory('skins', globals())


#################################
# register plugins with pas
try:
    registerMultiPlugin( GRUFBridge.GRUFBridge.meta_type )
    registerMultiPlugin( UserManager.UserManager.meta_type )
    registerMultiPlugin( GroupManager.GroupManager.meta_type )    
    registerMultiPlugin( GroupAwareRoleManager.GroupAwareRoleManager.meta_type )
    registerMultiPlugin( LocalRolesManager.LocalRolesManager.meta_type )
    registerMultiPlugin( PloneUserFactory.PloneUserFactory.meta_type )
    
except RuntimeError:
    # make refresh users happy
    pass

def initialize(context):

    tools = ( GroupsTool, )

    plone_utils.ToolInit('PlonePAS Tools',
                         tools=tools,
                         product_name='PlonePAS',
                         icon='tool.gif',
                         ).initialize(context)
                         
    
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

    context.registerClass( GroupManager.GroupManager,
                           permission = add_user_folders,
                           constructors = ( GroupManager.manage_addGroupManagerForm,
                                            GroupManager.manage_addGroupManager ),
                           visibility = None
                           )                           

    context.registerClass( PloneUserFactory.PloneUserFactory,
                           permission = add_user_folders,
                           constructors = ( PloneUserFactory.manage_addPloneUserFactoryForm,
                                            PloneUserFactory.manage_addPloneUserFactory ),
                           visibility = None
                           )                           
