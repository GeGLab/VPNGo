"""vpngo proxy: config for a loopback SOCKS5 listener, and the JSON the Annoy app reads."""

import atexit
import base64
import contextlib
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "shared"))
TEST_HOME = Path(tempfile.mkdtemp(prefix="vpngo-proxy-test-"))
atexit.register(shutil.rmtree, TEST_HOME, ignore_errors=True)
os.environ.update(HOME=str(TEST_HOME), XDG_CONFIG_HOME=str(TEST_HOME / ".config"),
                  APPDATA=str(TEST_HOME / "AppData"), LOCALAPPDATA=str(TEST_HOME / "LocalAppData"))
os.environ.pop("VPNGO_MIHOMO", None)

import commands
import profiles
import proxy

KEY = base64.b64encode(bytes(range(32))).decode()
CONF = f"""[Interface]
PrivateKey = {KEY}
Address = 10.2.0.2/32
DNS = 10.2.0.1

[Peer]
PublicKey = {KEY}
AllowedIPs = 0.0.0.0/0, ::/0
Endpoint = 203.0.113.7:51820
"""


def run(*args):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = commands.main(["proxy", *args])
    return code, out.getvalue()


class ProxyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = TEST_HOME / "brasil.conf"
        path.write_text(CONF, encoding="utf-8")
        profiles.register(path, "brasil")

    def test_config_listens_on_loopback_and_never_goes_direct(self):
        config = proxy.build_config("brasil", profiles.parsed("brasil"), 41000)
        self.assertIn("    listen: 127.0.0.1\n    port: 41000\n", config)
        self.assertIn("  - \"MATCH,vpngo-wireguard-brasil\"", config)
        self.assertNotIn("DIRECT", config)
        self.assertIn("tun:\n  enable: false", config)
        self.assertIn("    remote-dns-resolve: true\n    dns:\n      - \"10.2.0.1\"", config)
        self.assertIn("allow-lan: false", config)

    def test_list_reports_profiles_and_missing_mihomo(self):
        with patch.object(proxy.shutil, "which", return_value=None):
            code, out = run("list", "--json")
        self.assertEqual(code, 0)
        data = json.loads(out)
        self.assertEqual(data["profiles"], ["brasil"])
        self.assertIn("Mihomo", data["problem"])

    def test_start_errors_come_back_as_json(self):
        with patch.object(proxy.shutil, "which", return_value=None):
            code, out = run("start", "brasil", "--json")
        self.assertEqual(code, 1)
        self.assertIn("Mihomo", json.loads(out)["error"])
        code, out = run("start", "nope", "--json")
        self.assertEqual(code, 1)
        self.assertIn("nope", json.loads(out)["error"])

    def test_unknown_subcommand_shows_usage(self):
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(commands.main(["proxy", "jump"]), 2)


if __name__ == "__main__":
    unittest.main()
