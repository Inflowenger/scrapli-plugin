# scrapli transport: open a connection and run commands/config. No sdkv1 import
# — kept free of the SDK so it's testable on its own and the SDK can't break it.
from __future__ import annotations

from typing import Any, Optional

from .settings import Device

# Conservative per-operation timeouts (seconds). A slow device or a flaky link
# should fail the node with a clear timeout rather than hang the flow.
_TIMEOUT_SOCKET = 15.0
_TIMEOUT_TRANSPORT = 30.0
_TIMEOUT_OPS = 30.0


async def open_conn(device: Device):
    """Open an async scrapli connection to `device` and return the live driver.
    The caller owns closing it. Raises on connect/auth failure."""
    from scrapli import AsyncScrapli

    conn = AsyncScrapli(
        timeout_socket=_TIMEOUT_SOCKET,
        timeout_transport=_TIMEOUT_TRANSPORT,
        timeout_ops=_TIMEOUT_OPS,
        **device.conn_args(),
    )
    await conn.open()
    return conn


def response_to_dict(resp: Any, parse: bool = False) -> dict[str, Any]:
    """Flatten one scrapli Response into JSON-able output the flow can read."""
    item: dict[str, Any] = {
        "command": resp.channel_input,
        "result": resp.result,
        "failed": bool(resp.failed),
        "elapsed_time": round(float(resp.elapsed_time or 0.0), 3),
    }
    if parse:
        try:
            item["parsed"] = resp.textfsm_parse_output()
        except Exception as e:  # parsing is best-effort; keep the raw result
            item["parse_error"] = str(e)
    return item


async def send_commands(
    device: Device, commands: list[str], *, strip_prompt: bool = True, parse: bool = False
) -> dict[str, Any]:
    """Open, run each exec/show command, close. Returns a JSON-able result bag."""
    conn = await open_conn(device)
    try:
        multi = await conn.send_commands(commands, strip_prompt=strip_prompt)
    finally:
        await conn.close()
    results = [response_to_dict(r, parse=parse) for r in multi]
    return {
        "host": device.host,
        "platform": device.platform,
        "failed": any(r["failed"] for r in results),
        "results": results,
    }


async def send_configs(
    device: Device, configs: list[str], *, stop_on_failed: bool = True
) -> dict[str, Any]:
    """Open, apply config lines (entering config mode), close."""
    conn = await open_conn(device)
    try:
        multi = await conn.send_configs(configs, stop_on_failed=stop_on_failed)
    finally:
        await conn.close()
    results = [response_to_dict(r) for r in multi]
    return {
        "host": device.host,
        "platform": device.platform,
        "failed": any(r["failed"] for r in results),
        "results": results,
    }


async def probe(device: Device) -> str:
    """Open, read the device prompt, close — the connection test for settings."""
    conn = await open_conn(device)
    try:
        prompt: Optional[str] = await conn.get_prompt()
    finally:
        await conn.close()
    return prompt or ""
