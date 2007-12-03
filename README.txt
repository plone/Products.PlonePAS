PlonePAS

This product adapts the
"PluggableAuthService":http://svn.zope.org/PluggableAuthService/
for use by Plone.

Please see STATUS.txt for notes on the current version and whether or
not it will help you.

Versions

  - Currently targeted to Plone 3.0, and its standard dependencies.

Depends On

 - Plone standard products (esp. GRUF)

 - PluggableAuthService 1.0.5 (or later)

 - PluginRegistry (latest)

 - PasswordResetTool (latest)

Optional

 - PloneTestCase

 - LDAPUserFolder 2.6b3 or better

 - LDAPMultiPlugins 1.0 or better

PlonePAS installs like any other Plone Product, but please note: it
does replace your existing portal user folder. There is automatic
migration, but this is not tested against setups other than GRUF+ZODB
UserFolder. It may work for other userfolders or sources, but it will
end up storing all users in the ZODB, regardless of original user
source.

(For instance, an exUserFolder user source in GRUF that goes to a
database may be migrated, but will not be attached to the database
anymore. If you have plugins that will replicate your original
functionality, it will not hurt to simply delete the existing
plugins.)

But whatever you do, if you decide to install this Product, please,
please, please back up your site.  The authors cannot guarantee that
PlonePAS will not stomp your site into mush and then eat it.  You
should be doing this anyway, but it is especially important
here. Repeat

YOU MUST BACK UP BEFORE INSTALLATION.

And don't throw the backup away until you're really really sure that
PlonePAS works for you. Please note: there is no automatic restoration
on uninstall.

After installation, you may replace or reconfigure any of PAS's
plugins.

For reference, the standard install procedure:

  - Unpack the distribution file,

  - place the PlonePAS/ directory in your Zope instance's Products/
    directory,

  - restart Zope.

  - In each Plone instance, go to the QuickInstaller
    (portal_quickinstaller in ZMI, or "Add/Remove Products" in the
    Plone Setup) and install it.

Notes

  Why doesn't the title of my group, that I set in the ZODB, show up?
  The title for a group comes from the properties plugin. The info
  in the groups plugin isn't used, except for the name.

  The value of the 'title' property on the portal_groupdata or
  portal_memberdata tool will not be used as a default for the title
  of the group or member. This is to prevent UI confusion if a title
  is set without realizing the implications. To remove this special
  case, see 'plugins.property._getDefaultValues'.

  If PAS caching is enabled (see the "Cache" tab) and the cache
  manager does not have a 'cleanup' method (RAMCacheManager has one),
  then changes to the memberdata schema will not effect users already
  cached. In this case, restart the server or clear the cache (if
  possible) for the changes to take effect.

  Similarly, changes to the memberdata schema will not propagate to
  member objects already in use. If you have a memberdata object and
  change the memberdata properties you must re-construct the member by
  saying portal_membership.getMemberById again.  See
  'tests.test_properties.test_user_properties' for example.

  By default, logout from users signed in under HTTP Basic Auth cannot
  log out.  If you enable the "Credentials Reset" plugin for the HTTP
  Basic plugin, the logout for cookies will no longer work. However,
  this is not a problem if you're not using cookies.

Implementation

  In some places, PlonePAS acts as an adaptor to make PAS provide
  enough of GRUF's interface to satisfy Plone. All the monkey patches
  in pas.py, for instance, extend PAS with expected methods.

  PlonePAS also modifies Plone to work with PAS by providing
  partially-new implementations of several tools.  In the tools/
  directory you can see new tools for groups and members, as well as
  the utils tool.

  It also provides extra capabilties for PAS needed by plone, such as
  mutable property sheets, local role calculation, creation of group
  objects, and more.

Authorship

  Initial creation: The PAS CIGNEX Sprint Team [ Anders, Bob, Ben,
  Chad, Gautham, Joel, Kapil, Michel, Micheal ]

  Post-sprint work: J Cameron Cooper, Leo, Sidnei, Mark at "Enfold
  Systems":http://enfoldsystems.com

  Basic setAuthCookie support (to mimick CookieCrumbler):
  Rocky Burt at "ServerZen Software":http://www.serverzen.com

  Synced login process with Plone:
  Dorneles Tremea at "PloneSolutions":http://plonesolutions.com

  Bugfixes, various development and merging with Plone:
  Wichert Akkerman at Simplon

  (Add yourself if you work on it!)

Bug Reports

  Please report bugs to the PlonePAS issue tracker at
  http://plone.org/products/plonepas/issues
