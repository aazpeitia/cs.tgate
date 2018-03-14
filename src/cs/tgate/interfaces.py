# -*- coding: utf-8 -*-
"""Module where all interfaces, events and exceptions live."""

from cs.tgate import _
from zope import schema
from zope.interface import Interface
from zope.publisher.interfaces.browser import IDefaultBrowserLayer


class ICsTgateLayer(IDefaultBrowserLayer):
    """Marker interface that defines a browser layer."""


class ITgateControlPanel(Interface):
    tgate_server_url = schema.TextLine(
        title=_(u'Enter the URL of the TGATE server'),
        required=True,
        default=u''
    )

    tgate_server_username = schema.TextLine(
        title=_(u'Enter the user to use the TGATE server'),
        required=True,
        default=u''
    )

    tgate_server_password = schema.TextLine(
        title=_(u'Enter the password to use the TGATE server'),
        required=True,
        default=u''
    )

