# -*- coding: utf-8 -*-
from DateTime import DateTime
from OFS.Image import Image
from Products.CMFCore.interfaces import IMemberData
from Products.PlonePAS.tests import base
from Products.PlonePAS.tests import dummy
from Products.PluggableAuthService.interfaces.events import \
        IPropertiesUpdatedEvent
from plone.app.testing import TEST_USER_ID as default_user
import zope.component


class TestMemberDataTool(base.TestCase):

    def afterSetUp(self):
        self.memberdata = self.portal.portal_memberdata
        self.membership = self.portal.portal_membership
        self.membership.memberareaCreationFlag = 0
        # Don't let default_user disturb results
        self.portal.acl_users._doDelUsers([default_user])
        # Add some members
        self.addMember('fred', 'Fred Flintstone', 'fred@bedrock.com',
                       ['Member', 'Reviewer'], '2002-01-01')
        self.addMember('barney', 'Barney Rubble', 'barney@bedrock.com',
                       ['Member'], '2002-01-01')
        self.addMember('brubble', 'Bambam Rubble', 'bambam@bambam.net',
                       ['Member'], '2003-12-31')
        # MUST reset this
        self.memberdata._v_temps = None

    def addMember(self, username, fullname, email, roles, last_login_time):
        self.membership.addMember(username, 'secret', roles, [])
        member = self.membership.getMemberById(username)
        member.setMemberProperties({
            'fullname': fullname,
            'email': email,
            'last_login_time': DateTime(last_login_time), })

    def testSetPortrait(self):
        self.memberdata._setPortrait(
            Image(id=default_user, file=dummy.File(), title=''),
            default_user)
        self.assertEqual(self.memberdata._getPortrait(default_user).getId(),
                         default_user)
        self.assertEqual(self.memberdata._getPortrait(default_user).meta_type,
                         'Image')

    def testDeletePortrait(self):
        self.memberdata._setPortrait(
            Image(id=default_user, file=dummy.File(), title=''),
            default_user)
        self.memberdata._deletePortrait(default_user)
        self.assertEqual(self.memberdata._getPortrait(default_user), None)

    def testPruneMemberDataContents(self):
        # Only test what is not already tested elswhere
        self.memberdata._setPortrait(
            Image(id=default_user, file=dummy.File(), title=''),
            default_user)
        self.memberdata._setPortrait(
            Image(id=default_user, file=dummy.File(), title=''),
            'dummy')
        self.memberdata.pruneMemberDataContents()
        self.assertEqual(len(self.memberdata.portraits), 1)

    def testFulltextMemberSearch(self):
        # Search for a user by id, name, email, ...
        search = self.memberdata.searchFulltextForMembers
        self.assertEqual(len(search('')), 3)
        self.assertEqual(len(search('rubble')), 2)
        self.assertEqual(len(search('stone')), 1)
        self.assertEqual(len(search('bambam.net')), 1)
        self.assertEqual(len(search('bedrock.com')), 2)
        self.assertEqual(len(search('brubble')), 1)

    def testPropertiesUpdatedEvent(self):

        def event_handler(context, event):
            self._properties_updated_handler_called = True

        gsm = zope.component.getGlobalSiteManager()
        gsm.registerHandler(event_handler,
                            (IMemberData, IPropertiesUpdatedEvent))

        self._properties_updated_handler_called = False

        username = 'ez'
        roles = ['Member']
        fullname = 'Ez Zy'
        email = 'ez@ezmail.net'

        self.membership.addMember(username, 'secret', roles, [])
        member = self.membership.getMemberById(username)

        self.assertFalse(self._properties_updated_handler_called)

        member.setMemberProperties({
            'fullname': fullname,
            'email': email})

        self.assertTrue(self._properties_updated_handler_called)

        # Test that notify(PropertiesUpdated) isn't called on user login.
        self._properties_updated_handler_called = False

        # Imitate a login as the plone.app.testing login method doesn't seem to
        # set these member properties.
        member.setMemberProperties({
            'login_time': DateTime('2018-02-15'),
            'last_login_time': DateTime('2018-02-15')})

        self.assertFalse(self._properties_updated_handler_called)

        # Test notify(PropertiesUpdated) isn't called when login_time is
        # present as we're assuming this should only be changed on login.
        self._properties_updated_handler_called = False
        member.setMemberProperties({
            'login_time': DateTime('2018-02-15'),
            'fullname': 'Bed Rock'})

        self.assertFalse(self._properties_updated_handler_called)
        gsm.unregisterHandler(event_handler,
                              (IMemberData, IPropertiesUpdatedEvent))
