Overview
========

This product extends `PluggableAuthService <https://github.com/zopefoundation/Products.PluggableAuthService>`_ (PAS) for use in Plone.

It adds

- group support
- auto group assignment
- support for mutable properties
- cookie based login
- local role support
- password policy support
- enhanced user objects
- enhanced cmf tools (groups, members)
- simple passwordpolicy
- new event for users initial log in

PlonePAS also adds the API of the old GroupUserFolder (GRUF) to PAS.
GRUF was used in Plone 2.5.x and earlier as the default user folder.

Lots of this changes are done with monkey patches to PAS itself.
This is not ideal, but was done in past this way, even if we now would do it better.

PlonePAS does not depend on Plone itself, just on Zope2, PAS and CMF and some low level libraries.

FAQ
---

Why doesn't the title of my group, that I set in the ZMI, show up?
    The title for a group comes from the properties plugin.
    The info in the groups plugin isn't used, except for the name.

    The value of the ``title`` property on the ``portal_groupdata`` or ``portal_memberdata tools`` themselves (as opposed to the group or member data records within them) will not be used as a default for the title of the group or member.
    This is to prevent UI confusion if a title is set without realizing the implications.
    To remove this special case, see ``plugins.property._getDefaultValues``.

Why are my schema changes ignored?
    If PAS caching is enabled (see the ``Cache`` tab) and the cache manager does not have a *cleanup* method (RAMCacheManager has one), then changes to the memberdata schema will not effect users already cached.
    In this case, restart the server or clear the cache (if possible) for the changes to take effect.

    Similarly, changes to the memberdata schema will not propagate to member objects already in use.
    If you have a memberdata object and change the memberdata properties you must re-construct the member by saying ``portal_membership.getMemberById`` again.
    See ``tests.test_properties.test_user_properties`` for example.

Why can't I logout?
    By default, logout from users signed in under HTTP Basic Auth cannot log out.
    If you enable the ``Credentials Reset`` plugin for the HTTP Basic plugin, the logout for cookies will no longer work.
    However, this is not a problem if you're not using cookies.

Authorship
----------

Initial creation: The PAS CIGNEX Sprint Team [ Anders, Bob, Ben,
Chad, Gautham, Joel, Kapil, Michel, Micheal ]

Post-sprint work: J Cameron Cooper, Leo, Sidnei, Mark at `Enfold
Systems <http://enfoldsystems.com>`_

Basic setAuthCookie support (to mimick CookieCrumbler):
Rocky Burt at `ServerZen Software <http://www.serverzen.com>`_

Synced login process with Plone:
Dorneles Tremea at `PloneSolutions <http://plonesolutions.com>`_

Bugfixes, various development and merging with Plone:
Wichert Akkerman at Simplon

Bugfixes, improvements to membership and property lookups:
Eric Steele and Erik Rose

Review, cleanup, modernize code, adressing Plone 5:
Jens Klein, BlueDynamics Alliance - `Klein & Partner KG <http://kleinundpartner.at>`_

Source Code
-----------

Contributors please read the document `Process for Plone core's development <http://docs.plone.org/develop/plone-coredev/index.html>`_

Sources are at the `Plone code repository hosted at Github <https://github.com/plone/Products.PlonePAS>`_.
