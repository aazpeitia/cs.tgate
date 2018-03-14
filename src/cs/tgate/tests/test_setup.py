# -*- coding: utf-8 -*-
"""Setup tests for this package."""
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from cs.tgate.testing import CS_TGATE_INTEGRATION_TESTING  # noqa

import unittest


class TestSetup(unittest.TestCase):
    """Test that cs.tgate is properly installed."""

    layer = CS_TGATE_INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer['portal']
        self.installer = api.portal.get_tool('portal_quickinstaller')

    def test_product_installed(self):
        """Test if cs.tgate is installed."""
        self.assertTrue(self.installer.isProductInstalled(
            'cs.tgate'))

    def test_browserlayer(self):
        """Test that ICsTgateLayer is registered."""
        from cs.tgate.interfaces import (
            ICsTgateLayer)
        from plone.browserlayer import utils
        self.assertIn(
            ICsTgateLayer,
            utils.registered_layers())


class TestUninstall(unittest.TestCase):

    layer = CS_TGATE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.installer = api.portal.get_tool('portal_quickinstaller')
        roles_before = api.user.get(userid=TEST_USER_ID).getRoles()
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        self.installer.uninstallProducts(['cs.tgate'])
        setRoles(self.portal, TEST_USER_ID, roles_before)

    def test_product_uninstalled(self):
        """Test if cs.tgate is cleanly uninstalled."""
        self.assertFalse(self.installer.isProductInstalled(
            'cs.tgate'))

    def test_browserlayer_removed(self):
        """Test that ICsTgateLayer is removed."""
        from cs.tgate.interfaces import \
            ICsTgateLayer
        from plone.browserlayer import utils
        self.assertNotIn(
           ICsTgateLayer,
           utils.registered_layers())
