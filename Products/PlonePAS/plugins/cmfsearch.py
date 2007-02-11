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
import copy

from AccessControl import ClassSecurityInfo
from Products.CMFCore.utils import getToolByName
from Globals import InitializeClass
from OFS.Cache import Cacheable
from Products.PageTemplates.PageTemplateFile import PageTemplateFile

from Products.PluggableAuthService.interfaces.plugins \
    import IUserEnumerationPlugin

from Products.PluggableAuthService.permissions import ManageUsers
from Products.PluggableAuthService.plugins.BasePlugin import BasePlugin
from Products.PluggableAuthService.utils import classImplements
from Products.PluggableAuthService.utils import createViewName

manage_addCMFSearchForm = PageTemplateFile(
    '../zmi/CMFSearchForm', globals(), __name__='manage_addCMFSearchForm' )

def addCMFSearch( dispatcher, id, title=None, REQUEST=None ):
    """ Add a addCMFSearch to a Pluggable Auth Service. """

    zum = CMFSearch(id, title)
    dispatcher._setObject(zum.getId(), zum)

    if REQUEST is not None:
        REQUEST['RESPONSE'].redirect(
                                '%s/manage_workspace'
                                '?manage_tabs_message='
                                'CMFSearch+added.'
                            % dispatcher.absolute_url())

class CMFSearch ( BasePlugin, Cacheable ):

    """ PAS plugin for managing users in the ZODB.
    """

    meta_type = 'CMF Search plugin'

    security = ClassSecurityInfo()

    def __init__(self, id, title=None):

        self._setId(id)
        self.title = title

    def isStringType(data):
        return isinstance(data, str) or isinstance(data, unicode)#
        
    def getMemberData(self):
        """Return the MemberData storage.
        The MemberData is retrieved from the portal_memberdata tool.#
        """
        md = getToolByName(self, 'portal_memberdata')
        return md._members
        
    def testMemberData(self, memberdata, criteria, exact_match=False):
        """Test if a memberdata matches the search criteria.
        """
        for (key, value) in criteria.items():
            if key not in memberdata:
                return False
            testvalue=memberdata.getProperty(key)

            if isStringType(testvalue):
                testvalue=testvalue.lower()
            if isStringType(value):
                value=value.lower()
                
            if exact_match:
                if value!=testvalue:
                    return False
            else:
                if not isinstance(value, type(testvalue)):
                    return False
                if not isStringType(value):
                    return False
                if value not in testvalue:
                    return False
        return True

    security.declarePrivate('enumerateUsers')
    def enumerateUsers( self
                      , id=None
                      , login=None
                      , exact_match=False
                      , sort_by=None
                      , max_results=None
                      , **kw
                      ):

        """ See IUserEnumerationPlugin.
        """
        user_info = []
        user_ids = []
        plugin_id = self.getId()
        view_name = createViewName('enumerateUsers', id or login)

        # return empty list if there is anything from IDs or User Name 
        if kw:
            return []

        if isinstance( id, str ):
            id = [ id ]

        if isinstance( login, str ):
            login = [ login ]

        # Look in the cache first...
        keywords = copy.deepcopy(kw)
        keywords.update( { 'id' : id
                         , 'login' : login
                         , 'exact_match' : exact_match
                         , 'sort_by' : sort_by
                         , 'max_results' : max_results
                         }
                       )
        cached_info = self.ZCacheable_get( view_name=view_name
                                         , keywords=keywords
                                         , default=None
                                         )
        if cached_info is not None:
            return tuple(cached_info)

        memberdata=self.getMemberData()

        criteria=copy.copy(kw)
        if id is not None:
            criteria["id"]=id
        if login is not None:
            criteria["login"]=login
        
        user_ids=[user_id for (user_id,data) in memberdata.items()
                  if self.testMemberData(data, criteria, exact_match)]

        for user_id in user_ids:
            info = { 'id' : self.prefix + user_id
                     , 'login' : user_id
                     , 'pluginid' : plugin_id
                 } 
            if not user_filter or user_filter( info ):
                user_info.append( info )

        # Put the computed value into the cache
        self.ZCacheable_set(user_info, view_name=view_name, keywords=keywords)

        return tuple( user_info )

classImplements( CMFSearch
                , IUserEnumerationPlugin
               )

InitializeClass( CMFSearch )
