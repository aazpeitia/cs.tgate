# -*- coding: utf-8 -*-
from cs.tgate import _
from plone.app.textfield.value import RichTextValue
from plone.registry.interfaces import IRegistry
from Products.CMFPlone.utils import safe_unicode
from Products.Five.browser import BrowserView
from Products.statusmessages.interfaces import IStatusMessage
from tgateclient.client import TGateClient
from z3c.form import button
from z3c.form import field
from z3c.form import form
from zope.annotation.interfaces import IAnnotations
from zope.component import getUtility
from zope.interface import Interface
from zope.schema import Choice
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary
from plone.app.multilingual import api as pam

import tempfile


KEY = "cstgate.document"


def not_document_being_translated(frm):
    return not frm.document_being_translated()


def document_translated(frm):
    return frm.document_translated()


model_vocabulary = SimpleVocabulary(
    [
        SimpleTerm("generic_en2es_GPU", title="generic_en2es_GPU"),
        SimpleTerm("generic_es2en_GPU", title="generic_es2en_GPU"),
    ]
)

translation_mode_vocabulary = SimpleVocabulary(
    [
        SimpleTerm("HumanTranslation", "HumanTranslation"),
        SimpleTerm("MachineTranslation", "MachineTranslation"),
        SimpleTerm("PostEditedTranslation", "PostEditedTranslation"),
    ]
)


class ITGateTranslation(Interface):
    model = Choice(title=_(u"Translation model"), source=model_vocabulary)

    tr_mode = Choice(title=_(u"Translation mode"), source=translation_mode_vocabulary)

    field_to_translate = Choice(title=_(u"Field to translate"), values=["text"])


class RequestTGateTranslation(form.Form):
    ignoreContext = True

    @property
    def fields(self):
        if self.document_being_translated():
            return field.Fields(ITGateTranslation["field_to_translate"])
        else:
            return field.Fields(ITGateTranslation)

    @property
    def label(self):
        if self.document_being_translated():
            if self.document_translated():
                return _(u"This document has already translated")
            else:
                return _(u"This document is being translated")
        else:
            return _(u"Click to translate the document")

    @button.buttonAndHandler(
        _(u"Request translation"), condition=not_document_being_translated
    )
    def request_translation(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return

        fieldname = data.get("field_to_translate")
        filepath = self._make_html_document_from_field(fieldname)
        result = self._translate(filepath, data.get("model"), data.get("tr_mode"))

        # XXX: Hardcoded langauge
        translation = pam.translate(self.context, target_language="en")
        translation.title = self.context.title
        translation.description = self.context.description
        translation.text = self.context.text

        if result is not None:
            annotated = IAnnotations(translation)
            annotated[KEY] = result

            messages = IStatusMessage(self.request)
            messages.add(_(u"TGATE translation requested correctly"))
            return self.request.response.redirect(translation.absolute_url())
        else:
            messages = IStatusMessage(self.request)
            messages.add(_(u"Error when requesting translations"), "error")
            return self.request.response.redirect(self.context.absolute_url())

    @button.buttonAndHandler(_(u"Download translation"), condition=document_translated)
    def download_translation(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return

        registry = getUtility(IRegistry)
        base_url = registry.get("tgate.tgate_server_url")
        username = registry.get("tgate.tgate_server_username")
        password = registry.get("tgate.tgate_server_password")

        client = TGateClient(base_url, username, password)
        annotated = IAnnotations(self.context)
        document_id = annotated.get(KEY, None)
        if document_id:
            response = client.download_document(document_id)
            if response.get("status") == "success":
                text = response.get("data", {}).get("contents", "")
                self._make_field_from_html_document(
                    text, data.get("field_to_translate")
                )
                messages = IStatusMessage(self.request)
                messages.add(_(u"Translation downloaded correctly"), "info")
                return self.request.response.redirect(self.context.absolute_url())

        messages = IStatusMessage(self.request)
        messages.add(_(u"Error when downloading the translation"), "error")
        return self.request.response.redirect(self.context.absolute_url())

    def _make_html_document_from_field(self, fieldname):
        fp = tempfile.NamedTemporaryFile(delete=False)
        field = getattr(self.context, fieldname)
        if isinstance(field, RichTextValue):
            value = field.output

        fp.write(safe_unicode(value).encode("utf-8"))
        fp.close()
        return fp.name

    def _make_field_from_html_document(self, html, fieldname):
        field = getattr(self.context, fieldname)
        if isinstance(field, RichTextValue):
            setattr(
                self.context, fieldname, RichTextValue(html, "text/html", "text/html")
            )
        else:
            setattr(self.context, fieldname, html)

    def _translate(self, filename, model_id, translation_mode):
        registry = getUtility(IRegistry)
        base_url = registry.get("tgate.tgate_server_url")
        username = registry.get("tgate.tgate_server_username")
        password = registry.get("tgate.tgate_server_password")

        client = TGateClient(base_url, username, password)
        response = client.upload(filename)
        if response.get("status") == "success":
            document_id = response.get("data", {}).get("id", None)
            response = client.translate_document(
                document_id, model_id, translation_mode
            )
            if response.get("status") == "success":
                return response.get("data", {}).get("id", None)

        return None

    def document_being_translated(self):

        manager = pam.get_translation_manager(self.context)
        translation = manager.get_translation("en")
        if translation is not None:
            annotated = IAnnotations(translation)
            return KEY in annotated
        return False

    def document_translated(self):
        registry = getUtility(IRegistry)
        base_url = registry.get("tgate.tgate_server_url")
        username = registry.get("tgate.tgate_server_username")
        password = registry.get("tgate.tgate_server_password")

        client = TGateClient(base_url, username, password)

        manager = pam.get_translation_manager(self.context)
        translation = manager.get_translation("en")
        if translation is not None:
            annotated = IAnnotations(translation)
            document_id = annotated.get(KEY, None)
            if document_id:
                response = client.get_document_status(document_id)
                if response.get("status") == "success":
                    status = response.get("data", {}).get("id", "")
                    return status == "READY"

        return False
