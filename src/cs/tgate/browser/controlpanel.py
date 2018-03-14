from ..interfaces import ITgateControlPanel
from plone.app.registry.browser.controlpanel import ControlPanelFormWrapper
from plone.app.registry.browser.controlpanel import RegistryEditForm
from plone.z3cform import layout


class TgateControlPanelForm(RegistryEditForm):
    schema = ITgateControlPanel
    schema_prefix = "tgate"
    label = u'TGATE translation service settings'


TgateControlPanelView = layout.wrap_form(
    TgateControlPanelForm, ControlPanelFormWrapper)
