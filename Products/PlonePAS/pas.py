"""
pas alterations and monkies
$Id: pas.py,v 1.1 2005/02/01 19:28:31 k_vertigo Exp $
"""

from Products.PluggableAuthService.PluggableAuthService import PluggableAuthService

# give pas the userfolder public api
PluggableAuthService.userFolderAddUser = PluggableAuthService._doAddUser

