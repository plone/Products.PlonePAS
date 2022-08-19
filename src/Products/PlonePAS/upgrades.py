"""
Upgrade steps specific to Plone's use of PAS.
"""

from Products.PlonePAS.plugins import cookie_handler
from Products.PluggableAuthService.plugins import CookieAuthHelper

import logging


logger = logging.getLogger(__name__)


def from4to5_fix_zope_root(context):
    """
    Fix broken Zope root `/acl_users/` plugins.
    """
    root = context.getPhysicalRoot()
    pas = root.acl_users.manage_addProduct["PluggableAuthService"]
    # Identify which interfaces should be considered PAS plugin interfaces
    plugin_ifaces = [
        plugin_type_info["interface"]
        for plugin_type_info in root.acl_users.plugins.listPluginTypeInfo()
    ]
    broken_meta_type = cookie_handler.ExtendedCookieAuthHelper.meta_type
    broken_plugins = root.acl_users.objectValues(broken_meta_type)
    for broken_plugin in broken_plugins:
        # Collect properties from old/broken plugin
        kwargs = dict(
            id=broken_plugin.id,
            title=broken_plugin.title,
            cookie_name=broken_plugin.cookie_name,
        )
        # Which PAS plugin interfaces has this plugin been activated for
        active_ifaces = [
            plugin_iface
            for plugin_iface in plugin_ifaces
            if plugin_iface.providedBy(broken_plugin)
            and broken_plugin.id in root.acl_users.plugins.listPluginIds(plugin_iface)
        ]
        # Delete the old/broken plugin
        logger.info(
            "Deleting broken %r plugin: %r",
            broken_meta_type,
            "/".join(broken_plugin.getPhysicalPath()),
        )
        root.acl_users.manage_delObjects([broken_plugin.id])
        # Add the correct plugin
        logger.info(
            "Adding working %r plugin: %r",
            CookieAuthHelper.CookieAuthHelper.meta_type,
            "/".join(broken_plugin.getPhysicalPath()),
        )
        pas.addCookieAuthHelper(**kwargs)
        # Restore activated plugin interfaces
        for plugin_iface in active_ifaces:
            root.acl_users.plugins.activatePlugin(
                plugin_iface,
                kwargs["id"],
            )
