##############################################################################
#
# Copyright (c) 2001 Zope Corporation and Contributors. All Rights
# Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this
# distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
""" Classes: PloneUserManager

$Id: PloneUserManager.py,v 1.1 2005/02/02 00:10:36 whit537 Exp $
"""
from AccessControl import ClassSecurityInfo, AuthEncoding
from AccessControl.SecurityManagement import getSecurityManager
from App.class_init import default__class_init__ as InitializeClass
from OFS.Cache import Cacheable

from Products.PluggableAuthService.plugins import ZODBUserManager
from Products.PluggableAuthService.plugins.ZODBUserManager import ZODBUserManager as BasePlugin
from Products.PluggableAuthService.interfaces.plugins import \
    IAuthenticationPlugin, IUserEnumerationPlugin
from Products.PlonePAS.interfaces.plugins import IUserDeleterPlugin

from Globals import DTMLFile
manage_addPloneUserManagerForm = DTMLFile('zmi/PloneUserManagerForm', globals())

def addPloneUserManager( dispatcher, id, title=None, REQUEST=None ):
    """ Add a PloneUserManager to a Pluggable Auth Service. """

    pum = PloneUserManager(id, title)
    dispatcher._setObject(pum.getId(), pum)

    if REQUEST is not None:
        REQUEST['RESPONSE'].redirect(
                                '%s/manage_workspace'
                                '?manage_tabs_message='
                                'PloneUserManager+added.'
                            % dispatcher.absolute_url())

class PloneUserManager( BasePlugin, Cacheable ):

    """ PAS plugin for managing users in Plone. (adds deletion
    API) """
    __implements__ = BasePlugin.__implements__ + (IUserDeleterPlugin,)

    meta_type = 'Plone User Manager'

    security = ClassSecurityInfo()

    def doDelUser(self, login):
        """ given a login, delete a user """
        self.removeUser(login)


InitializeClass( PloneUserManager )