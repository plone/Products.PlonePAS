Add separate `GenericSetup` profile to switch the Zope root `/acl_users` to use a simple
cookie login form.  Useful when Zope root login and logout need to synchronize
authentication state between multiple plugins, which is not possible with HTTP `Basic
...` authentication. [rpatterson] (#65)
