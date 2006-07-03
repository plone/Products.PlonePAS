##############################################################################
#
# PlonePAS - Adapt PluggableAuthService for use in Plone
# Copyright (C) 2005 Enfold Systems, Kapil Thangavelu, et al
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
"""
This external method installs PAS as a plugin of GRUF.
"""

from Products.PlonePAS.Extensions.Install import activatePluginInterfaces
from Products.GroupUserFolder.GRUFFolders import GRUFUsers

def addPAS( gruf ):

    # how does GRUF suck let me count the ways... this is how you can
    # programatically add a user source to gruf

    # copied from gruf guts

    # Get the initial Users id
    ids = gruf.objectIds(GRUFUsers.meta_type)
    if ids:
        ids.sort()
        if ids == ['Users',]:
            last = 0
        else:
            last = int(ids[-1][-2:])
            next_id = "Users%02d" % (last + 1, )

        # Add the GRUFFolder object
        uf = GRUFFolder.GRUFUsers(id = next_id)
        gruf._setObject(next_id, uf)

    usource = gruf._getOb( next_id )
    usource.manage_addProduct['PluggableAuthService'].addPluggableAuthService()

def integrate( self ):

    out = StringIO()
    portal = getToolByName(self, 'portal_url').getPortalObject()

    print >> out, "Adding PAS as a GRUF User Source"
    addPAS( portal.acl_users )

    pas.manage_addProduct['PlonePAS'].manage_addUserManager('source_users')
    print >> out, "Added User Manager."
    activatePluginInterfaces(portal, 'source_users', out)

    pas.manage_addProduct['PlonePAS'].manage_addPloneUserFactory('user_factory')
    print >> out, "Added Plone User Factory."
    activatePluginInterfaces(portal, "user_factory", out)

    return out.getvalue()
