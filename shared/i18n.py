"""Small CLI message catalog. English is the default language."""

import os


MESSAGES = {
    "en-US": {
        "usage": "VPNGo — route apps through WireGuard.\n"
                 "Usage: vpngo start <app> [profile]\n"
                 "       vpngo --temp <profile> <executable> [-d]\n"
                 "Run 'vpngo help' for all commands.",
        "help": "VPNGo — route apps through WireGuard.\n\n"
                "  vpngo profile add <name> <file.conf>         Save a VPN profile\n"
                "  vpngo profile import <folder|zip|file>...    Save every .conf, named after its file\n"
                "  vpngo profile list                          List profiles\n"
                "  vpngo profile remove <name>                  Forget a profile\n"
                "  vpngo assign <app> <profile>                 Save an app's profile\n"
                "  vpngo start <app> [profile]                  Start an app on the VPN\n"
                "  vpngo --temp <profile> <executable> [-d]     Run once without saving\n"
                "  vpngo start <executable> <profile> --temp [-d]  Same temporary run\n"
                "  vpngo switch <app> <profile>                 Change the active profile\n"
                "  vpngo check <app>                            Compare the app's IP and DNS with yours (Linux)\n"
                "  vpngo stop <app>                             Stop the app and VPN session\n"
                "  vpngo status <app>                           Show the app's route\n"
                "  vpngo on|off <app>                           Select VPN or direct route\n"
                "  vpngo policy <app> killswitch|dns on|off     Set routing policy\n"
                "  vpngo helper add <app> <executable>          Route a helper process\n"
                "  vpngo config <path>                          Register an app path\n"
                "  vpngo app remove <app>                       Forget a stopped app\n"
                "  vpngo group add <group> <app>...             Put apps in a group\n"
                "  vpngo group on|off|stop <group>              Act on every app in a group\n"
                "  vpngo group switch <group> <profile>         Move a group to another profile\n"
                "  vpngo group list | remove <group> [app...]   List groups, or remove one or its apps\n"
                "  vpngo group rename <group> <new-name>        Rename a group\n"
                "  vpngo version                                Show the version\n"
                "  vpngo update [--check]                       Install the latest release\n"
                "  vpngo proxy start|stop|status|list           Local SOCKS5 proxy for one profile\n"
                "  vpngo --install-gui                          Install the graphical interface\n\n"
                "  -d, --detach                                 Return to prompt while the app runs\n"
                "  vpngo help <command>                         Explain a command and its options",
        "help_unknown": "Unknown help topic '{topic}'. Run 'vpngo help' to list commands.",
        "profile_configured": "VPN profile '{profile}' saved, encrypted, from {path}. vpngo no longer needs that file.",
        "profile_migrated": "Your VPN profiles are now stored encrypted. {path} is no longer needed; delete it if you like.",
        "profiles_none": "No VPN profiles configured.",
        "check_profile": "profile {profile}",
        "check_app_ip": "App's public IP ",
        "check_your_ip": "Your public IP  ",
        "check_no_answer": "no answer",
        "check_dns": "DNS server      ",
        "check_dns_tunnel": "(through the tunnel)",
        "check_dns_direct": "(NOT through the tunnel)",
        "check_dns_resolved": "Note: DNS isolation is off and this system resolves names through systemd-resolved, "
                              "outside the tunnel; {app}'s lookups can bypass the VPN. "
                              "Turn it on with: vpngo policy {app} dns on",
        "check_failed": "Result: the app's network did not answer. Check the route with 'vpngo status'.",
        "check_same_ip": "Result: the app leaves the internet with your own IP; it is NOT on the VPN.",
        "check_not_on": "Result: {app} is not fully on the VPN. Run 'vpngo on {app}'.",
        "check_ok": "Result: the app's traffic leaves through the VPN.",
        "profile_imported": "VPN profile '{profile}' saved, encrypted, from {path}.",
        "profile_import_failed": "Skipped {path}: {error}",
        "profile_import_none": "No .conf file found to import.",
        "profile_import_done": "{count} profile(s) imported. vpngo no longer needs those files.",
        "extra_apps": "Other applications share this namespace; network was not changed.",
        "namespace_count": "Expected one running '{app}' namespace; found {count}.",
        "invalid_namespace": "Invalid network namespace name.",
        "one_wg": "Expected exactly one WireGuard interface in the application namespace.",
        "no_direct_route": "Could not find the application's direct network route.",
        "route_is_vpn": "The normal route points to the VPN; no direct route is available.",
        "no_firewall": "Could not identify the namespace firewall.",
        "unexpected_dns": "Unexpected namespace DNS file; operation cancelled.",
        "already_off": "VPN is already off for {app}.",
        "already_on": "VPN is already on for {app}.",
        "incomplete_switch": "An earlier switch is incomplete; run 'vpngo <application> on' first.",
        "rule_collision": "A network rule already uses priority {priority}; nothing was changed.",
        "off": "VPN is off for {app}. Existing connections were closed for automatic reconnection.",
        "missing_backup": "DNS backup for this session was not found; network was not changed.",
        "on": "VPN is on for {app}. Existing connections were closed for automatic reconnection.",
        "status_off": "VPN off",
        "status_on": "VPN on",
        "status_partial": "partial configuration",
        "status_stopped": "stopped and blocked",
        "status_no_session": "stopped (no VPN namespace)",
        "ipv4_route": "IPv4 route",
        "config_created": "Mihomo configuration created at {path}.",
        "config_private": "Keep this file private: it contains your WireGuard private key.",
        "controller_unavailable": "Mihomo's local controller is unavailable. Start Mihomo first.",
        "controller_bad": "Unexpected response from Mihomo's local controller.",
        "controller_on": "VPN is on for {app}. Its old connections were closed for automatic reconnection.",
        "controller_off": "VPN is off for {app}. Its old connections were closed for automatic reconnection.",
        "controller_status": "{app}: {state}",
        "not_configured": "Mihomo is not set up yet. Start the app with 'vpngo start <app> <profile>' first.",
        "reconnect_failed": "Route switched, but old TCP connections could not be closed: {detail}",
        "missing_wg_file": "WireGuard configuration not found: {path}. Run 'vpngo setup <wireguard.conf>'.",
        "missing_command": "Required command not found: {name}.",
        "starting": "Starting {app} through WireGuard...",
        "started": "{app} started through the VPN. You can close this terminal.",
        "start_failed": "Application did not start through vopono. See {path}.",
        "authentication_failed": "Administrator authentication failed.",
        "unsafe_process": "Refusing to close shared system process '{app}' automatically.",
        "existing_wg_file": "Configuration exists at {path}; move it before running setup again.",
        "wg_configured": "WireGuard configuration linked from {path}.",
        "path_configured": "Application path registered: {path}.",
        "app_not_started": "{app} is not managed yet. Start it with 'vpngo {app}'.",
    },
    "pt-BR": {
        "usage": "VPNGo — aplicativos pela VPN WireGuard.\n"
                 "Uso: vpngo start <app> [perfil]\n"
                 "     vpngo --temp <perfil> <executável> [-d]\n"
                 "Execute 'vpngo help' para ver todos os comandos.",
        "help": "VPNGo — aplicativos pela VPN WireGuard.\n\n"
                "  vpngo profile add <nome> <arquivo.conf>      Salva um perfil VPN\n"
                "  vpngo profile import <pasta|zip|arquivo>...  Salva cada .conf com o nome do arquivo\n"
                "  vpngo profile list                          Lista os perfis\n"
                "  vpngo profile remove <nome>                  Esquece um perfil\n"
                "  vpngo assign <app> <perfil>                  Salva o perfil do app\n"
                "  vpngo start <app> [perfil]                   Abre o app pela VPN\n"
                "  vpngo --temp <perfil> <executável> [-d]     Executa uma vez, sem salvar\n"
                "  vpngo start <executável> <perfil> --temp [-d]  Mesmo uso temporário\n"
                "  vpngo switch <app> <perfil>                  Troca o perfil em uso\n"
                "  vpngo check <app>                            Compara o IP e o DNS do app com os seus (Linux)\n"
                "  vpngo stop <app>                             Fecha o app e sua sessão VPN\n"
                "  vpngo status <app>                           Mostra a rota do app\n"
                "  vpngo on|off <app>                           Seleciona VPN ou rota direta\n"
                "  vpngo policy <app> killswitch|dns on|off     Define a política de rota\n"
                "  vpngo helper add <app> <executável>          Inclui um processo auxiliar\n"
                "  vpngo config <caminho>                       Cadastra o caminho do app\n"
                "  vpngo app remove <app>                       Esquece um app parado\n"
                "  vpngo group add <grupo> <app>...             Põe apps num grupo\n"
                "  vpngo group on|off|stop <grupo>              Age sobre todos os apps do grupo\n"
                "  vpngo group switch <grupo> <perfil>          Passa o grupo para outro perfil\n"
                "  vpngo group list | remove <grupo> [app...]   Lista grupos, ou remove um ou seus apps\n"
                "  vpngo group rename <grupo> <novo-nome>       Renomeia um grupo\n"
                "  vpngo version                                Mostra a versão\n"
                "  vpngo update [--check]                       Instala a versão mais recente\n"
                "  vpngo proxy start|stop|status|list           Proxy SOCKS5 local para um perfil\n"
                "  vpngo --install-gui                          Instala a interface gráfica\n\n"
                "  -d, --detach                                 Libera o terminal; o app continua aberto\n"
                "  vpngo help <comando>                         Explica um comando e suas opções",
        "help_unknown": "Ajuda desconhecida: '{topic}'. Execute 'vpngo help' para listar os comandos.",
        "profile_configured": "Perfil VPN '{profile}' salvo, criptografado, a partir de {path}. O vpngo não precisa mais desse arquivo.",
        "profile_migrated": "Seus perfis VPN agora ficam criptografados. {path} não é mais necessário; apague se quiser.",
        "profiles_none": "Nenhum perfil VPN cadastrado.",
        "check_profile": "perfil {profile}",
        "check_app_ip": "IP público do app",
        "check_your_ip": "Seu IP público   ",
        "check_no_answer": "sem resposta",
        "check_dns": "Servidor DNS     ",
        "check_dns_tunnel": "(pelo túnel)",
        "check_dns_direct": "(FORA do túnel)",
        "check_dns_resolved": "Atenção: o isolamento de DNS está desligado e este sistema resolve nomes pelo "
                              "systemd-resolved, fora do túnel; as consultas do {app} podem escapar da VPN. "
                              "Ligue com: vpngo policy {app} dns on",
        "check_failed": "Resultado: a rede do app não respondeu. Confira a rota com 'vpngo status'.",
        "check_same_ip": "Resultado: o app sai para a internet com o seu próprio IP; ele NÃO está na VPN.",
        "check_not_on": "Resultado: o {app} não está totalmente na VPN. Rode 'vpngo on {app}'.",
        "check_ok": "Resultado: o tráfego do app sai pela VPN.",
        "profile_imported": "Perfil VPN '{profile}' salvo, criptografado, a partir de {path}.",
        "profile_import_failed": "{path} ignorado: {error}",
        "profile_import_none": "Nenhum arquivo .conf encontrado para importar.",
        "profile_import_done": "{count} perfil(is) importado(s). O vpngo não precisa mais desses arquivos.",
        "extra_apps": "Outros aplicativos compartilham este namespace; a rede não foi alterada.",
        "namespace_count": "Esperava um namespace ativo de '{app}'; encontrei {count}.",
        "invalid_namespace": "Nome de namespace inválido.",
        "one_wg": "Esperava exatamente uma interface WireGuard no namespace do aplicativo.",
        "no_direct_route": "Não encontrei a rota direta do aplicativo.",
        "route_is_vpn": "A rota normal aponta para a VPN; não há saída direta preparada.",
        "no_firewall": "Não consegui identificar o firewall do namespace.",
        "unexpected_dns": "Arquivo DNS do namespace inesperado; operação cancelada.",
        "already_off": "VPN já está desligada para {app}.",
        "already_on": "VPN já está ligada para {app}.",
        "incomplete_switch": "Há uma alternância incompleta; execute 'vpngo <aplicação> on' primeiro.",
        "rule_collision": "Já existe uma regra de rede na prioridade {priority}; nada foi alterado.",
        "off": "VPN desligada para {app}. As conexões antigas foram fechadas para reconexão automática.",
        "missing_backup": "Não encontrei o backup DNS desta sessão; a rede não foi alterada.",
        "on": "VPN ligada para {app}. As conexões antigas foram fechadas para reconexão automática.",
        "status_off": "VPN desligada",
        "status_on": "VPN ligada",
        "status_partial": "configuração parcial",
        "status_stopped": "encerrado e bloqueado",
        "status_no_session": "encerrado (sem namespace VPN)",
        "ipv4_route": "Rota IPv4",
        "config_created": "Configuração do Mihomo criada em {path}.",
        "config_private": "Mantenha este arquivo privado: ele contém sua chave WireGuard.",
        "controller_unavailable": "A API local do Mihomo está indisponível. Inicie o Mihomo primeiro.",
        "controller_bad": "Resposta inesperada da API local do Mihomo.",
        "controller_on": "VPN ligada para {app}. As conexões antigas foram fechadas para reconexão automática.",
        "controller_off": "VPN desligada para {app}. As conexões antigas foram fechadas para reconexão automática.",
        "controller_status": "{app}: {state}",
        "not_configured": "O Mihomo ainda não foi configurado. Inicie o aplicativo com 'vpngo start <app> <perfil>' primeiro.",
        "reconnect_failed": "A rota mudou, mas as conexões TCP antigas não puderam ser fechadas: {detail}",
        "missing_wg_file": "Configuração WireGuard não encontrada: {path}. Execute 'vpngo setup <wireguard.conf>'.",
        "missing_command": "Comando necessário não encontrado: {name}.",
        "starting": "Iniciando {app} pelo WireGuard...",
        "started": "{app} iniciado pela VPN. Você pode fechar este terminal.",
        "start_failed": "O aplicativo não iniciou pelo vopono. Veja {path}.",
        "authentication_failed": "Falha na autenticação de administrador.",
        "unsafe_process": "Não vou fechar automaticamente o processo de sistema compartilhado '{app}'.",
        "existing_wg_file": "Já existe uma configuração em {path}; mova-a antes de repetir setup.",
        "wg_configured": "Configuração WireGuard vinculada de {path}.",
        "path_configured": "Caminho do aplicativo registrado: {path}.",
        "app_not_started": "{app} ainda não é gerenciado. Inicie com 'vpngo {app}'.",
    },
}


def language():
    value = os.environ.get("VPNGO_LANG", "en-US").replace("_", "-")
    return "pt-BR" if value.lower().startswith("pt") else "en-US"


def tr(key, **values):
    return MESSAGES[language()][key].format(**values)
