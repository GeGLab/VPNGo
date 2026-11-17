# vpngo

Route selected desktop applications through different WireGuard VPN profiles while every other application keeps using your usual connection.

```text
browser-app  ──► germany.conf ──► VPN exit A
chat-app     ──► brazil.conf  ──► VPN exit B
other apps   ──► usual network
```

vpngo is a small command-line launcher. You register WireGuard `.conf` files as named profiles, assign a profile to an application, and start the application through vpngo. You can run several applications on different profiles at the same time and switch one of them to another exit while it is running. On macOS, routing uses Mihomo process rules inside a shared TUN. On Windows, ProxiFyre redirects selected processes into local Mihomo SOCKS listeners without a TUN, default-route changes, or a system proxy. Both have [important limits](#platform-limits) for DNS, helpers and processes with the same name.

The project was built and tested with the **free WireGuard configurations from Proton VPN**. Any provider works, paid or free, including a WireGuard server you host yourself, if it gives you a standard WireGuard client file that meets the [profile requirements](#profile-requirements).

## First Time

Follow the step-by-step guide for your system. It covers everything from installing what vpngo needs to checking that the app is on the VPN.

| System | English | Português |
| --- | --- | --- |
| Linux | [Guide](docs/HOWTO.md#2-linux) | [Guia](docs/HOWTO.pt-BR.md#2-linux) |
| Windows | [Guide](docs/HOWTO.md#3-windows) | [Guia](docs/HOWTO.pt-BR.md#3-windows) |
| macOS | [Guide](docs/HOWTO.md#4-macos) | [Guia](docs/HOWTO.pt-BR.md#4-macos) |

Every system starts with the same first step: [get your VPN file](docs/HOWTO.md#1-get-your-vpn-file) ([pt-BR](docs/HOWTO.pt-BR.md#1-pegue-seu-arquivo-de-vpn)).

## Contents

- [First Time](#first-time)
- [How it works](#how-it-works)
- [Project status](#project-status)
- [Install](#install)
- [Get a WireGuard profile](#get-a-wireguard-profile)
  - [Free Proton VPN configuration (reference setup)](#free-proton-vpn-configuration-reference-setup)
  - [Paid plans and other providers](#paid-plans-and-other-providers)
  - [Provider compatibility](#provider-compatibility)
  - [Profile requirements](#profile-requirements)
- [Quick start](#quick-start)
- [Commands](#commands)
- [Graphical interface](#graphical-interface)
- [Routing and isolation](#routing-and-isolation)
- [Files, secrets and language](#files-secrets-and-language)
- [Development](#development)
- [Contributing](#contributing)
- [License](#license)

## How it works

| | Linux | macOS | Windows |
| --- | --- | --- | --- |
| Routing engine | vopono | Mihomo | Mihomo + ProxiFyre 2.6.4+ + Windows Packet Filter |
| Per-app mechanism | Network namespace per app | Shared TUN and process rules | Explicit process allowlist; TCP/UDP redirected into an authenticated loopback SOCKS listener per app |
| Host routing | App namespace | Shared system TUN routes | Default routes, system proxy and system DNS stay as configured |
| What `start` does | Closes and relaunches the app in its namespace | Prepares TUN rules and relaunches the app | Starts a local proxy, applies process filters, then relaunches the app |

The launchers for each system (`linux/vpngo`, `macos/vpngo`, `windows/vpngo.ps1`) share the same profile, assignment and app-discovery code in `shared/`, so the commands are the same everywhere.

## Project status

> **Linux is tested; macOS and Windows still need device testing.**
>
> Linux application routing and `on`/`off` reconnection were tested on Arch Linux. During a live Linux switch between two WireGuard peers, the same probe process and namespace kept running while the public IPv4 changed from the first VPN exit to the second. One DNS lookup failed during the transition, and the next request recovered without a manual reload. Persistent assignments, multi-profile Mihomo config generation, selection logic and Linux rollback have automated tests. Mihomo v1.19.32 accepts a generated two-profile configuration. Simultaneous live tunnels on macOS and Windows have not been run on real devices. See [platform limits](#platform-limits).

## Install

First install what your system needs:

| System | Requirements |
| --- | --- |
| Linux | Python 3, vopono, `wg`, `ip`, `ss`, `pgrep`, `ping`, `nft` or `iptables`; `bwrap` for optional DNS isolation |
| macOS | Python 3, Mihomo on `PATH` or `VPNGO_MIHOMO=/absolute/path/mihomo` |
| Windows | Python 3, `mihomo.exe` on `PATH` or `VPNGO_MIHOMO`, ProxiFyre 2.6.4+ and Windows Packet Filter; see [Windows backend setup](docs/WINDOWS.md) |

Then install vpngo from the [latest release](https://github.com/GustavoHSCruz/VPNGo/releases/latest). Each installer downloads the archive for your system, checks it against `SHA256SUMS`, installs it in `~/.local/share/vpngo` (`%LOCALAPPDATA%\vpngo` on Windows) and creates the `vpngo` command. Running it again later upgrades in place and keeps your settings.

**Linux**

```sh
curl -fLO https://github.com/GustavoHSCruz/VPNGo/releases/latest/download/install-linux.sh
sh install-linux.sh
```

**macOS**

```sh
curl -fLO https://github.com/GustavoHSCruz/VPNGo/releases/latest/download/install-macos.sh
sh install-macos.sh
```

**Windows** (PowerShell)

```powershell
Invoke-WebRequest https://github.com/GustavoHSCruz/VPNGo/releases/latest/download/install-windows.ps1 -OutFile install-windows.ps1
powershell -ExecutionPolicy Bypass -File .\install-windows.ps1
```

**Package managers.** Each stable release is also published to:

| System | Command |
| --- | --- |
| Arch Linux, CachyOS, Manjaro | `curl -fLO https://github.com/GustavoHSCruz/VPNGo/releases/latest/download/PKGBUILD` in an empty folder, then `makepkg -si`; install `vopono-bin` from the AUR first |
| Ubuntu, Debian | `sudo apt install ./vpngo_<version>-1_all.deb`, downloaded from the release; install [vopono's `.deb`](https://github.com/jamesmcm/vopono/releases) first |
| Fedora | `sudo dnf install ./vpngo-<version>-1.noarch.rpm`, downloaded from the release; install [vopono's `.rpm`](https://github.com/jamesmcm/vopono/releases) first |
| macOS (Homebrew) | `brew tap GustavoHSCruz/vpngo && brew trust GustavoHSCruz/vpngo && brew install vpngo` (also installs Mihomo; Homebrew asks you to trust a tap before installing from it) |
| Windows (Scoop) | `scoop bucket add vpngo https://github.com/GustavoHSCruz/scoop-vpngo`, then `scoop install vpngo` (also installs Python and Mihomo) |

Package managers install vpngo system-wide or in their own folders and update it with their usual upgrade command.

Check the installation with `vpngo version`. Each release also has the archives for manual download (`.tar.gz` for Linux and macOS, `.zip` for Windows); extract one and run the installer inside it (`linux/install.sh`, `macos/install.sh` or `windows\install.ps1`).

**From source.** Clone the repository and run the same inner installer from the checkout. `vpngo version` then reports `dev`.

```sh
git clone https://github.com/GustavoHSCruz/VPNGo.git
cd VPNGo
./linux/install.sh      # or ./macos/install.sh; on Windows: powershell -ExecutionPolicy Bypass -File .\windows\install.ps1
```

What each installer does, and which permission vpngo asks for later:

- **Linux** (`linux/install.sh`): checks the dependencies and links `vpngo` into `~/.local/bin`. `vpngo start` asks for your password with `sudo` to create the app's network namespace.
- **macOS** (`macos/install.sh`): links `vpngo` into `~/.local/bin`. `vpngo start` asks for your password with `sudo` to start Mihomo.
- **Windows** (`windows/install.ps1`): creates `vpngo.cmd` in `%USERPROFILE%\bin` and adds that folder to your user `PATH`. `vpngo start` requests administrator permission to apply ProxiFyre process filters. Mihomo runs without elevation and without a TUN. Install the additional driver explicitly with `windows/install-backend.ps1` first; it is not installed by the normal vpngo installer.

The vpngo launchers can be installed without administrator rights. The separate Windows backend installer requires administrator rights to install Windows Packet Filter and ProxiFyre. The command runs from the installed folder (or your checkout), so don't move it. Open a new terminal if `vpngo` is not found.

The [step-by-step guide](docs/HOWTO.md) ([Português](docs/HOWTO.pt-BR.md)) has complete instructions for each system: dependencies with copy-and-paste commands, what each installer does, the permissions it asks for, and troubleshooting.

## Get a WireGuard profile

vpngo does not create VPN accounts or keys. It uses a WireGuard client file exported by your VPN provider. Each `.conf` file is one profile, meaning one VPN exit.

### Free Proton VPN configuration (reference setup)

The project was developed against Proton VPN's free plan, which can export WireGuard files for its free servers. To get one:

1. Create a free account at [protonvpn.com](https://protonvpn.com) if you do not have one.
2. Sign in at [account.protonvpn.com](https://account.protonvpn.com).
3. Open **Downloads** and scroll to **WireGuard configuration**.
4. Enter a name for the configuration, such as `vpngo-nl`. Proton uses this name to list the key, so you can revoke it later.
5. Choose your platform (**GNU/Linux**, **macOS** or **Windows**). The file format is the same on every platform.
6. Under VPN options, leave the defaults. Free accounts can only toggle **VPN Accelerator**; NetShield, Moderate NAT and port forwarding need a paid plan.
7. Pick a server from the free server list and click **Create**. When the file is ready, download it and save it as a `.conf` file.
8. Repeat for each exit you want as a separate profile. Every file has its own private key.

A Proton file looks like this (keys and addresses replaced):

```ini
[Interface]
# Key for vpngo-nl
# VPN Accelerator = on
PrivateKey = <your-private-key>
Address = 10.2.0.2/32
DNS = 10.2.0.1

[Peer]
# NL-FREE#1
PublicKey = <server-public-key>
AllowedIPs = 0.0.0.0/0, ::/0
Endpoint = <server-ip>:51820
```

Store the files outside the repository and readable only by you, then register them:

```sh
mkdir -p ~/.config/wireguard && chmod 700 ~/.config/wireguard
mv ~/Downloads/vpngo-nl.conf ~/.config/wireguard/
chmod 600 ~/.config/wireguard/*.conf
vpngo profile add netherlands ~/.config/wireguard/vpngo-nl.conf
```

Free plan limits to keep in mind:

- **Simultaneous connections.** The free plan allows a very small number of simultaneous VPN connections (one at the time of writing). Running two apps on two free profiles at the same time can exceed it; the second tunnel may fail its handshake or drop the first. Check Proton's current plan terms.
- **Server choice.** Free files only work with free servers. Choose the country when you create the file; you cannot change it later by editing the file.
- **Key lifetime.** The account page lists the configurations you created. If a profile stops completing handshakes, check whether its key was revoked or expired there, then create a new file and run `vpngo profile add` with the same name to replace it.

Proton's own guide is at [How to download WireGuard configuration files](https://protonvpn.com/support/wireguard-configurations/).

### Paid plans and other providers

Paid Proton plans and other providers are supported if they export a standard WireGuard client file. Most providers that support WireGuard have a configuration generator in the account area or let you build a file manually. A self-hosted WireGuard server also works. vpngo does not depend on anything specific to Proton.

- **Paid Proton plans** use the same download page. They add more servers and options such as NetShield and port forwarding. Port forwarding needs an application that can use it; vpngo only routes the traffic.
- **More simultaneous profiles.** With a plan that allows several connections, you can run one app per profile at the same time. On Linux each profile lives in its own namespace, so profiles with the same `Address` do not collide. If two profiles on macOS or Windows fail together, give the second file a different tunnel address, as Proton's guide recommends for multiple tunnels (for Proton: `Address = 10.3.0.2/32` and `DNS = 10.3.0.1`). Only do this with addresses your provider accepts.
- **Other protocols are not supported.** OpenVPN, IKEv2 and proprietary apps that do not export a WireGuard file cannot be used. Only the WireGuard protocol is supported.

### Provider compatibility

Some popular VPN providers, in no particular order. Only Proton VPN has been tested with vpngo so far; the other rows show whether the provider documents how to get a WireGuard file. Reports from other providers are welcome (see [Contributing](#contributing)).

| Provider | Tested | Works | Errors found | WireGuard file documentation |
| --- | --- | --- | --- | --- |
| Proton VPN | Yes (free plan, Linux) | Yes | 0 | [Yes](https://protonvpn.com/support/wireguard-configurations/) |
| NordVPN | No | — | — | Yes: Nord Account → manual setup ([report](https://www.techradar.com/vpn/vpn-services/no-more-scripts-nordvpn-finally-lets-you-download-wireguard-files-directly-and-it-could-make-your-router-up-to-five-times-faster)) |
| ExpressVPN | No | — | — | None found |
| Surfshark | No | — | — | [Yes](https://support.surfshark.com/hc/en-us/articles/32395023041810-How-to-set-up-WireGuard-on-Raspberry-Pi) |
| CyberGhost | No | — | — | No: [WireGuard only through its apps](https://support.cyberghostvpn.com/hc/en-us/articles/360015810460-Discover-More-About-the-WireGuard-VPN-Protocol) |
| Private Internet Access | No | — | — | Partial: [official scripts](https://github.com/pia-foss/manual-connections) create the file |
| Mullvad | No | — | — | [Yes](https://mullvad.net/help/easy-wireguard-mullvad-setup-linux/) |
| IPVanish | No | — | — | [Yes](https://www.ipvanish.com/blog/generate-wireguard-configurations/) |
| Windscribe | No | — | — | [Yes, paid plans only](https://windscribe.com/support/article/103/where-do-i-access-my-wireguard-configs) |
| PureVPN | No | — | — | [Yes](https://purevpn2.helpjuice.com/en_US/linux/how-to-setup-wireguard-on-linux); the file must be used within minutes of download |

Errors found counts problems seen while using that provider's files with vpngo. A provider without a WireGuard file cannot be used, even on a paid plan.

### Profile requirements

`vpngo profile add` checks the file and refuses it if any of these rules fails:

| Section | Field | Requirement |
| --- | --- | --- |
| `[Interface]` | `PrivateKey` | Required; a valid 32-byte base64 WireGuard key. |
| `[Interface]` | `Address` | Required; must include an IPv4 address. An IPv6 address is optional. |
| `[Interface]` | `DNS` | Optional. IP entries are used; search domains are ignored. **Required** for Linux DNS isolation (`policy <app> dns on`). |
| `[Interface]` | `MTU` | Optional; 576–9000, default 1420. |
| `[Peer]` | — | Exactly one `[Peer]` section. Files with several peers are rejected. |
| `[Peer]` | `PublicKey` | Required; a valid WireGuard key. |
| `[Peer]` | `AllowedIPs` | Required; must include `0.0.0.0/0` so all of the app's IPv4 traffic goes through the tunnel. `::/0` is recommended. |
| `[Peer]` | `Endpoint` | Required; `host:port` or `[IPv6]:port`. A hostname is resolved before connecting. |
| `[Peer]` | `PresharedKey` | Optional; validated when present. |
| `[Peer]` | `PersistentKeepalive` | Optional; 0–65535. |

A file that imports and connects in the official `wg-quick` or WireGuard app and meets these rules should work. A split-tunnel file whose `AllowedIPs` covers only some networks is rejected on purpose, because vpngo expects the app's whole route to go through the VPN.

## Quick start

```sh
vpngo profile add germany /path/to/de.conf
vpngo profile add brazil /path/to/br.conf
vpngo profile list

vpngo assign browser-app germany
vpngo assign chat-app brazil
vpngo start browser-app
vpngo start chat-app

vpngo status browser-app
vpngo switch browser-app brazil
vpngo off browser-app
vpngo on browser-app
vpngo stop browser-app
```

For a one-off run, pass an executable and a registered profile:

```sh
vpngo --temp germany /home/me/games/dota2
cd /home/me/games
vpngo --temp germany dota2
vpngo --temp germany kitty -d
```

`--temp` checks the current directory first for a bare executable name. It also accepts an absolute or relative path, then falls back to normal executable discovery. It does not save an app-to-profile assignment or register the executable. Without `-d`, the command stays active until the launched process exits. Add `-d` or `--detach` to close the original terminal while the app runs. On macOS and Windows, close any already running instance of the same program first: Mihomo routes by process name, so it cannot distinguish two copies of that program. If the temporary worker dies unexpectedly, the next command blocks its route; `vpngo stop <app>` closes the app and clears it. A surviving child process can lose the route when its parent exits normally.

Replace `browser-app` and `chat-app` with the executable names of your applications.

- `assign` saves the profile, and later starts reuse it.
- `start` closes running instances of the application and launches it on its saved profile, or on the profile you pass as a second argument.
- `switch` changes the profile of one running application without restarting it. The application has to reconnect its own connections. On Linux, vpngo checks the new WireGuard handshake before it commits the change and rolls back on failure.
- Other managed applications keep their own routes.

If vpngo cannot find the executable, register the executable or the folder that contains it, then try again:

```sh
vpngo config /path/to/app/bin
# or: vpngo config /path/to/app/executable
```

Keep the original `.conf` files at their registered paths. vpngo stores their paths, not copies.

## Commands

| Command | Effect |
| --- | --- |
| `vpngo profile add <name> <file.conf>` | Save or update a named WireGuard profile: vpngo keeps an encrypted copy, so the original file is no longer needed. |
| `vpngo profile import <folder\|file.zip\|file.conf>...` | Save every `.conf` found as a profile named after its file (`wg-NL-FREE-12.conf` becomes `wg-nl-free-12`). Folders are read without subfolders and `.zip` archives without extracting them. A refused file is reported and does not stop the others. |
| `vpngo profile list` | List registered profiles. |
| `vpngo profile remove <name>` | Forget a profile and delete its encrypted copy. Refused while an app uses it. |
| `vpngo assign <app> <profile>` | Save the profile used by future `start` commands. |
| `vpngo start <app> [profile]` | Close and launch the app on its saved or specified profile. |
| `vpngo --temp <profile> <executable> [-d\|--detach]` | Run an executable once on the profile without saving an assignment. Add `-d` to close the original terminal. `vpngo start <executable> <profile> --temp` is equivalent. |
| `vpngo stop <app>` | Close the app and end its managed VPN session. On macOS/Windows, block that app's selector while leaving Mihomo available to others. |
| `vpngo switch <app> <profile>` | Change a running app's profile and save the new assignment after success. |
| `vpngo status <app>` | Show the app's active route and saved settings. |
| `vpngo check <app>` | Linux: compare the running app's public IP and country with this computer's, and show whether each DNS server of its namespace goes through the tunnel. Exits with 1 when the app is not on the VPN. |
| `vpngo status --json` | Print every profile, group and app as JSON without asking for a password: route, start time, when the current route began and the time on each route, VPN server, byte counters of running apps (in total and since the last switch), and whether an app was opened by vpngo or outside it (running without a VPN route). Used by the graphical interface. |
| `vpngo off <app>` / `vpngo on <app>` | Intentionally select the direct route, or return to the assigned VPN. |
| `vpngo policy <app> killswitch on\|off` | Set the Linux per-app fail-closed policy for the next start. Default: on. |
| `vpngo policy <app> dns on\|off` | Set Linux resolver isolation for the next start. Default: off; needs the kill switch and a DNS IP in the profile. |
| `vpngo helper add <app> <executable>` | Register a known helper executable for Mihomo process matching. |
| `vpngo shutdown` | Windows: stop all VPNGo process filters and its local proxy; apps remain open and use their usual connection. |
| `vpngo proxy start <profile> [--json]` | Open a SOCKS5 listener on `127.0.0.1` for one profile and print its port. Mihomo runs the WireGuard tunnel in user space: no TUN, no route or DNS change. Every connection it receives goes through the profile, with no direct fallback; names resolve inside the tunnel. Needs Mihomo on every system. Used by the Annoy app to route chosen servers. |
| `vpngo proxy stop <profile>` / `vpngo proxy status [--json]` | Close that listener; list the open listeners and their ports. |
| `vpngo proxy list --json` | Profiles a proxy can use, the version, and why `proxy start` can't run (Mihomo missing), as JSON. |
| `vpngo version` | Show the installed version (`dev` in a source checkout). |
| `vpngo update [--check]` | Install the latest release over this one: it downloads the release's installer for your system, checks it against `SHA256SUMS` and runs it; settings and profiles are kept, and a failed update restores the previous version. `--check` only reports whether a newer version exists. Installs from a package manager update with that manager; a source checkout with `git pull`. |
| `vpngo --install-gui` | Download, verify and install (or upgrade) the [graphical interface](#graphical-interface). |
| `vpngo config <path>` | Register an executable, executable folder, or macOS `.app` bundle. |
| `vpngo app remove <app>` | Forget a stopped app: its registered path, saved profile, policies and group. The program itself is not changed. |
| `vpngo group add <group> <app>...` | Put apps in a group (created on first use). An app is in one group at most; adding it to another moves it. |
| `vpngo group on\|off\|stop <group>` | Act on every app in the group: `on` starts the stopped ones and returns direct ones to the VPN, `off` moves the ones on the VPN to the direct route, `stop` closes them all. One password; a failing app does not stop the others. |
| `vpngo group switch <group> <profile>` | Switch the group's apps on the VPN to the profile now; the others use it on their next start. |
| `vpngo group list` / `vpngo group remove <group> [app...]` | List groups; take apps out of a group, or delete the group (its apps stay). |
| `vpngo group rename <group> <new-name>` | Rename a group; its apps stay in it. |
| `vpngo help <command>` | Show a command's syntax and options, for example `vpngo help start`. |

The legacy commands `vpngo setup <file> [profile]`, `vpngo profiles` and the app-first form still work. On Windows, run the commands in PowerShell.

## Graphical interface

[VPNGo interface](https://github.com/GustavoHSCruz/VPNGo-gui) is an optional tray app and window for the everyday commands: start, stop, VPN on/off, switching profiles, groups, protection settings, and adding or removing profiles and apps. Each app is a tile lit by its route, with the time on its current route, a traffic trace colored by route, and its address masked until clicked (the VPN server, or the public IP on the direct route). It runs these same `vpngo` commands, so everything above still applies.

```sh
vpngo --install-gui
```

The command downloads the latest interface release, checks it against its `SHA256SUMS`, and installs it in its own Python environment (`~/.local/share/vpngo-gui`, or `%LOCALAPPDATA%\vpngo-gui` on Windows) with Qt (PySide6). The first install downloads about 250 MB unless PySide6 is already installed on the system. It creates the `vpngo-gui` command and, on Linux, an application menu entry. Run it again to upgrade. To use only the interface, without installing vpngo first, run the interface's own `install.py` instead: it uses a vpngo it finds on `PATH`, or downloads this release as its private engine. On Linux and macOS the interface asks for the sudo password in its own dialog when an action needs it; see its [README](https://github.com/GustavoHSCruz/VPNGo-gui#readme) for details and removal.

## Routing and isolation

| Capability | Linux | macOS | Windows |
| --- | --- | --- | --- |
| Simultaneous profiles | Namespace per app | Shared TUN, selector per app | Loopback SOCKS listener and selector per app |
| Live profile switch | Reconfigure and check handshake; rollback on failure | Change selector and close attributed connections | Change selector and close that listener's connections |
| Kill switch | Configurable, default on | No strict per-app guarantee | No strict per-app guarantee |
| DNS isolation | Optional namespace resolver view | No strict per-app guarantee | Windows DNS remains unchanged; no strict per-app guarantee |
| Child/helper traffic | Children inherit namespace | Best effort process rules | Main executable name and explicitly registered helper paths |

`off` explicitly selects the direct route. While it is active, the Linux `switch` command refuses to change profiles; run `on` first. Policies take effect on the next `start`.

`stop` closes the application. On Linux, vopono tears down its namespace and WireGuard session. On macOS/Windows, vpngo closes the process and its attributed connections and leaves a `REJECT` selector for a persistent app; it removes a temporary app's selector. On macOS the shared Mihomo TUN keeps serving other managed apps. On Windows the local proxy and explicit process filters keep serving other managed apps; `vpngo shutdown` stops all of them. `start` reactivates a persistent app. Its profile assignment stays saved.

### Platform limits

- **Linux namespaces.** Ordinary child processes stay on the same network, but a program that hands work to a service outside the namespace may use that service's route. DNS isolation covers resolver calls that use the app's glibc/NSS view; embedded resolvers, DoH, IPC and external services can bypass it. The kill switch relies on vopono's firewall and should be validated for your app and configuration.
- **Mihomo process rules (macOS).** Routing depends on process attribution. The final rule is `MATCH,DIRECT`, so an unmatched helper, a failed lookup or the routing engine stopping can let traffic go direct. Mihomo's global DNS resolvers are `1.1.1.1` and `9.9.9.9`; queries are not bound to the selected VPN profile. A process-name rule can include another instance with the same name. `vpngo helper add` improves matching but does not make the setup fail-closed. A true system-enforced per-app guarantee would need native OS filtering or VPN integration. See the [device checks](docs/HOWTO.md#route-checks-on-windows-and-macos).
- **Windows process filters.** ProxiFyre 2.6.4+ redirects only the generated executable allowlist to authenticated local SOCKS listeners. There is no catch-all process rule and no global TUN, DNS hijack or system-proxy change. Adding or removing an app can restart the shared filter service and briefly reconnect other managed apps. Processes with the same executable name share a route; register helpers explicitly. Windows resolver traffic stays on the existing system DNS. Unresolved process ownership and fragmented IPv6 UDP can bypass attribution, so this is not a strict kill switch or private network compartment. See [setup, rollback and checks](docs/WINDOWS.md).
- **Reconnection.** Existing connections may reconnect slowly or stay disconnected, because retry behavior belongs to the application. vpngo closes attributed Mihomo connections or Linux namespace TCP sockets, but it cannot force every program to retry. When it matters, check the public IP and DNS from inside the application.
- **Untested launchers.** Windows and macOS behavior has not been verified on real devices. Different executables with the same process name may collide in Mihomo rules; vpngo rejects known conflicts when it prepares an app.
- **Privacy scope.** vpngo changes routing only. Accounts, cookies, device identifiers and the VPN provider itself may still identify your activity.

## Files, secrets and language

| What | Linux / macOS | Windows |
| --- | --- | --- |
| Installed program (release installers) | `~/.local/share/vpngo/app/` | `%LOCALAPPDATA%\vpngo\app\` |
| Profiles, app paths, assignments, policies | `~/.config/vpngo/` | `%APPDATA%\vpngo\` |
| Linux session logs and metadata | `~/.local/state/vpngo/` | — |
| Generated Mihomo config, log and controller secret (macOS/Windows) | `~/.local/state/vpngo/mihomo/` | `%LOCALAPPDATA%\vpngo\mihomo\` |

**Profiles are stored encrypted.** `vpngo profile add` copies the `.conf` into the profiles folder, encrypted with a key the system keeps for your user, so using it needs no extra password: on Linux `systemd-creds --user` (systemd 256 or newer; otherwise the desktop keyring through `secret-tool`), on Windows DPAPI, on macOS the login Keychain. The copy can only be decrypted by your user on this machine; to move to another computer, add the original `.conf` again. Profiles saved in plain text by older versions are encrypted by the next vpngo command; a plain copy inside the profiles folder is then deleted, and vpngo tells you about one elsewhere that you may delete. On Linux, vopono still reads a plain file: vpngo writes it to a private folder in memory (`$XDG_RUNTIME_DIR`) and deletes it as soon as the app's VPN is up. On macOS and Windows, Mihomo's generated `config.yaml` holds the keys while it runs.

Your original `.conf` files and the Mihomo folder's `config.yaml` and `controller.json` contain private keys or secrets. The repository's `.gitignore` excludes `*.conf`, `*.key`, `*.wg` and logs; still, never commit, paste or attach them. vpngo writes its registry files with owner-only permissions.

Windows also writes a generated `proxifyre.json` in its Mihomo state folder. The elevated helper applies it to the official ProxiFyre installation only when that installation is unconfigured or owned by the same VPNGo user. Existing unrelated ProxiFyre settings are refused. The local SOCKS TCP/UDP path and unchanged host routes/adapters/proxy are tested; actual ProxiFyre driver routing still needs device validation.

Messages default to English (en-US). Set `VPNGO_LANG=pt-BR` for Portuguese messages (`$env:VPNGO_LANG = 'pt-BR'` in PowerShell). `VPNGO_MIHOMO` and `VPNGO_PYTHON` select custom Mihomo and Python binaries.

## Development

```text
linux/      Linux launcher (vopono), installer and DNS-isolation helper
macos/      macOS launcher and installer
windows/    PowerShell launcher, cmd shim and installer
shared/     Profiles, assignments, app discovery, Mihomo config generation, i18n
tests/      Automated tests and a manual probe app for live route checks
docs/       Setup guides in English and Portuguese
packaging/  Download-and-install scripts, .deb/.rpm, AUR, Homebrew and Scoop templates, release notes
tools/      Release build, package manifest and tagging scripts
.github/    Release workflow
```

The automated tests need no VPN connection:

```sh
python3 -m unittest discover -s tests
```

To check a live switch on Linux without closing one of your applications, use the bundled probe. It logs its public IP about every ten seconds:

```sh
vpngo config "$PWD/tests/manual/vpngo-probe"
vpngo assign vpngo-probe netherlands
vpngo start vpngo-probe
vpngo switch vpngo-probe germany
tail -n 12 ~/.local/state/vpngo/start.log
vpngo stop vpngo-probe
```

After `switch`, the logged IP should become the new exit's IP. The [step-by-step guide](docs/HOWTO.md#7-problems-and-checks) shows how to run two probes in parallel.

### Releases

Versions follow [Semantic Versioning](https://semver.org): `1.2.3`, or `1.2.3-rc.1` for a pre-release. Each release is a git tag `v1.2.3`.

To publish one, commit and push your changes on `main`, then run:

```sh
tools/tag-release.sh 1.2.3
```

The script checks that `main` is clean and matches `origin/main`, runs the tests and a local build, then creates and pushes the annotated tag `v1.2.3`. The tag starts the [Release workflow](.github/workflows/release.yml), which:

1. runs the tests;
2. builds the Linux and macOS `.tar.gz` and Windows `.zip` archives, the `.deb` and `.rpm` packages, the three download-and-install scripts and `SHA256SUMS`;
3. installs and upgrades vpngo with each installer on Linux, macOS and Windows runners;
4. installs the `.deb` on Ubuntu, the `.rpm` on Fedora and, for stable versions, builds and installs the `PKGBUILD` on Arch Linux;
5. publishes the GitHub release with install instructions and generated notes. Versions with a suffix such as `-rc.1` are marked as pre-releases;
6. for stable versions, adds a tested Arch Linux `PKGBUILD` to the release, and updates the AUR package `vpngo`, the [Homebrew tap](https://github.com/GustavoHSCruz/homebrew-vpngo) and the [Scoop bucket](https://github.com/GustavoHSCruz/scoop-vpngo), then installs vpngo from each one to check it.

The package updates need two repository secrets: `AUR_SSH_PRIVATE_KEY` (an SSH key registered in the AUR account that owns `vpngo`) and `PACKAGES_TOKEN` (a GitHub token that can push to `homebrew-vpngo` and `scoop-vpngo`). Without them the release still publishes and the workflow notes which updates it skipped. The AUR package is not published yet, because AUR registration is temporarily closed; until then, Arch users install from the release's `PKGBUILD`.

Running the workflow by hand from the Actions tab does steps 1–4 without publishing. To build locally (add `--linux-packages` with [nfpm](https://nfpm.goreleaser.com) installed to include the `.deb` and `.rpm`):

```sh
python3 tools/build_release.py --version 1.2.3 --out dist
cd dist && sha256sum -c SHA256SUMS
```

Builds are reproducible: the same commit and version always produce the same files and checksums.

## Contributing

Contributions are welcome, especially:

- test reports from **macOS and Windows** devices;
- reports from **other VPN providers and paid plans**: which provider, whether `profile add` accepted the file, and whether the route worked;
- fixes for applications whose helpers escape the route.

Include the OS, the vpngo version (`vpngo version`), the routing engine version (vopono or Mihomo), the application, and the routes or public IPs you observed. **Remove private keys, preshared keys, endpoints you consider private and controller secrets** from every report.

## License

vpngo is free software under the [Apache License 2.0](LICENSE). You may use, modify and redistribute it for any purpose, including commercially. Every copy or derived work you distribute must keep the [LICENSE](LICENSE) and [NOTICE](NOTICE) files, which credit vpngo and its author, [GustavoHSCruz](https://github.com/GustavoHSCruz), and must state the files you changed.
