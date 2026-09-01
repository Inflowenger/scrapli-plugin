# Scrapli plugin for Inflowenger

An Inflowenger **plugin node** that runs CLI commands and configuration against
network devices — Cisco IOS-XE / NX-OS / IOS-XR, Arista EOS, Juniper JunOS —
using [scrapli](https://github.com/carlmontanari/scrapli) over SSH or Telnet. It
speaks the `inflowv1` protocol through the Python
[`inflowenger-plugin-sdk`](https://pypi.org/project/inflowenger-plugin-sdk/).

When a flow reaches the node, it opens an async scrapli connection to the device
named by the bound settings profile, runs your commands, and commits the results
as the node's output for downstream nodes to read.

## Actions

| Method | Title | What it does |
|--------|-------|--------------|
| `scrapli.command.send` | Send Commands | Run one or more exec/show commands. Optional TextFSM parsing. |
| `scrapli.config.send` | Send Config | Apply configuration lines (device enters config mode). |

Both output the same shape — a flow can read fields straight out of it:

```jsonc
{
  "host": "10.0.0.1",
  "platform": "cisco_iosxe",
  "failed": false,
  "results": [
    { "command": "show version", "result": "...", "failed": false, "elapsed_time": 0.42 }
    // when "Parse output" is on: also "parsed": [ { ... } ]
  ]
}
```

## How the connection is supplied

The plugin **stores no credentials.** It declares a **Scrapli Device** settings
form; the platform stores a filled-in copy as a reusable profile and folds it
into every call as `body.settings`. Bind one profile per device on the node.

Settings fields: `host`, `platform`, `transport` (SSH/Telnet), `port`,
`username`, `password`, `enable` (secondary secret), `strict_key`. Keys are
matched leniently — case, spaces, dashes and underscores are ignored, and common
synonyms (`ip`/`address` for host, `os`/`nos` for platform, `ios`/`nxos`/`xr`/
`eos`/`junos` platform aliases) are accepted. Submitting the settings dialog runs
a live connection test that reads the device prompt.

## Run it

```bash
cp .env.inflow.example .env.inflow     # fill in the values Infra minted
pip install -r requirements.txt
python main.py
```

`.env.inflow` holds a live credential — it is gitignored; never commit it.
Override the file path with `INFLOW_ENV_FILE`. On startup the SDK logs every NATS
subject it subscribes to — that log is your confirmation the plugin registered
with Infra. Then add the **SCRAPLI** node to a flow and run it.

## Layout

```
main.py                       wiring: intro, settings, actions, Start()
scrapli_plugin/
  settings.py                 lenient settings profile → Device  (no SDK/scrapli import)
  device.py                   scrapli connect + run helpers       (no SDK import)
  forms.py                    formkit form declarations
  actions.py                  action handlers + shared preamble
  meta.py                     settings-submit connection test
tests/                        offline: settings parsing + form invariants
```

`settings.py` and `device.py` carry no `inflow_plugin_sdk` import, so the
transport is testable without NATS and a future SDK version can't break it.

## Test

```bash
pip install -e ".[dev]"        # or: pip install pytest pytest-asyncio
pytest -q
```

The suite is fully offline (no device, no NATS): it covers the lenient settings
matcher — including the wrong-profile and bad-input cases — and asserts every
action form parses and never declares a `settings` property.

## Notes

- TextFSM parsing (the *Parse output* toggle) needs `ntc-templates`, pulled in by
  `requirements.txt`. When no template matches a command it falls back to the raw
  result and reports `parse_error` alongside it.
- A failed command **does not stop the flow** — the reason is committed as output
  and the run continues. Branch on it downstream if you need to.
