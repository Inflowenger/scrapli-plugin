"""Scrapli plugin — wiring: intro, settings, actions, then Start() and block.

Run:
    cp .env.inflow.example .env.inflow    # fill in the values Infra minted
    pip install -r requirements.txt
    python main.py

On startup the SDK logs every subject it subscribes to — that log is the
confirmation the plugin registered with Infra.
"""
import asyncio
import os

from inflow_plugin_sdk import Action, new_plugin, with_dot_env

from scrapli_plugin import __version__, actions, forms, meta


async def main() -> None:
    env_file = os.getenv("INFLOW_ENV_FILE") or ".env.inflow"
    p = await new_plugin(with_dot_env(env_file))

    p.intro_data.name = "SCRAPLI"
    p.intro_data.author = "Mehdi Shokohifar"
    p.intro_data.version = __version__
    p.intro_data.manual = (
        "Run CLI commands and configuration against network devices "
        "(Cisco IOS-XE / NX-OS / IOS-XR, Arista EOS, Juniper JunOS) using scrapli.\n\n"
        "Create a **Scrapli Device** settings profile per device, then bind it on "
        "the node. Submit tests the connection by reading the device prompt."
    )

    # Settings (the connection form) + its submit-time connection test. The same
    # object serves @intro.settings and @settings, and carries the submit handler.
    settings = forms.settings_form().settings(meta.ping)
    p.intro_data.settings = settings
    p.required_params(settings)

    p.add_action(
        Action(
            method="scrapli.command.send",
            title="Send Commands",
            description="Run one or more exec/show commands on the device",
            form=forms.command_form(),
            request_handler=actions.send_commands,
        ),
        Action(
            method="scrapli.config.send",
            title="Send Config",
            description="Apply configuration lines on the device",
            form=forms.config_form(),
            request_handler=actions.send_config,
        ),
    )

    await p.start()
    await asyncio.Event().wait()  # keep the process alive to serve requests


if __name__ == "__main__":
    asyncio.run(main())
