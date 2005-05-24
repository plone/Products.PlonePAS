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
