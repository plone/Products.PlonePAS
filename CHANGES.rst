Changelog
=========

.. You should *NOT* be adding new change log entries to this file.
   You should create a file in the news directory instead.
   For helpful instructions, please see:
   https://github.com/plone/plone.releaser/blob/master/ADD-A-NEWS-ITEM.rst

.. towncrier release notes start

8.0.0 (2023-04-06)
------------------

Breaking changes:


- Remove `ldapmp` module. It is not being tested in Plone 6.
  See https://github.com/plone/Products.PlonePAS/pull/71#pullrequestreview-1351349950
  [gforcada] (#1)


Internal:


- Update configuration files.
  [plone devs] (80cf330f)


7.0.0 (2022-12-02)
------------------

Bug fixes:


- Final release for Plone 6.0.0 (#600)


7.0.0b3 (2022-10-11)
--------------------

Bug fixes:


- Fix admin password used in tests. [davisagli] (#70)


7.0.0b2 (2022-10-03)
--------------------

New features:


- Increase the minimum password length to 8 characters. [davisagli] (#69)


7.0.0b1 (2022-08-31)
--------------------

Bug fixes:


- Apply `isort`, `black`, `pyupgrade` and manual removal of six leftovers.
  Fix `PIL` deprecation warning, assume `PIL` is always there.
  Make `mypy` happy again.
  [jensens] (#68)


7.0.0a3 (2022-03-09)
--------------------

New features:


- Add separate `GenericSetup` profile to switch the Zope root `/acl_users` to use a simple
  cookie login form.  Useful when Zope root login and logout need to synchronize
  authentication state between multiple plugins, which is not possible with HTTP `Basic
  ...` authentication. [rpatterson] (#65) (zope-root-cookie)


7.0.0a2 (2021-12-29)
--------------------

Bug fixes:


- Fixed deprecation warning for ``AccessControl.AuthEncoding``.
  [maurits] (#64)
- Fix broken Zope root `/acl_users` cookie plugin on `PlonePAS` install.
  [rpatterson] (#65)


7.0.0a1 (2021-07-28)
--------------------

Breaking changes:


- Drop support for Plone 5.2 and Python 2.7.
  [maurits] (#61)


Bug fixes:


- Support for Pillow 8. [jensens] (#61)
- Fixed tests for cookie auth to also work with `zope.interface` 5.3.0.
  This uses simpler representations for interfaces.
  Tests now pass with earlier and later versions.
  [maurits] (#237)


6.0.7 (2021-02-16)
------------------

Bug fixes:


- Fixes deprection message: `AccessControl.User has moved to AccessControl.users`.
  [jensens] (#59)


6.0.6 (2020-04-23)
------------------

Bug fixes:


- Minor packaging updates. (#1)


6.0.5 (2019-12-10)
------------------

Bug fixes:


- - Notify CredentialsUpdated event when password is changed
    [ezvirtual] (#33)


6.0.4 (2019-12-02)
------------------

Bug fixes:


- - Notify PropertiesUpdated event when member properties are changed
    [ezvirtual]

  - Add simple test for PropertiesUpdated event
    [ezvirtual] (#27)


6.0.3 (2019-11-25)
------------------

Bug fixes:


- Log exception from PAS logout() instead of swallowing them
  [ajung] (#50)
- Fix deprecated imports.
  Fix buildout infrastructure for Plone 5.2.
  [thet] (#51)
- Create the MemberData object from an adapter instead of directly instantiating it, as intended in Products.CMFCore.MemberDataTool.
  This allows for better extensibility.
  [thet] (#52)


6.0.2 (2019-04-29)
------------------

Bug fixes:


- Avoid ResourceWarning messages.
  [gforcada] (#47)


6.0.1 (2018-12-11)
------------------

Bug fixes:


- Change `im_self` to `__self__` [vangheem] (#43)


6.0.0 (2018-11-05)
------------------

Breaking changes:

- Adapt to changes of MemberData in CMFCore.
  Fixes https://github.com/plone/Products.PlonePAS/issues/24
  [pbauer]

New features:

- Make it work in Python 3:
  Make imports work.
  Fix startup.
  Fix setting the auth-cookie.
  Fix assignment of MemberData-functions during startup.
  User properties are text.
  Fix scaling user profile.
  Migrate all tests away from PloneTestCasei.
  Fix other tests.
  [pbauer]

Bug fixes:

- InitializeClass was moved to AccessControl.class_init
  [jensens]

- setDefaultRoles is deprecated.
  addPermission from AccessControl.Permission is used.
  [jensens]

- Removed ``Extensions/Install.py`` which had only backwards compatibility imports.
  [maurits]

- Report home_page as empty when it is suspicious.
  It may for example contain javascript.
  Part of PloneHotfix20171128.
  [maurits]

- Remove setAuthCookie script. #1801
  This used to be a hook to allow overriding the credentials update. The
  default override has been used as the new implementation.
  [tlotze]


5.0.14 (2017-05-09)
-------------------

Bug fixes:

- Remove WarningInterceptor (CMFCore) - it is gone in newer versions.
  [jensens]


5.0.13 (2016-11-09)
-------------------

Bug fixes:

- In getMemberInfo, if a property is not present it now returns an
  empty string, rather than raising an exception. This fixes login for
  sites that have location removed.
  [MatthewWilkes]


5.0.12 (2016-09-09)
-------------------

Bug fixes:

- Depend on plone.protect 2.0.3 or higher.
  Fixes https://github.com/plone/Products.PlonePAS/issues/21
  [maurits]


5.0.11 (2016-05-20)
-------------------

Bug fixes:

- Use the _marker from CMFCore for MemberDataTool.getProperty,
  this makes sure that we never return the _marker from PlonePAS
  but an error.
  [pcdummy]

- Don't raise an ValueError if a property doesn't exists for a ZOPE
  user.
  [pcdummy]


5.0.10 (2016-05-02)
-------------------

Fixes:

- Fix UnicodeDecodeError in searchForMembers by using safe_unicode.
  [pbauer]


5.0.9 (2016-03-03)
------------------

New:

- Notify new IGroupDeletedEvent when deleting a group.
  [DieKatze]


5.0.8 (2016-02-24)
------------------

Fixes:

- Let ``cleanId`` return a string when getting a unicode.  [maurits]

- Fixed AttributeError with Python 2.6 when reading setup.py.  [maurits]


5.0.7 (2016-01-08)
------------------

Fixes:

- Fixed typo in documentation.  [gforcada]


5.0.6 (2015-12-16)
------------------

Fixes:

- bring back Python 2.6 support (in 2.6 depend on orderedict) and import
  conditional with fallback.
  [gforcada, jensens]


5.0.5 (2015-12-08)
------------------

Fixes:

- Applied Hotfix 2015-12-08.


5.0.4 (2015-09-20)
------------------

- Removed tests for non-utf-8 encodings.
  [esteele]


5.0.3 (2015-07-18)
------------------

- Allow to set a property to None.
  [ebrehault]


5.0.2 (2015-05-04)
------------------

- Prevent CRSF protecting errors when logging out because of
  Zope2 write on read issues
  [vangheem]

- Reduce logging level for while patching from info down to debug.
  [jensens]


5.0.1 (2015-03-21)
------------------

- Add a integrated test setup with codeanalysis and travis. For this moved
  ``Products`` folder to a ``src`` folder in order to follow the package
  structure expected by ``buildout.plonetest``'s ``qa.cfg``.
  [jensens]

- Make patching of LDAPMultiPlugin explicit. Code using those must call
  ``Products.PlonePAS.ldapmp.patch_ldapmp`` with no parameters in order
  to activate the patches.
  [jensens]

- Removed (optional) Archetypes Storage (used in past with CMFMember, which
  itself was long time ago superseded by Membrane). Probably dead code. If
  there's someone out there needing it in Plone 5 please copy the code from
  git/Plone4 in your addon/project.
  [jensens]

- Moved ``Extensions/Install.py`` functions to setuphandlers, kept BBB import
  for ``activatePluginInterfaces`` since this is imported by ``borg.localrole``.
  [jensens]

- Expect Python 2.7 with ``collections.OrderedDict``.
  [jensens]

- Remove nasty dependency to Products.CMFDefault.
  [jensens]

- Cleanup patches, allow introspection by using wrap_method, add roles using wrap_method,
  add deprecation and merge ``gruf_support.py`` in ``pas,py`` to have a better overview
  what is patched.
  [jensens]

- Cleanup: PEP8 et all, zca decorators, rough code review
  [jensens]

- In searchForMembers, ensure that request parameters are properly
  decoded to unicode
  [do3cc]


5.0 (2014-04-05)
----------------

- Do not write member data on read
  [vangheem]

- Allow ``properties`` to be passed to ``PloneUser.setProperties``.
  This was previously ignored as ``setProperties`` solely utilised
  keyword arguments.
  [davidjb]


4.1.2 (2014-01-27)
------------------

- Don't try to migrate the root user folder if the portal has no parent.
  [davisagli]

- Use batteries included odict implementation in favour of homegrown one.
  [tomgross]

- Use correct methods for getting users from id or names
  [tomgross]

- Ported tests to plone.app.testing
  [tomgross]

4.1.1 (2013-03-05)
------------------

- Fix a bug in setSecurityProfile where the login name was passed
  instead of the user id.
  [davisagli]

- Added empty updateUser and updateEveryLoginName methods in
  ZODBMutablePropertyProvider to fulfill the new standards of the
  IUserEnumerationPlugin.
  [maurits]


4.1 (2013-01-01)
----------------

- Fix assignRoleToPrincipal to work with new Products.PluggableAuthService 1.10.0.
  [maurits]

- Fix saving, getting and deleting the user portrait for non-standard
  user ids like 'bob-jones' or 'bob-jones+test@example.org'.
  [maurits]

- Fix the test for the current password if the user id differs from
  the login name.
  [maurits]


4.1a2 (2012-08-29)
------------------

- Bug fix: User with e-mail login got 'Insufficient Privileges' when
  trying to delete own portrait. Fixes http://dev.plone.org/ticket/12819.
  [patch by kagesenshi, applied by kleist]

- MembershipTool.searchForMembers() now preserves sort order.
  Fixes http://dev.plone.org/ticket/11716.
  [patch by neaj, applied by kleist]

- Changed deprecated getSiteEncoding to hardcoded `utf-8`
  [tom_gross]


4.1a1 (2012-06-29)
------------------

- Allow members with usernames that contain special characters
  (such as @ when use email to login), set their own member portrait
  [erral]

- PEP8 Cleanup
  [pbdiode]

- Add a default password validation policy as PAS plugin,
  see http://dev.plone.org/ticket/10959

- Extensions/Install.py: Don't use list as default argument value
  to activatePluginInterfaces()
  [patch by rossp, applied by kleist]


4.0.13 (2012-05-07)
-------------------

- Require ListPortalMembers permission for searchForMembers
  so anonymous users can not get a list of site users.
  [vangheem]


4.0.12 (2012-04-09)
-------------------

- Make sure that during registration you can change your member
  portrait (if this has been enabled the member registration config).
  Refs http://dev.plone.org/ticket/5432
  [maurits]


4.0.11 (2012-02-08)
-------------------

- Do some more checks when changing or deleting a member portrait.
  Fixes http://dev.plone.org/ticket/5432
  [maurits]

- Pass request along to getGroupsForPrincipal for caching purposes.
  [esteele]


4.0.10 (2012-01-04)
-------------------

- Fixed typo in method name hasOpenIDExtractor, keeping the old name
  (hasOpenIDdExtractor) around for backwards compatibility.
  Fixes http://dev.plone.org/ticket/11040
  [maurits]


4.0.9 (2011-11-24)
------------------

- Avoid a failure when we try to add a role to principal that is managed by
  an other plugin.
  [thomasdesvenain]

- Cleaned up and reduced dependencies. New extra ``atstorage`` for the rare case
  someone uses PlonePAS w/o Plone but with Archetypes (if this is this
  possible). [jensens]

4.0.8 - 2011-06-30
------------------

- Fire IPrincipalDeleted when a user is deleted.
  [stefan, ggozad]

4.0.7 - 2011-05-12
------------------

- Copy in CleanupTemp from CMFCore as it has been removed from CMFCore 2.3.
  [elro]

- Move import step to be registered in ZCML rather than XML.
  Remove the non-existent dependency on `plonepas-content`.
  [kiorky]

4.0.6 - 2011-02-25
------------------

- Fix missing and broken security declarations.
  [davisagli]

4.0.5 - 2011-02-14
------------------

- Avoid breaking on startup if PIL isn't present.
  [davisagli]

- Use 'defaultUser.png' as the default user portrait, since the .gif version
  has been deprecated for a long time now. See
  http://dev.plone.org/plone/changeset/36350
  [mj]

4.0.4 - 2011-01-03
------------------

- Remove plone.openid dependency in setup.py, import errors are already caught
  in PASInfoView.
  [elro]

- The code to search by id in mutable_properties.enumerateUsers didn't work at
  all, an exception was always raised and it was actually a good thing.
  We tried to implement it in 3.10 and we had strange listing in Plone UI. Then
  we reverted it in the next version so the behavior was backward compatible
  with previous versions.
  If we allow search by id, we can potentially break other part of the code. For
  example acl_users/portal_role_manager/manage_roles will break because
  Products.PluggableAuthService.plugins.ZODBRoleManager.listAssignedPrincipals
  raises MultiplePrincipalError, and maybe it will break somewhere else.
  Versions 4.0.4 and 3.13 use now the same algorithm.
  References http://dev.plone.org/plone/ticket/9361
  [vincenfretin]

- When calling editGroup method, avoid error
  while trying to remove dynamic 'AuthenticatedUsers' group.
  [thomasdesvenain]

- In Plone 4.1+, create a Site Administrators group with the new Site
  Administrator role.
  [davisagli]

- Fix critical error on groupprefs page
  when some groups have a non-ascii character in their title.
  Sort groups on their title normalized.
  This fixes http://dev.plone.org/plone/ticket/11301
  [thomasdesvenain]

- Fix interface error: doChangeUser takes a user id as parameter,
  not a login name.
  [wichert]

4.0.3 - 2010-09-09
------------------

- Check we have a REQUEST attribute before accessing it in
  getRolesForPrincipal.
  [vincentfretin]

- Use safe_unicode to correctly find users with
  non-ascii properties, regardless of the sys.defaultencoding.
  This fixes http://dev.plone.org/plone/ticket/10898
  [mr_savage]

4.0.2 - 2010-08-08
------------------

- Made last_login_time logic compatible with DateTime 2.12.5.
  [hannosch]

4.0.1 - 2010-07-31
------------------

- Clean up some unused imports and variable assignments.
  [esteele]

- Stop looking to GRUF to check if group properties can be edited.
  [esteele]

4.0 - 2010-07-18
----------------

- Avoid a deprecation warning for the credentialsChanged method.
  [hannosch]

- Fixed problems with missing user cache invalidation. This closes
  http://dev.plone.org/plone/ticket/10715.
  [fafhrd, hannosch]

- Make VirtualGroup inherit from PropertiedUser so it gets wrapped correctly.
  Have getGroupsForPrincipal not return the AutoGroup as a member of itself.
  Closes http://dev.plone.org/plone/ticket/10568.
  [cah190]

- PluggableAuthService expects a list of group ids from getGroups, don't pass a
  list of wrapped groups instead.
  [cah190, esteele]

- Added a custom `IMembershipTool` interface to PlonePAS extending the base one
  from CMFCore. It adds the `getMemberInfo` method to the mix. This closes
  http://dev.plone.org/plone/ticket/10240.
  [hannosch]

4.0b9 - 2010-06-03
------------------

- Fixed a test to no longer use removed Large Plone Folder type.
  [davisagli]

4.0b8 - 2010-05-01
------------------

- Removed special unauthorized view workaround, after the underlying issue
  has been fixed in Zope2.
  [davisagli, hannosch]

4.0b7 - 2010-04-07
------------------

- Added manage_setMembersFolderById method for ZMI.
  Fixes http://dev.plone.org/plone/ticket/10400
  [daftdog]

4.0b6 - 2010-03-05
------------------

- Revert incorrect PIL import change.
  [hannosch]

4.0b5 - 2010-03-03
------------------

- Install recursive_groups in new sites by default. Make it the last
  IGroupsPlugin installed.
  [esteele]

- Remove caching of utils.py's getGroupsForPrincipal method as it was nastily
  overzealous.
  [esteele, cah190]

- Use sets instead of util.py's 'unique' method.
  [esteele]

4.0b4 - 2010-02-18
------------------

- Properly import from PIL 1.1.7
  [tom_gross]

- Cache getGroupsForPrincipal per principal id per request (when available).
  [esteele]

4.0b3 - 2010-01-31
------------------

- Role plugin's tests no longer subclass (and run all of) ZODBRoleManagerTests
  as they cannot properly handle the plugin's expectation of finding a
  PluginRegistry with IGroupsPlugin
  [erikrose, esteele]

- Revert changes made to ZODBMutablePropertyProvider's enumerateUsers method
  which prevented lookup of users by id. Some refactoring.
  Refs http://dev.plone.org/plone/ticket/9361
  [erikrose, esteele]

- GroupAwareRoleManager now properly computes the roles of deeply-nested
  principals.
  [erikrose, esteele]

- Factor up getGroupsForPrincipal call.
  [erikrose, esteele]

- AutoGroup now implements IPropertiesPlugin to return group title and description.
  [erikrose, esteele]

- GroupsTool's getGroupsForPrincipal and getGroupMembers now return a list
  made up of groups/members from all responding plugins instead of just the
  first responder.
  [erikrose, esteele]

- Remove GroupData's _gruf_getProperty method, move remaining functionality
  into getProperty. getProperty now searches for properties in the following
  places: property sheets directly on the group object, PAS
  IPropertyProviders, portal_groupdata properties, and attributes on its
  GroupData entry. It returns the first piece of data found.
  Closes http://dev.plone.org/plone/ticket/9828
  [erikrose, esteele]

- Added __ignore_direct_roles__ request flag to getRolesForPrincipal() to
  permit retrieval of only group-provided (inherited) roles.
  [cah190]

- getGroupsForPrincipal is a method of PAS' IGroupsPlugin, adjust the groups
  tool's plugin lookup accordingly.
  [esteele]

- Rework the group detection of the ZODBMutablePropertyProvider so that
  enumerateUsers only returns users.
  [esteele]

- Add, but don't activate, a recursive groups plugin on installation.
  [esteele]

- Set proper titles for default groups.
  [esteele]

- Avoid the use of the classImplements helper from PAS. It dealt with the now
  gone Zope2 Interface variants and is no longer needed.
  [hannosch]

- Fix a misnamed kwarg in autogroup plugin.
  [cah190]

- Allow the groups tool's searchForGroups to handle an empty search string as
  'find all'.
  [esteele, cah190]

- Allow PASSearchView's searchGroups method to accept a sorting option.
  [esteele]

- Apply deiter's patch from http://dev.plone.org/plone/ticket/9460 to prevent
  GroupManager's 'getGroupById' from returning groups managed by other group
  managers.
  [esteele]

- GroupsTool.editGroup() now stores title and description in PAS
  propertysheets in addition to Plone-specific tools. This helps us not pave
  over group titles with IDs.
  [erikrose]

- Query the correct keyword variable for the group's description.
  [esteele]

- Fix an incorrect setdefault syntax.
  Closes http://dev.plone.org/plone/ticket/7345
  [esteele]

4.0b2 - 2010-01-02
------------------

- Don't specify PIL as a direct dependencies. It is not installed as an egg on
  all platforms.
  [hannosch]

4.0b1 - 2009-12-27
------------------

- Fixed package dependencies declaration.
  [hannosch]

4.0a2 - 2009-12-16
------------------

- Added backwards compatibility alias for PloneTool to support upgrades from
  Plone 2.5 to work.
  [hannosch]

- Added 'has_email' to the info returned by getMemberInfo.
  Refs http://dev.plone.org/plone/ticket/8707
  [maurits]

4.0a1 - 2009-11-14
------------------

- Simplified ``pas_member`` view.  Also return info when no member
  with the requested id exists, so this can be safely used also to get
  "member info" for deleted members.
  [maurits]

- Added new ``pas_member`` view, which provides easy access to the membership
  tools getMemberInfo method but caches the result on the request.
  [hannosch]

- Changed the default value of `memberareaCreationFlag` for the membership
  tool to False, as it was done during Plone site creation so far.
  [hannosch]

- Removed patch on ZODBUserManager.enumerateUsers which was introduced
  historical because of a former missing release of PluggableAuthService 1.5.
  This now superfluous patch also reduced the functionality of the
  patched method and introduced different behavior compared to i.e in
  a similar method on LDAPMultiPlugins. For details on the former
  patch see:
  http://dev.plone.org/collective/changeset/41512/PlonePAS/trunk/pas.py
  [jensens]

- Moved a couple DTML files here from CMFPlone that got left out of the earlier
  refactoring.
  [davisagli]

- Added a view of the Unauthorized exception which re-raises that exception
  in order to make sure that it triggers PAS' challenge plugin rather than
  rendering the standard_error_message.
  [davisagli]

- Removed deprecation warnings for various methods. These never happened.
  [hannosch]

- Removed half-done ZCacheable caching for users and groups.
  [hannosch]

- Removed the CMFDefault dependency of the membership tool. We only need the
  CMFCore functionality.
  [hannosch]

- PlonePAS.gruf_support.authenticate method was not breaking out of
  the loop upon successful authenticateCredentials.
  [runyaga]

- Changed objectIds and objectValues calls to use the IContainer API.
  [hannosch]

- Removed parts of the outdated Extensions.Install code.
  [hannosch]

- Removed a dependency on CMFPlone's `_createObjectByType` method.
  [hannosch]

- Removed magical `homePageText` lookup for initial memberarea content. You
  can use the `notifyMemberAreaCreated` hook for any kind of custom behavior.
  [hannosch]

- Moved the `scale_image` function from CMFPlone.utils into our own utils
  module, as we are the only user of it. Also made the tests independent of
  any CMFPlone code.
  [hannosch]

- Cleaned up package metadata.
  [hannosch]

- Declare test dependencies in an extra and fixed deprecation warnings
  for use of Globals.
  [hannosch]

- Switched the installation progress reporting to the logging framework.
  [hannosch]

- Cleaned up annoying license headers in all files. We have a central place
  to state the license.
  [hannosch]

- Started cleaning up deprecated methods and comments.
  [hannosch]

- Removed support for group workspaces. This part from GRUF hasn't been
  supported for many releases anymore.
  [hannosch]

- Merged all code for the groups tool from GRUF into this package, we are
  officially GRUF-dependency-free :)
  [hannosch]

- Merged all code for the group data tool from GRUF into this package.
  [hannosch]

- Removed the GRUFBridge plugin. PAS inside GRUF isn't supported anymore.
  [hannosch]

- Merged tests moved from CMFPlone into the same modules as the existing
  tests and normalized file names.
  [hannosch]

- Modernized tests and introduce a proper base testcase and layer.
  [hannosch]

- Removed cookie auth tests, these don't work anymore with plone.session.
  [hannosch]

- Moved over all tests for the four tools from CMFPlone.
  [hannosch]

- Removed the user folder migration code and cleaned up tests.
  [hannosch]

- Moved all code from the four tools from CMFPlone into this package.
  [hannosch]

- Removed 'listed' member property support from one of the many search
  functions following Plone.
  [hannosch]

- Copied setLoginFormInCookieAuth from CMFPlone migrations.
  [hannosch]

- Purged old Zope 2 Interface interfaces for Zope 2.12 compatibility.
  (only a test in this case)
  [elro]


3.12 - 2009-10-16
-----------------

- Fixed the performance fix again. enumerateUsers from mutable_properties
  plugin should return all the users if kw is empty. And it returns empty
  tuple if login or id parameter is used.
  [vincentfretin]


3.11 - 2009-10-05
-----------------

- Revert performance fix introduced in 3.10 for the mutable properties plugin.
  enumerateUsers shouldn't return results if id or login is not None like in
  3.9 (data dict doesn't contain id or login key, so testMemberData returns
  always False). The search should be performed only if kw parameter is not
  empty. This is the new optimization fix.
  [vincentfretin]


3.10 - 2009-09-06
-----------------

- Performance fix for searching in the mutable properties plugin:
  when only searching on user id do not walk over all properties,
  but only test if the user id is known. This fixes
  http://dev.plone.org/plone/ticket/9361
  [toutpt]

- Nested groups are now visible in prefs_group_members. This closes
  http://dev.plone.org/plone/ticket/8557
  [vincentfretin]

- Add sort and merge PASSearchView's interface to prevent code duplication.
  [csenger]


3.9 - 2009-04-21
----------------

- Fix the cookie plugin's login handler to not trust the username
  from the request. Instead we use the login name of the currently
  authenticated user. This fixes CVE-2009-0662 (see
  http://plone.org/products/plone/security/advisories/cve-2009-0662
  for more information).
  [wichert]


3.8 - 2009-02-13
----------------

- Update the role manager's assignRoleToPrincipal method to lazily
  update the cached list of portal roles. This fixes problems with
  adding users with GenericSetup-created roles.
  [wichert]

- Fixed our OrderedDict to be unpickable with pickle protocol 2. On
  unpickling a __init__ method is not called and an optimization in
  protocol 2 would call __setitem__ without the _list to be initialized.
  Even using a __getstate__ / __setstate__ combination wouldn't work
  around that. This change was found in using membrane and
  MemcachedManager.
  [hannosch, tesdal]


3.7 - 2008-09-28
----------------

- Removed deprecation zcml statements for PluggableAuthService components:
  these are now in PluggableAuthService itself.
  [wichert]

- Adjusted deprecation warnings to point to Plone 4.0 instead of Plone 3.5
  since we changed the version numbering again.
  [hannosch]


3.6 - 2008-06-25
----------------

- Modify PloneGroup.getMemberIds to use all IGroupIntrospection plugins
  to get the group members. This makes it possible to list members in
  an LDAP group.
  [wichert]


3.5 - 2008-06-25
----------------

- Make PASSearchView.merge actually merge search results. Its previous
  behaviour was quite nasty: it preferred search results from the
  enumeration plugin with the lowest priority!
  [wichert]


3.4 - 2008-03-26
----------------

- Added BBB code for changed setLoginFormInCookieAuth upgrade method.
  [hannosch]

- Ignore but log users without passwords during migration from pre-PAS, as
  these cannot be added to any standard user source.
  [hannosch]

- Fix listRoleInfo on the role plugin to also lazily update the list
  of portal roles.
  [wichert]

3.3 - 2007-03-07
----------------

- Added metadata.xml file to the profile.
  [hannosch]

- Move global role lookup out of the local role plugin. Part of the
  PLIP 127 merge for Plone 3.1.
  [alecm]


3.2 - 2008-02-15
----------------

- Fix schema handling for ZODBMutablePropertyProvider initialization.
  [maurits]

- Remove some exception swallowing from the installation logic so errors
  are not hidden.
  [hannosch]

- Correct handling an empty roles list when modifying groups.
  This fixes http://dev.plone.org/plone/ticket/6994
  [rsantos]


3.1 - 2007-10-08
----------------

- Improve handing of sorting for searches.
  [csenger]

- Updating the roles for a group did not invalidate the _findGroup cache.
  [wichert]

- Fixed some tool icons to point to existing icons.
  [hannosch]


3.0 - 2007-08-16
----------------

- Fix check for authenticateCredentials return value
  [rossp]


3.0rc2 - 2007-07-27
-------------------

- Fake a getPhysicalPath on our search view so ZCacheing works properly
  everywhere.
  [wichert]

- Add event classes for logged-in and logged-out events.
  [wichert]


3.0rc1 - 2007-07-08
-------------------

- Correct logic in MemberData capability methods: any plugin is
  allowed to (re)set a password, delete the user or add roles.
  [wichert]

- Use the proper API to get the containing PAS in the group plugin
  [wichert]

- Fix setting user properties on the user object.
  [wichert]


3.0b7 - 2007-05-05
------------------

- Removed the five:registerPackage statement again. It causes problems in a
  ZEO environment.
  [hannosch]

- Removed our version of the Plone tool from ToolInit. It won't get an icon
  anymore and you cannot add it, but existing instances still work. We
  migrate all instances back to the regular tool anyways.
  [hannosch]


3.0b6 - 2007-05-05
------------------

- Fixed two migration related test failures.
  [hannosch]

- Spring cleaning, removed some cruft, pyflaked and corrected some more
  undefined names.
  [hannosch]

- New package layout, following standard Python package conventions.
  [hannosch]

- Fixed tool names in ToolInit, so the permission has a proper name. This
  closes http://dev.plone.org/plone/ticket/6525.
  [hannosch]


3.0-beta5 - 2007-05-02
----------------------

- Modify the roles plugin to lazily update its roles list from the portal.
  [wichert]

- Filter duplicate search results.
  [laz, wichert]

- Add a sort_by option to the search methods to allow sorting of results
  by a property.
  [laz, wichert]

- Modify login method for the cookie plugin to perform the credential
  update in the PAS of the user instead of the PAS of the plugin. This
  helps in making sure that users will only authenticate against their
  own user folder, so we get all their roles, properties, etc. correctly.
  [wichert]

- Update installation logic to use plone.session for cookies
  [wichert]

- Add pas_info and pas_search browser views.
  [wichert]

- Deprecate the PlonePAS PloneTool; its changes have been merged in the
  standard Plone version.
  [wichert]

- Use getUtility to get the portal object.
  [wichert]

- Deprecate user and group searching through CMF member and group tools
  in favour of PAS enumeration.
  [wichert]

- Refactor user searching in the membership tool to use standard PAS
  searches.
  [wichert]

- Add user enumeration capabilities to the mutable properties plugin.
  [wichert]

- Add a new automatic group plugin which puts all users in a virtual
  group. This is useful for permissions handling: since it is not
  possible to add roles to users with the Authenticated role a
  virtual group can be used instead.
  [wichert]

- Added support to import PloneUserFactory and added stub
  for ZODBMutableProperties. Attention: Latter needs a real
  export and import! At the moment it do not export the
  propertysheets. This is a TODO. At least with this two
  additions PlonePAS import runs. Additional I needed to
  hack PluginRegistry and and PluggableAuthService slightly.
  [jensens]

- Added HISTORY.txt and updated version information.
  [hannosch]


2.4 - 2007-04-15
----------------

- Optomise the local roles plugin for the common case where
  local_roles is empty
  [dreamcatcher]

- the plone user was assuming a one to one mapping between property plugin
  and user property sheet, and stripping away additional ones as part of
  the retrieval of ordered sheets, instead, it now stores all
  propertysheets in an ordered dictionary, so this assumption is not needed
  [k_vertigo]

- More postonly security changes
  [alecm, ramon]


2.3 - 2007-05-30
----------------

- Use a local postonly decorator so PlonePAS can be used with Plone
  2.5, 2.5.1 and 2.5.2.
  [wichert]

- Protect the tools with postonly security modifiers.
  [mj]

- Update GRUF compatibility functions to use the same security checks
  as GRUF itself uses.
  [mj]

- Fix migration to handle properties of selection or multiple selection
  types.
  [reinout]

- Correct creation of groups which default group managers.
  [dreamcatcher]

- Fix migration from GRUF sites: also include the member properties in the
  migration.
  [tesdal]

- Correct the test for creation of groups with the same id as users: search
  for the exact id, not substrings.
  [tesdal]

- Fix bad form action which made it impossible to add a plone user factory
  plugin through the ZMI. Backported from trunk.
  [wichert]
