# Action handlers. Each casts the request, resolves the settings profile into a
# Device, runs the scrapli work, and finishes with exactly one terminal call.
from __future__ import annotations

from typing import Any

from inflow_plugin_sdk import Frame, Job, cast_request_to

from . import device as dev
from .settings import parse_settings


def _lines(value: Any) -> list[str]:
    """Split a textarea (or accept an already-list) into non-empty trimmed lines."""
    if isinstance(value, list):
        items = value
    elif value is None:
        items = []
    else:
        items = str(value).splitlines()
    return [s.strip() for s in items if str(s).strip()]


async def _resolve(job: Job) -> tuple[Any, dict[str, Any]] | None:
    """Shared preamble: cast the envelope and resolve settings into a Device.
    On any failure it finishes the job and returns None, so the caller returns."""
    try:
        rb = cast_request_to(job.req.data)
    except Exception as e:
        await job.done_with_error(f"bad request: {e}")
        return None
    body = rb.body if isinstance(rb.body, dict) else {}
    device, err = parse_settings(body.get("settings"))
    if err:
        await job.done_with_error(err)
        return None
    return device, body


async def send_commands(job: Job) -> None:
    resolved = await _resolve(job)
    if resolved is None:
        return
    device, body = resolved

    commands = _lines(body.get("commands"))
    if not commands:
        await job.done_with_error("no commands: enter at least one command to run")
        return

    await job.progress(20, Frame(title="connecting", content=f"{device.host} ({device.platform})"))
    try:
        out = await dev.send_commands(
            device,
            commands,
            strip_prompt=body.get("strip_prompt", True),
            parse=bool(body.get("parse", False)),
        )
    except Exception as e:
        await job.done_with_error(f"{device.host}: {e}")
        return

    await job.progress(90, Frame(title="done", content=f"{len(commands)} command(s)"))
    await job.done(out)


async def send_config(job: Job) -> None:
    resolved = await _resolve(job)
    if resolved is None:
        return
    device, body = resolved

    configs = _lines(body.get("configs"))
    if not configs:
        await job.done_with_error("no configuration: enter at least one config line")
        return

    await job.progress(20, Frame(title="connecting", content=f"{device.host} ({device.platform})"))
    try:
        out = await dev.send_configs(
            device,
            configs,
            stop_on_failed=body.get("stop_on_failed", True),
        )
    except Exception as e:
        await job.done_with_error(f"{device.host}: {e}")
        return

    await job.progress(90, Frame(title="done", content=f"{len(configs)} line(s)"))
    await job.done(out)
