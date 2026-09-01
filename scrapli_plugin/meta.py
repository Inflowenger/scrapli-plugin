# Settings submit handler — the connection test the set-up dialog runs. It's a
# validator, not a store: it opens the device, reads the prompt, and answers
# ok/error. The platform owns storing the profile.
from __future__ import annotations

from inflow_plugin_sdk import Request, Response, cast_request_to

from . import device as dev
from .settings import parse_settings


async def ping(req: Request) -> Response:
    """Reply for `@settings` submit. The submitted values arrive as the action
    envelope, so the fields sit under `.body` (not `.body.settings` — these fields
    ARE the connection)."""
    try:
        rb = cast_request_to(req.data)
    except Exception as e:
        return Response(error=f"unreadable settings: {e}")

    device, err = parse_settings(rb.body if isinstance(rb.body, dict) else {})
    if err:
        return Response(error=err)

    try:
        prompt = await dev.probe(device)
    except Exception as e:
        return Response(error=f"cannot reach {device.host}: {e}")

    return Response(data={"ok": True, "host": device.host, "prompt": prompt})
