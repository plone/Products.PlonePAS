"""
$Id: __init__.py,v 1.14 2005/02/24 15:13:31 k_vertigo Exp $
"""

from AccessControl.Permissions import add_user_folders
from Products.CMFCore.DirectoryView import registerDirectory
from Products.PluggableAuthService import registerMultiPlugin
from Products.CMFPlone import PloneUtilities as plone_utils

import config

#################################
# plugins
from plugins import gruf
from plugins import user
from plugins import group
from plugins import role
from plugins import local_role
from plugins import ufactory

#################################
# pas monkies
import pas                              

#################################
# pas monkies 2 play w/ gruf
if config.PAS_INSIDE_GRUF:
    import gruf_support

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
    registerMultiPlugin( gruf.GRUFBridge.meta_type )
    registerMultiPlugin( user.UserManager.meta_type )
    registerMultiPlugin( group.GroupManager.meta_type )    
    registerMultiPlugin( role.GroupAwareRoleManager.meta_type )
    registerMultiPlugin( local_role.LocalRolesManager.meta_type )
    registerMultiPlugin( ufactory.PloneUserFactory.meta_type )
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
                         
    
    context.registerClass( role.GroupAwareRoleManager,
                           permission = add_user_folders,
                           constructors = ( GroupAwareRoleManager.manage_addGroupAwareRoleManagerForm,
                                            GroupAwareRoleManager.manage_addGroupAwareRoleManager ),
                           visibility = None
                           )
    
    context.registerClass( gruf.GRUFBridge,
                           permission = add_user_folders,
                           constructors = ( GRUFBridge.manage_addGRUFBridgeForm,
                                            GRUFBridge.manage_addGRUFBridge ),
                           visibility = None
                           )

    context.registerClass( user.UserManager,
                           permission = add_user_folders,
                           constructors = ( UserManager.manage_addUserManagerForm,
                                            UserManager.manage_addUserManager ),
                           visibility = None
                           )

    context.registerClass( group.GroupManager,
                           permission = add_user_folders,
                           constructors = ( GroupManager.manage_addGroupManagerForm,
                                            GroupManager.manage_addGroupManager ),
                           visibility = None
                           )                           

    context.registerClass( ufactory.PloneUserFactory,
                           permission = add_user_folders,
                           constructors = ( PloneUserFactory.manage_addPloneUserFactoryForm,
                                            PloneUserFactory.manage_addPloneUserFactory ),
                           visibility = None
                           )                           
