"""Forms — every schema/UI parses as JSON, and no ACTION form leaks a `settings`
property (credentials belong to the settings profile, not an action form)."""
import json

import pytest

from scrapli_plugin import forms

ACTION_FORMS = [forms.command_form(), forms.config_form()]


@pytest.mark.parametrize("fb", ACTION_FORMS)
def test_action_schema_and_ui_parse(fb):
    schema = json.loads(fb.jsonschema)
    ui = json.loads(fb.jsonui)
    assert schema["type"] == "object"
    assert ui["type"] == "VerticalLayout"


@pytest.mark.parametrize("fb", ACTION_FORMS)
def test_action_form_has_no_settings_property(fb):
    props = json.loads(fb.jsonschema).get("properties", {})
    assert "settings" not in props, "credentials must not appear on an action form"


def test_command_form_requires_commands():
    schema = json.loads(forms.command_form().jsonschema)
    assert "commands" in schema["properties"]
    assert "commands" in schema.get("required", [])


def test_config_form_requires_configs():
    schema = json.loads(forms.config_form().jsonschema)
    assert "configs" in schema.get("required", [])


def test_settings_form_declares_connection_fields():
    fb = forms.settings_form().build()
    props = json.loads(fb.jsonschema)["properties"]
    for key in ("host", "platform", "username", "password"):
        assert key in props
    # the password renders masked — the hint lives on the UI control's options
    ui = json.loads(fb.jsonui)
    controls = [e for e in ui["elements"] if e.get("scope", "").endswith("/password")]
    assert controls and controls[0]["options"]["format"] == "password"
