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
acceptable_user_sources = ("User Folder","LDAPUserFolder")
#acceptable_group_sources = ("User Folder","LDAPGroupFolder")
acceptable_group_sources = ("User Folder",)

def canAutoMigrate(userfolder):
    """Determine if a userfolder is set up so that it can be
    auto-migrated to PAS.

    Currently only true for GRUF with either UserFolder or
    LDAPUserFolder sources.
    """
    retval = 1
    if userfolder.meta_type == "Group User Folder":
        user_sources = userfolder.listUserSources()
        group_source = userfolder.Groups.acl_users

        retval = retval and group_source.meta_type in acceptable_group_sources
        for uf in user_sources:
            retval = retval and uf.meta_type in acceptable_user_sources
    else:
        retval = 0
    return retval
