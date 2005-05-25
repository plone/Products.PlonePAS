PlonePAS

This product adapts the
"PluggableAuthService":http://cvs.zope.org/Products/PluggableAuthService/
for use by Plone.

Please see STATUS.txt for notes on the current version and whether or
not it will help you.

PlonePAS installs like any other Plone Product, but please note: it
does destroy your existing portal user folder. There is automatic
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

  Making it work: J Cameron Cooper, Leo, Sidnei, Mark at "Enfold
  Systems":http://enfoldsystems.com

Bug Reports

  Please report bugs to plonepas@jcameroncooper.com, or to the PAS
  mailing list.
