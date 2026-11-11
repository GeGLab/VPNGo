#!/usr/bin/env python3
"""Shared command interface for Linux, macOS and Windows launchers."""

import json
import subprocess
import sys
from pathlib import Path

from apps import AppError, add_path, find, key
from assignments import add_helper, assign, get, load, set_policy
from help_topics import get as help_for
from i18n import tr
from profiles import load as load_profiles, profile_key, register, resolve


PROJECT = Path(__file__).resolve().parent.parent
GLOBAL_COMMANDS = {"profile", "assign", "start", "stop", "switch", "status", "check", "on", "off", "policy", "helper", "version",
                   "--install-gui", "group", "app", "update", "proxy"}
TEMP_FLAGS = {"--temp"}
DETACH_FLAGS = {"-d", "--detach"}


def version():
    """Release builds ship a VERSION file; a source checkout reports dev."""
    path = PROJECT / "VERSION"
    return path.read_text(encoding="utf-8").strip() if path.is_file() else "dev"


def backend(*arguments):
    if sys.platform == "win32":
        command = ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                   str(PROJECT / "windows/vpngo.ps1"), *arguments]
    elif sys.platform == "darwin":
        command = [str(PROJECT / "macos/vpngo"), *arguments]
    else:
        command = [str(PROJECT / "linux/vpngo"), *arguments]
    return subprocess.run(command, check=False).returncode


def configure_profile(path, profile):
    profile = profile_key(profile)
    if sys.platform in {"darwin", "win32"}:
        result = subprocess.run([sys.executable, str(PROJECT / "shared/generate_mihomo.py"), path, profile], check=False)
        if result.returncode:
            return result.returncode
        return subprocess.run([sys.executable, str(PROJECT / "shared/managed.py"), "reload"], check=False).returncode
    source = register(path, profile)
    print(tr("profile_configured", profile=profile, path=source))
    return 0


def import_profiles(paths):
    from profiles import import_profiles as save_all
    saved, failed = save_all(paths)
    for name, origin in saved.items():
        print(tr("profile_imported", profile=name, path=origin))
    for origin, error in failed:
        print(tr("profile_import_failed", path=origin, error=error), file=sys.stderr)
    if not saved and not failed:
        raise AppError(tr("profile_import_none"))
    if saved and sys.platform in {"darwin", "win32"}:
        subprocess.run([sys.executable, str(PROJECT / "shared/managed.py"), "reload"], check=False,
                       stdout=subprocess.DEVNULL)
    if saved:
        print(tr("profile_import_done", count=len(saved)))
    return 1 if failed else 0


def migrate_profiles():
    """Encrypt profiles saved as plain .conf paths by older versions; never blocks the command."""
    from profiles import migrate
    try:
        for path in migrate():
            print(tr("profile_migrated", path=path), file=sys.stderr)
    except AppError as error:
        print(f"vpngo: {error}", file=sys.stderr)


def running_routes():
    """Route of every running app, keyed by app name; never asks for a password."""
    from state import linux_routes, mihomo_routes
    return linux_routes() if sys.platform.startswith("linux") else mihomo_routes()


def group_step(action, application, state, profile=None):
    """The command that brings one member to the group action, or None when it is already there."""
    if action == "on":
        return None if state == "vpn" else ["start", application] if state == "stopped" else ["on", application]
    if action == "off":
        return ["off", application] if state in {"vpn", "partial"} else None
    if action == "stop":
        return None if state == "stopped" else ["stop", application]
    # A running app on the VPN switches live; the others keep the profile for their next start.
    return ["switch", application, profile] if state == "vpn" else ["assign", application, profile]


def group_command(args):
    from groups import add, group_key, load as load_groups, members, remove
    if args == ["list"]:
        data = load_groups()
        print("\n".join(f"{name}: {', '.join(item['apps'])}" for name, item in sorted(data.items()))
              or "No groups. Create one with: vpngo group add <group> <app>...")
        return 0
    if len(args) >= 3 and args[0] == "add":
        for application, other in add(args[1], args[2:]).items():
            print(f"{application} moved from group '{other}'.")
        print(f"Group '{group_key(args[1])}': {', '.join(members(args[1]))}.")
        return 0
    if len(args) == 3 and args[0] == "rename":
        from groups import rename
        print(f"Group '{group_key(args[1])}' is now '{rename(args[1], args[2])}'.")
        return 0
    if len(args) >= 2 and args[0] == "remove":
        remove(args[1], args[2:])
        print(f"Removed {', '.join(args[2:])} from group '{group_key(args[1])}'." if args[2:]
              else f"Group '{group_key(args[1])}' removed; its apps were not changed.")
        return 0
    if not (len(args) == 2 and args[0] in {"on", "off", "stop"} or len(args) == 3 and args[0] == "switch"):
        return usage()
    action, name = args[0], group_key(args[1])
    profile = profile_key(args[2]) if action == "switch" else None
    if profile:
        resolve(profile)
    routes = running_routes()
    failed = []
    for application in members(name):
        step = group_step(action, application, routes.get(application, {}).get("state", "stopped"), profile)
        if step is None:
            print(f"{application}: already {'stopped' if action == 'stop' else 'on the VPN' if action == 'on' else 'off the VPN'}.")
            continue
        try:
            code = main(step)
        except (AppError, OSError, ValueError, KeyError, json.JSONDecodeError) as error:
            print(f"vpngo: {application}: {error}", file=sys.stderr)
            code = 1
        if code:
            failed.append(application)
    if failed:
        print(f"vpngo: group '{name}' did not finish for: {', '.join(failed)}.", file=sys.stderr)
        return 1
    return 0


def remove_app(application):
    import groups
    from apps import forget
    from assignments import forget as forget_assignment
    name = key(application)
    if name in running_routes():
        raise AppError(f"{name} is running. Stop it first with: vpngo stop {name}")
    removed = [forget(name), forget_assignment(name)]
    groups.forget(name)
    if sys.platform in {"darwin", "win32"}:
        from managed import load_managed, reload_runtime, save_managed
        data = load_managed()
        if data.pop(name, None) is not None:
            save_managed(data)
            removed.append(True)
            reload_runtime()
    if not any(removed):
        raise AppError(f"'{name}' is not registered.")
    print(f"{name} removed from vpngo. The program itself was not changed.")
    return 0


def remove_profile(profile):
    from profiles import unregister
    name = profile_key(profile)
    if name not in load_profiles():
        raise AppError(f"VPN profile '{name}' was not found.")
    users = {application for application, item in load().items() if item.get("profile", "default") == name}
    users |= {application for application, route in running_routes().items() if route.get("active_profile") == name}
    if sys.platform in {"darwin", "win32"}:
        from managed import load_managed
        users |= {application for application, item in load_managed().items() if item.get("profile") == name}
    if users:
        raise AppError(f"Profile '{name}' is used by {', '.join(sorted(users))}. "
                       "Give them another profile (or remove them) first.")
    unregister(name)
    if sys.platform in {"darwin", "win32"}:
        subprocess.run([sys.executable, str(PROJECT / "shared/managed.py"), "reload"], check=False,
                       stdout=subprocess.DEVNULL)
    print(f"VPN profile '{name}' removed, with vpngo's encrypted copy.")
    return 0


def usage(exit_code=2, full=False):
    print(tr("help" if full else "usage"), file=sys.stderr if exit_code else sys.stdout)
    return exit_code


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        return usage()
    command = args[0]
    if command not in {"version", "help", "--help", "-h", "--install-gui", "update", "proxy"} and args[1:] != ["--json"]:
        migrate_profiles()
    if sys.platform in {"darwin", "win32"} and command not in {"version", "help", "--help", "-h", "--install-gui", "update", "proxy"}:
        from managed import reconcile_temporary
        reconcile_temporary()
    if command in {"help", "--help", "-h"}:
        if len(args) == 1:
            return usage(0, full=True)
        topic = " ".join(args[1:])
        description = help_for(topic)
        if description is None:
            print(tr("help_unknown", topic=topic), file=sys.stderr)
            return 2
        print(description)
        return 0
    if command == "version" and len(args) == 1:
        print(f"vpngo {version()}")
        return 0
    if command == "status" and args[1:] == ["--json"]:
        from state import snapshot
        print(json.dumps(snapshot(version()), indent=2))
        return 0
    if command == "update" and args[1:] in ([], ["--check"]):
        from self_update import update
        return update(version(), check_only=args[1:] == ["--check"])
    if command == "proxy":
        from proxy import command as proxy_command
        result = proxy_command(args[1:], version())
        return usage() if result is None else result
    if command == "--install-gui" and len(args) == 1:
        from gui_install import install
        return install()
    if command == "profile":
        if len(args) == 2 and args[1] == "list":
            print("\n".join(sorted(load_profiles())) or "No VPN profiles configured.")
            return 0
        if len(args) == 4 and args[1] == "add":
            return configure_profile(args[3], args[2])
        if len(args) >= 3 and args[1] == "import":
            return import_profiles(args[2:])
        if len(args) == 3 and args[1] == "remove":
            return remove_profile(args[2])
        return usage()
    if command == "group":
        return group_command(args[1:])
    if command == "app" and len(args) == 3 and args[1] == "remove":
        return remove_app(args[2])
    if command == "assign" and len(args) == 3:
        item = assign(args[1], args[2])
        print(f"{args[1]} assigned to profile '{item['profile']}'.")
        return 0
    direct_temp = command in TEMP_FLAGS and len(args) in {3, 4} and (len(args) == 3 or args[3] in DETACH_FLAGS)
    start_temp = (command == "start" and len(args) in {4, 5} and args[3] in TEMP_FLAGS and
                  (len(args) == 4 or args[4] in DETACH_FLAGS))
    if direct_temp or start_temp:
        profile, application = (args[1], args[2]) if direct_temp else (args[2], args[1])
        profile = profile_key(profile)
        resolve(profile)
        arguments = ["temp" if sys.platform == "win32" else "--temp", profile, application]
        if len(args) == (4 if direct_temp else 5):
            arguments.append("detach" if sys.platform == "win32" else "-d")
        return backend(*arguments)
    if command == "start" and len(args) in {2, 3}:
        application = args[1]
        profile = args[2] if len(args) == 3 else get(application)["profile"]
        resolve(profile)
        if sys.platform in {"darwin", "win32"} and get(application)["killswitch"]:
            raise AppError("A fail-closed per-app kill switch is not available on this platform.")
        result = backend(application, "start", profile)
        if result == 0 and len(args) == 3:
            assign(application, profile)
        return result
    if command == "switch" and len(args) == 3:
        application, profile = args[1], profile_key(args[2])
        resolve(profile)
        if sys.platform in {"darwin", "win32"}:
            result = subprocess.run([sys.executable, str(PROJECT / "shared/control.py"),
                                     application, "switch", profile], check=False).returncode
        else:
            result = backend(application, "switch", profile)
        if result == 0:
            assign(application, profile)
        return result
    if command == "stop" and len(args) == 2:
        return backend(args[1], "stop")
    if command == "check" and len(args) == 2:
        if sys.platform in {"darwin", "win32"}:
            raise AppError("vpngo check is available on Linux only for now.")
        return backend(args[1], "check")
    if command in {"status", "on", "off"} and len(args) == 2:
        result = backend(args[1], command)
        if result == 0 and command == "status":
            item = get(args[1])
            print(f"Saved settings for next start: profile {item['profile']}; kill switch "
                  f"{'on' if item['killswitch'] else 'off'}; DNS isolation "
                  f"{'on' if item['dns'] else 'off'}")
        return result
    if command == "policy" and len(args) == 4:
        application, policy, value = args[1:]
        if policy not in {"killswitch", "dns"}:
            return usage()
        if value not in {"on", "off"}:
            return usage()
        if value == "on" and sys.platform in {"darwin", "win32"}:
            raise AppError(f"Strict per-app {policy} is unavailable on {sys.platform}; "
                           "the routing backend cannot guarantee it.")
        if policy == "dns" and value == "on" and not get(application)["killswitch"]:
            raise AppError("Enable the kill switch before DNS isolation.")
        if policy == "killswitch" and value == "off" and get(application)["dns"]:
            raise AppError("Disable DNS isolation before disabling the kill switch.")
        item = set_policy(application, policy, value == "on")
        print(f"{application}: {policy} {'on' if item[policy] else 'off'} "
              "(takes effect on the next start).")
        return 0
    if command == "helper" and len(args) == 4 and args[1] == "add":
        item = add_helper(args[2], args[3])
        print(f"Helper registered for {args[2]}: {item['helpers'][-1]} (takes effect on the next start).")
        return 0
    return usage()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (AppError, OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(f"vpngo: {error}", file=sys.stderr)
        sys.exit(1)
