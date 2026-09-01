# Settings parsing: turn a settings profile (typed by hand as key/value rows)
# into a Device. No sdkv1 import here — this is pure, so it's testable without
# NATS, and a future SDK version can't break it.
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

# The five async core drivers scrapli's AsyncScrapli factory ships. A device's
# platform must resolve to one of these keys.
CORE_PLATFORMS = {
    "cisco_iosxe",
    "cisco_iosxr",
    "cisco_nxos",
    "arista_eos",
    "juniper_junos",
}

# Human synonyms → the canonical scrapli platform key. Profiles are typed by
# hand, so accept the spellings an operator actually writes.
_PLATFORM_SYNONYMS = {
    "ios": "cisco_iosxe",
    "iosxe": "cisco_iosxe",
    "cisco_ios": "cisco_iosxe",
    "cisco_iosxe": "cisco_iosxe",
    "iosxr": "cisco_iosxr",
    "xr": "cisco_iosxr",
    "cisco_iosxr": "cisco_iosxr",
    "nxos": "cisco_nxos",
    "nexus": "cisco_nxos",
    "cisco_nxos": "cisco_nxos",
    "eos": "arista_eos",
    "arista": "arista_eos",
    "arista_eos": "arista_eos",
    "junos": "juniper_junos",
    "juniper": "juniper_junos",
    "juniper_junos": "juniper_junos",
}

# async transports scrapli offers; anything else can't run under asyncio.
_TRANSPORTS = {"asyncssh", "asynctelnet"}

# Field synonyms. Each canonical setting accepts several key spellings; the
# lenient matcher (below) strips case, spaces, dashes and underscores first.
_ALIASES: dict[str, tuple[str, ...]] = {
    "host": ("host", "hostname", "ip", "ipaddress", "address", "device", "target"),
    "port": ("port",),
    "username": ("username", "user", "authusername", "login"),
    "password": ("password", "pass", "authpassword", "pwd"),
    "enable": ("enable", "enablesecret", "secret", "authsecondary", "enablepassword"),
    "platform": ("platform", "os", "devicetype", "driver", "nos"),
    "transport": ("transport",),
    "strictkey": ("strictkey", "authstrictkey", "stricthostkey", "hostkeychecking"),
}


def _canon(key: str) -> str:
    """Normalise a key for matching: lower-case, drop spaces/dashes/underscores."""
    return key.lower().replace(" ", "").replace("-", "").replace("_", "")


def _pick(raw: dict[str, Any], aliases: tuple[str, ...]) -> Optional[Any]:
    """First value in `raw` whose normalised key is one of `aliases`."""
    wanted = set(aliases)
    for k, v in raw.items():
        if _canon(k) in wanted:
            return v
    return None


def _as_bool(v: Any) -> bool:
    if isinstance(v, bool):
        return v
    return str(v).strip().lower() in ("1", "true", "yes", "on", "y")


@dataclass
class Device:
    """A resolved connection target — everything AsyncScrapli needs to open."""

    host: str
    platform: str = "cisco_iosxe"
    port: int = 22
    username: str = ""
    password: str = ""
    enable: str = ""
    transport: str = "asyncssh"
    strict_key: bool = False

    def conn_args(self) -> dict[str, Any]:
        """Keyword args for the AsyncScrapli factory."""
        args: dict[str, Any] = {
            "host": self.host,
            "port": self.port,
            "platform": self.platform,
            "transport": self.transport,
            "auth_username": self.username,
            "auth_password": self.password,
            "auth_strict_key": self.strict_key,
        }
        if self.enable:
            args["auth_secondary"] = self.enable
        return args


def parse_settings(raw: Optional[dict[str, Any]]) -> tuple[Optional[Device], str]:
    """Resolve a settings profile into a Device. Returns (device, "") on success
    or (None, reason) on failure — the reason names the fix, since it lands on the
    node. Matches keys leniently (case/space/dash/underscore-insensitive)."""
    if not raw:
        return None, "no connection: pick a Scrapli device settings profile in the node drawer"

    host = _pick(raw, _ALIASES["host"])
    if not host or not str(host).strip():
        return None, (
            "settings missing a host: the profile needs a host/IP "
            f"(keys seen: {', '.join(sorted(raw.keys())) or 'none'})"
        )

    platform_raw = _pick(raw, _ALIASES["platform"])
    platform = "cisco_iosxe"
    if platform_raw:
        p = _canon(str(platform_raw))
        if p not in _PLATFORM_SYNONYMS:
            return None, (
                f"unknown platform {platform_raw!r}: use one of "
                f"{', '.join(sorted(CORE_PLATFORMS))} (or ios/nxos/xr/eos/junos)"
            )
        platform = _PLATFORM_SYNONYMS[p]

    transport_raw = _pick(raw, _ALIASES["transport"])
    transport = "asyncssh"
    if transport_raw:
        t = _canon(str(transport_raw))
        if t in ("ssh", "asyncssh"):
            transport = "asyncssh"
        elif t in ("telnet", "asynctelnet"):
            transport = "asynctelnet"
        else:
            return None, f"unknown transport {transport_raw!r}: use ssh or telnet"

    port_raw = _pick(raw, _ALIASES["port"])
    port = 23 if transport == "asynctelnet" else 22
    if port_raw not in (None, ""):
        try:
            port = int(port_raw)
        except (TypeError, ValueError):
            return None, f"invalid port {port_raw!r}: must be a whole number"

    device = Device(
        host=str(host).strip(),
        platform=platform,
        port=port,
        username=str(_pick(raw, _ALIASES["username"]) or "").strip(),
        password=str(_pick(raw, _ALIASES["password"]) or ""),
        enable=str(_pick(raw, _ALIASES["enable"]) or ""),
        transport=transport,
        strict_key=_as_bool(_pick(raw, _ALIASES["strictkey"])),
    )
    return device, ""
