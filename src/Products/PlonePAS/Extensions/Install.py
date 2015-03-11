# -*- coding: utf-8 -*-
# BBB

# imported at least by borg.localrole.utils
from Products.PlonePAS.setuphandlers import activatePluginInterfaces  # noqa

# used by plone.app.upgrade/plone/app/upgrade/v43/final.py
from Products.PlonePAS.setuphandlers import setupPasswordPolicyPlugin  # noqa

# seems this is not needed anywhere outside setuphandlers
# from Products.PlonePAS.setuphandlers import setupRoles
# from Products.PlonePAS.setuphandlers import registerPluginType
# from Products.PlonePAS.setuphandlers import registerPluginTypes
# from Products.PlonePAS.setuphandlers import setupAuthPlugins
# from Products.PlonePAS.setuphandlers import updateProperties
# from Products.PlonePAS.setuphandlers import updateProp
# from Products.PlonePAS.setuphandlers import addPAS
# from Products.PlonePAS.setuphandlers import challenge_chooser_setup
