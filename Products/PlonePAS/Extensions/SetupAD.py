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
import Products.LDAPMultiPlugins

# note: need to import ADSI instead, and also decide what params we allow

def setupADSI(portal):
    """Create appropriate plugins to replace destroyed LDAP user
    folders.
    """
    print >> out, "\nSet up ADSI Multiplugin:"
    pas = portal.acl_users

    id = 'adsi_multi%s' % x
    title = 'ADSI Multi-plugin %s' % x
    LDAP_server = lduf.LDAP_server + ":" + `lduf.LDAP_port`
    login_attr = lduf._login_attr
    uid_attr = lduf._uid_attr
    users_base = lduf.users_base
    users_scope = lduf.users_scope
    roles = lduf._roles
    groups_base = lduf.groups_base
    groups_scope = lduf.groups_scope
    binduid = lduf._binduid
    bindpwd = lduf._bindpwd
    binduid_usage = lduf._binduid_usage
    rdn_attr = lduf._rdnattr
    local_groups = lduf._local_groups
    use_ssl = lduf._conn_proto == 'ldaps'
    encryption = lduf._pwd_encryption
    read_only = lduf.read_only

    # attribute over-rides
    uid_attr = login_attr = "sAMAccountName"

    ldapmp = pas.manage_addProduct['LDAPMultiPlugins']
    ldapmp.manage_addActiveDirectoryMultiPlugin(
                id, title,
                LDAP_server, login_attr,
                uid_attr, users_base, users_scope, roles,
                groups_base, groups_scope, binduid, bindpwd,
                binduid_usage=1, rdn_attr='cn', local_groups=0,
                use_ssl=0 , encryption='SHA', read_only=0)
    getattr(pas,id).groupid_attr = 'cn'

    print >> out, "Added ActiveDirectoryMultiPlugin %s" % x

    activatePluginInterfaces(portal, id, out)
    # turn off groups
    pas.plugins.deactivatePlugin(IGroupsPlugin, id)
    pas.plugins.deactivatePlugin(IGroupEnumerationPlugin, id)
    # move properties up
    pas.plugins.movePluginsUp(IPropertiesPlugin, [id])
