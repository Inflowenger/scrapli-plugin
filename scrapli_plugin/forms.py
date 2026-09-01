# Forms: the settings (connection) form and the per-action forms. Each is built
# once from a single formkit declaration, so schema and UI can't drift apart.
from __future__ import annotations

from inflow_plugin_sdk import formkit
from inflow_plugin_sdk.formkit import Option


def settings_form() -> formkit.Form:
    """The connection form. Its fields ARE the credentials — the platform stores a
    filled-in copy as a reusable profile and folds it into every call. Never put
    these on an action form."""
    return formkit.form("Scrapli Device").describe(
        "How to reach one network device over SSH or Telnet."
    ).add(
        formkit.text("host", "Host / IP").required()
            .help("Hostname or IP of the device, e.g. 10.0.0.1"),
        formkit.choice(
            "platform", "Platform",
            Option("cisco_iosxe", "Cisco IOS-XE"),
            Option("cisco_nxos", "Cisco NX-OS"),
            Option("cisco_iosxr", "Cisco IOS-XR"),
            Option("arista_eos", "Arista EOS"),
            Option("juniper_junos", "Juniper JunOS"),
        ).required().default("cisco_iosxe"),
        formkit.choice(
            "transport", "Transport",
            Option("asyncssh", "SSH"),
            Option("asynctelnet", "Telnet"),
        ).default("asyncssh"),
        formkit.integer("port", "Port").help("Defaults to 22 (SSH) / 23 (Telnet)."),
        formkit.text("username", "Username").required(),
        formkit.secret("password", "Password").required(),
        formkit.secret("enable", "Enable secret")
            .help("Secondary/enable password, if the platform needs one."),
        formkit.boolean("strict_key", "Strict host-key checking").default(False),
    )


def command_form() -> formkit.FormBuilder:
    """`scrapli.command.send` — run one or more exec/show commands."""
    return formkit.form("Send Commands").add(
        formkit.text_area("commands", "Commands").required()
            .help("One command per line, e.g. show version"),
        formkit.boolean("parse", "Parse output (TextFSM)").default(False)
            .help("Structure each result with ntc-templates, when a template exists."),
        formkit.boolean("strip_prompt", "Strip trailing prompt").default(True),
    ).build()


def config_form() -> formkit.FormBuilder:
    """`scrapli.config.send` — apply configuration lines."""
    return formkit.form("Send Config").add(
        formkit.text_area("configs", "Configuration").required()
            .help("One configuration line per row; the device enters config mode."),
        formkit.boolean("stop_on_failed", "Stop on first failure").default(True),
    ).build()
