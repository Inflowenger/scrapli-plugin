"""Settings parsing — offline, no NATS, no scrapli."""
from scrapli_plugin.settings import parse_settings


def test_minimal_profile_resolves():
    dev, err = parse_settings({"host": "10.0.0.1", "username": "admin", "password": "pw"})
    assert err == ""
    assert dev.host == "10.0.0.1"
    assert dev.platform == "cisco_iosxe"  # default
    assert dev.transport == "asyncssh"
    assert dev.port == 22
    assert dev.username == "admin"


def test_lenient_keys_and_platform_synonyms():
    dev, err = parse_settings(
        {
            "Host Name": "sw1",       # spaced/cased alias for host
            "OS": "NX-OS",            # platform synonym → cisco_nxos
            "User": "netops",
            "Pass": "s3cret",
            "Enable Secret": "en",
        }
    )
    assert err == ""
    assert dev.platform == "cisco_nxos"
    assert dev.username == "netops"
    assert dev.enable == "en"


def test_platform_synonyms_table():
    cases = {
        "ios": "cisco_iosxe",
        "iosxe": "cisco_iosxe",
        "xr": "cisco_iosxr",
        "nexus": "cisco_nxos",
        "arista": "arista_eos",
        "junos": "juniper_junos",
    }
    for given, want in cases.items():
        dev, err = parse_settings({"host": "h", "platform": given})
        assert err == "" and dev.platform == want, given


def test_telnet_defaults_to_port_23():
    dev, err = parse_settings({"host": "h", "transport": "telnet"})
    assert err == ""
    assert dev.transport == "asynctelnet"
    assert dev.port == 23


def test_explicit_port_and_bool_coercion():
    dev, err = parse_settings({"host": "h", "port": "2222", "strict_key": "yes"})
    assert err == ""
    assert dev.port == 2222
    assert dev.strict_key is True


def test_missing_host_names_the_fix():
    dev, err = parse_settings({"username": "admin"})
    assert dev is None
    assert "host" in err


def test_empty_profile_points_at_the_drawer():
    dev, err = parse_settings({})
    assert dev is None
    assert "settings profile" in err


def test_unknown_platform_lists_valid_ones():
    dev, err = parse_settings({"host": "h", "platform": "windows"})
    assert dev is None
    assert "cisco_iosxe" in err


def test_bad_port_rejected():
    dev, err = parse_settings({"host": "h", "port": "twenty-two"})
    assert dev is None
    assert "port" in err


def test_conn_args_shape():
    dev, _ = parse_settings({"host": "h", "username": "u", "password": "p", "enable": "e"})
    args = dev.conn_args()
    assert args["host"] == "h"
    assert args["platform"] == "cisco_iosxe"
    assert args["auth_username"] == "u"
    assert args["auth_secondary"] == "e"  # only present when enable is set
    assert "auth_secondary" in args


def test_conn_args_omits_empty_enable():
    dev, _ = parse_settings({"host": "h"})
    assert "auth_secondary" not in dev.conn_args()
