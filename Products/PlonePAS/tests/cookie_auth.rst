Test for Cookie Auth
====================

  >>> from zope.interface import implementedBy
  >>> from plone.app.testing import TEST_USER_NAME
  >>> from plone.app.testing import TEST_USER_PASSWORD

User in Plone Site
------------------

Plone Site has PAS installed

  >>> portal = layer['portal']
  >>> print portal.acl_users.meta_type
  Pluggable Auth Service

User exists in the user folder inside the Plone Site.

  >>> uf = portal.acl_users
  >>> print uf.meta_type
  Pluggable Auth Service

  >>> user_name, user_password, user_role = ('foo', 'bar', 'Manager')
  >>> uf.userFolderAddUser(user_name, user_password, [user_role], [])

  >>> uf.getUserById(user_name)
  <PloneUser 'foo'>

Login to Plone Site using Basic Auth works.

  >>> from plone.testing.z2 import Browser
  >>> browser = Browser(layer['app'])
  >>> browser.addHeader('Authorization', 'Basic %s:%s' % (TEST_USER_NAME, TEST_USER_PASSWORD,))
  >>> browser.open('%s/manage' % portal.absolute_url())
  >>> print browser.headers
  Status: 200 Ok...

Make sure cookie plugin is installed and activated.

  >>> uf.objectIds('Extended Cookie Auth Helper')
  ['credentials_cookie_auth']

  >>> plugins = uf.plugins
  >>> cookie = uf['credentials_cookie_auth']

  >>> ifaces = tuple(implementedBy(cookie.__class__).flattened())

  >>> actives = []
  >>> for iface in ifaces:
  ...    try:
  ...       actives.append((plugins.listPlugins(iface), iface))
  ...    except KeyError:
  ...       pass

  >>> for active, iface in actives:
  ...     print iface,
  ...     for id, plugin in active:
  ...         if id == 'credentials_cookie_auth':
  ...            print True
  <...IExtraction...> True
  <...IChallenge...> True
  <...ICredentialsUpdate...> <...ICredentialsReset...>

User in parent folder
---------------------

User Exists on the folder containing the Plone Site, which should be a
Pluggable Auth Service too.

  >>> uf = layer['app'].acl_users
  >>> print uf.meta_type
  Pluggable Auth Service

  >>> user_name, user_password, user_role = ('baz', 'bar', 'Manager')
  >>> uf.userFolderAddUser(user_name, user_password, [user_role], [])

  >>> uf.getUserById(user_name)
  <PropertiedUser 'baz'>

  >>> import transaction
  >>> transaction.commit()

Login directly to containing folder using Basic Auth works.

  >>> browser = Browser(layer['app'])
  >>> browser.addHeader('Authorization', 'Basic %s:%s' % (user_name, user_password,))
  >>> browser.open('%s/manage' % layer['app'].absolute_url())
  >>> print browser.headers
  Status: 200 Ok...

Login to Plone Site using Basic Auth works.

  >>> browser = Browser(layer['app'])
  >>> browser.addHeader('Authorization', 'Basic %s:%s' % (user_name, user_password,))
  >>> browser.open('%s/manage' % portal.absolute_url())
  >>> print browser.headers
  Status: 200 Ok...

