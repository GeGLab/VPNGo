"""vpngo proxy: a local SOCKS5 listener for one WireGuard profile.

Other programs (the Annoy app, for its per-server routes) send only the
connections they choose through it. Mihomo runs the WireGuard tunnel in user
space: no TUN, no route or DNS change on the computer. The listener binds to
loopback only. Every connection it receives goes through the profile; there is
no direct fallback, so a dead tunnel fails instead of leaking.
"""

import json
import os
import shutil
import signal
import socket
import subprocess
import sys
import time

from apps import mihomo_dir
from generate_mihomo import private_write, profile_proxy, scalar
from profiles import load as load_profiles, parsed, profile_key

STATE = mihomo_dir() / "proxy"
START_TIMEOUT = 20


def mihomo():
    """Mihomo's binary: VPNGO_MIHOMO, then PATH."""
    configured = os.environ.get("VPNGO_MIHOMO")
    if configured:
        return configured if os.path.isfile(configured) else None
    return shutil.which("mihomo") or (shutil.which("mihomo.exe") if os.name == "nt" else None)


def problem():
    if not mihomo():
        return "Mihomo was not found. Install Mihomo or set VPNGO_MIHOMO to its path."
    return None


def build_config(name, wg, port):
    proxy = profile_proxy(name)
    dns = wg["dns"] or ["1.1.1.1", "9.9.9.9"]
    lines = [
        "mode: rule", "log-level: warning", "allow-lan: false", "ipv6: true",
        "port: 0", "socks-port: 0", "mixed-port: 0", "redir-port: 0", "tproxy-port: 0",
        "tun:", "  enable: false",
        "proxies:",
        f"  - name: {proxy}", "    type: wireguard", f"    ip: {scalar(wg['ipv4'])}",
    ]
    if wg["ipv6"]:
        lines.append(f"    ipv6: {scalar(wg['ipv6'])}")
    lines += [f"    private-key: {scalar(wg['private_key'])}", "    peers:",
              f"      - server: {scalar(wg['host'])}", f"        port: {wg['port']}",
              f"        public-key: {scalar(wg['public_key'])}", "        allowed-ips:"]
    lines += [f"          - {scalar(network)}" for network in wg["allowed"]]
    if wg["psk"]:
        lines.append(f"        pre-shared-key: {scalar(wg['psk'])}")
    if wg["keepalive"]:
        lines.append(f"        persistent-keepalive: {wg['keepalive']}")
    # Names are resolved inside the tunnel, by the profile's DNS servers.
    lines += ["    udp: true", f"    mtu: {wg['mtu']}", "    remote-dns-resolve: true", "    dns:"]
    lines += [f"      - {scalar(server)}" for server in dns]
    lines += ["listeners:", f"  - name: {proxy}-in", "    type: socks", "    listen: 127.0.0.1",
              f"    port: {port}", "    udp: true", f"    proxy: {proxy}",
              "rules:", f"  - {scalar(f'MATCH,{proxy}')}"]
    return "\n".join(lines) + "\n"


def free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


def listening(port):
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.5):
            return True
    except OSError:
        return False


def alive(pid):
    if not isinstance(pid, int) or pid <= 0:
        return False
    if os.name == "nt":
        out = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/NH"], capture_output=True, text=True, check=False).stdout
        return str(pid) in out
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def read_state(name):
    try:
        data = json.loads((STATE / name / "state.json").read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def running(name):
    state = read_state(name)
    if alive(state.get("pid")) and isinstance(state.get("port"), int) and listening(state["port"]):
        return state
    return None


def start(name):
    name = profile_key(name)
    if name not in load_profiles():
        raise ValueError(f"Profile '{name}' does not exist.")
    current = running(name)
    if current:
        return current["port"]
    binary = mihomo()
    if not binary:
        raise ValueError(problem())
    stop(name)
    folder = STATE / name
    folder.mkdir(parents=True, exist_ok=True)
    if os.name == "posix":
        os.chmod(folder, 0o700)
    port = free_port()
    config = folder / "config.yaml"
    private_write(config, build_config(name, parsed(name), port))
    options = {"stdin": subprocess.DEVNULL, "stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL}
    if os.name == "nt":
        options["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS | subprocess.CREATE_NO_WINDOW
    else:
        options["start_new_session"] = True
    process = subprocess.Popen([binary, "-d", str(folder), "-f", str(config)], **options)
    deadline = time.monotonic() + START_TIMEOUT
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise ValueError(f"Mihomo stopped while starting profile '{name}'.")
        if listening(port):
            private_write(folder / "state.json", json.dumps({"pid": process.pid, "port": port}))
            return port
        time.sleep(0.2)
    process.kill()
    raise ValueError(f"Mihomo did not open the proxy for profile '{name}'.")


def stop(name):
    name = profile_key(name)
    state = read_state(name)
    pid = state.get("pid")
    if alive(pid):
        if os.name == "nt":
            subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True, check=False)
        else:
            os.kill(pid, signal.SIGTERM)
    try:
        (STATE / name / "state.json").unlink()
    except OSError:
        pass
    return 0


def command(args, version):
    as_json = "--json" in args
    args = [arg for arg in args if arg != "--json"]
    if args == ["list"]:
        data = {"version": version, "profiles": sorted(load_profiles()), "problem": problem()}
        print(json.dumps(data) if as_json else "\n".join(data["profiles"]) or "No VPN profiles configured.")
        return 0
    if len(args) == 2 and args[0] == "start":
        try:
            port = start(args[1])
        except (ValueError, OSError, KeyError) as error:
            if as_json:
                print(json.dumps({"error": str(error)}))
                return 1
            raise
        print(json.dumps({"port": port}) if as_json else f"SOCKS5 127.0.0.1:{port}")
        return 0
    if len(args) == 2 and args[0] == "stop":
        return stop(args[1])
    if args == ["status"]:
        status = {name: (running(name) or {}).get("port") for name in sorted(load_profiles())}
        print(json.dumps(status) if as_json else "\n".join(f"{name}: {port or 'stopped'}" for name, port in status.items()))
        return 0
    return None
