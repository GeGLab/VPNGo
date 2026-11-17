"""Short, read-only help for each public command."""

from i18n import language


TOPICS = {
    "en-US": {
        "help": "Usage: vpngo help [command]\n"
                "Show all commands, or explain one command and its options.\n"
                "Examples: vpngo help start | vpngo help profile add",
        "profile": "Usage: vpngo profile add <name> <wireguard.conf>\n"
                   "       vpngo profile import <folder|file.zip|file.conf>...\n"
                   "       vpngo profile list\n"
                   "Add or list named WireGuard profiles. vpngo keeps an encrypted copy of each .conf.",
        "profile add": "Usage: vpngo profile add <name> <wireguard.conf>\n"
                       "  <name>            Name used by start, assign and switch.\n"
                       "  <wireguard.conf>  Existing WireGuard config; copied, encrypted, into vpngo's profiles folder.",
        "check": "Usage: vpngo check <app>\n"
                 "Linux. Compare the running app's public IP and country with this computer's, and show\n"
                 "whether each DNS server of its namespace is reached through the tunnel.\n"
                 "Exits with 1 when the app is not on the VPN or its network does not answer.",
        "profile import": "Usage: vpngo profile import <folder|file.zip|file.conf>...\n"
                          "Save every .conf found as a profile named after its file (wg-NL-FREE-12.conf becomes\n"
                          "wg-nl-free-12). A folder is read without subfolders; a .zip is read without extracting it.\n"
                          "An existing profile with the same name is updated. A refused file does not stop the others.",
        "profile list": "Usage: vpngo profile list\n"
                        "List registered VPN profile names.",
        "profile remove": "Usage: vpngo profile remove <name>\n"
                          "Forget a profile and delete vpngo's encrypted copy. Refused while an app uses it.",
        "app": "Usage: vpngo app remove <app>\n"
               "Forget a stopped app: its registered path, saved profile, policies and group.\n"
               "The program itself is not changed.",
        "app remove": "Usage: vpngo app remove <app>\n"
                      "Forget a stopped app: its registered path, saved profile, policies and group.\n"
                      "The program itself is not changed.",
        "group": "Usage: vpngo group add <group> <app>...\n"
                 "       vpngo group on|off|stop <group>\n"
                 "       vpngo group switch <group> <profile>\n"
                 "       vpngo group list\n"
                 "       vpngo group remove <group> [app...]\n"
                 "       vpngo group rename <group> <new-name>\n"
                 "Act on a set of apps at once. An app belongs to one group; adding it elsewhere moves it.\n"
                 "  on      Start stopped apps and return direct ones to the VPN.\n"
                 "  off     Move the apps on the VPN to the direct route.\n"
                 "  stop    Close every app in the group.\n"
                 "  switch  Running apps on the VPN switch now; the others use the profile on their next start.\n"
                 "  remove  Without apps, delete the group; the apps themselves stay.",
        "assign": "Usage: vpngo assign <app> <profile>\n"
                  "Save the profile for future starts; does not launch the app.\n"
                  "  <app>      App name or registered executable.\n"
                  "  <profile>  Registered VPN profile.",
        "start": "Usage: vpngo start <app> [profile]\n"
                 "       vpngo start <executable> <profile> --temp [-d|--detach]\n"
                 "Normal start closes running copies and launches the app on the VPN.\n"
                 "  [profile]  Use this profile and save it; omitted uses the saved profile.\n"
                 "  --temp     Run once without saving or closing other copies.\n"
                 "  -d        Return to the prompt during a temporary run.",
        "--temp": "Usage: vpngo --temp <profile> <executable> [-d|--detach]\n"
                  "Run once without saving an app assignment.\n"
                  "  <profile>     Registered VPN profile.\n"
                  "  <executable>  Absolute/relative path, or name in the current directory or PATH.\n"
                  "  -d, --detach  Return to the prompt; the app keeps running.",
        "detach": "Usage: vpngo --temp <profile> <executable> [-d|--detach]\n"
                  "Detach a temporary run from the original terminal. The VPN session ends when the app exits.",
        "switch": "Usage: vpngo switch <app> <profile>\n"
                  "Change a running app's VPN profile without restarting it.\n"
                  "  <profile>  Registered profile; saved after a successful switch.\n"
                  "The app must reconnect its own connections. Run 'on' first if it is off.",
        "stop": "Usage: vpngo stop <app>\n"
                "Close the app and end its VPN session. The saved profile remains.",
        "shutdown": "Usage: vpngo shutdown\n"
                    "Windows: stop VPNGo's process filters and local proxy for every managed app.\n"
                    "Applications remain open and return to their usual connection.",
        "status": "Usage: vpngo status <app>\n"
                  "       vpngo status --json\n"
                  "Show the current route and the settings saved for the next start.\n"
                  "  --json  Every profile, group and app with its route, start time, time on each route,\n"
                  "          VPN server, traffic counters and who opened it (vpngo or outside), as JSON;\n"
                  "          never asks for a password.",
        "--install-gui": "Usage: vpngo --install-gui\n"
                         "Download, verify and install or upgrade the graphical interface (vpngo-gui).\n"
                         "It goes in its own Python environment with Qt; the first install downloads about 250 MB.",
        "on": "Usage: vpngo on <app>\n"
              "Return a managed app to its VPN route. The app stays open.",
        "off": "Usage: vpngo off <app>\n"
               "Move a managed app to the direct route. The app stays open.",
        "policy": "Usage: vpngo policy <app> killswitch|dns on|off\n"
                  "Save Linux routing safeguards for the next start.\n"
                  "  killswitch  Block traffic if the VPN route fails.\n"
                  "  dns         Isolate DNS; requires the kill switch and a DNS IP.\n"
                  "  on|off      Enable or disable the chosen safeguard.\n"
                  "Strict per-app policies are unavailable on macOS and Windows.",
        "policy killswitch": "Usage: vpngo policy <app> killswitch on|off\n"
                             "Block traffic if the VPN route fails. On by default on Linux.\n"
                             "Takes effect on the next start; turn DNS isolation off before disabling it.",
        "policy dns": "Usage: vpngo policy <app> dns on|off\n"
                      "Isolate DNS inside the Linux VPN namespace. Off by default.\n"
                      "Requires the kill switch and an IP in the profile's DNS field.\n"
                      "Takes effect on the next start.",
        "helper": "Usage: vpngo helper add <app> <executable>\n"
                  "Add a helper process to the app's Mihomo route on macOS/Windows.\n"
                  "The executable must exist; the change takes effect on the next start.",
        "helper add": "Usage: vpngo helper add <app> <executable>\n"
                      "Route the helper executable with the app on macOS/Windows.\n"
                      "The executable must exist; the change takes effect on the next start.",
        "config": "Usage: vpngo config <path>\n"
                  "Register an executable, a folder of executables, or a macOS .app bundle.\n"
                  "Use this when the app cannot be found automatically.",
        "proxy": "Usage: vpngo proxy start <profile> [--json]\n"
                 "       vpngo proxy stop <profile>\n"
                 "       vpngo proxy status [--json]\n"
                 "       vpngo proxy list --json\n"
                 "Open a SOCKS5 listener on 127.0.0.1 for one profile; Mihomo runs the tunnel in user space.\n"
                 "No TUN, route or DNS change. Every connection goes through the profile, never direct.\n"
                 "  start   Open the listener (or reuse the open one) and print its port.\n"
                 "  stop    Close the profile's listener.\n"
                 "  status  List the open listeners and their ports.\n"
                 "  list    Profiles, version and why 'proxy start' can't run, as JSON.\n"
                 "Needs Mihomo on PATH or VPNGO_MIHOMO. Used by the Annoy app to route chosen servers.",
        "update": "Usage: vpngo update [--check]\n"
                  "Download the latest release from GitHub, check it against SHA256SUMS and install it in place.\n"
                  "Profiles and settings are kept; a failed update restores the previous version.\n"
                  "  --check  Only say whether a newer version exists.\n"
                  "Package manager installs update with their own command; a source checkout with git pull.",
        "version": "Usage: vpngo version\n"
                   "Show the installed version (or 'dev' from a source checkout).",
        "setup": "Usage: vpngo setup <wireguard.conf> [profile]\n"
                 "Legacy form of 'profile add'; omitted profile means 'default'.",
        "profiles": "Usage: vpngo profiles\n"
                    "Legacy form of 'profile list'.",
    },
    "pt-BR": {
        "help": "Uso: vpngo help [comando]\n"
                "Lista os comandos ou explica as opções de um comando.\n"
                "Exemplos: vpngo help start | vpngo help profile add",
        "profile": "Uso: vpngo profile add <nome> <wireguard.conf>\n"
                   "     vpngo profile import <pasta|arquivo.zip|arquivo.conf>...\n"
                   "     vpngo profile list\n"
                   "Cadastra ou lista perfis WireGuard. O vpngo guarda uma cópia criptografada de cada .conf.",
        "profile add": "Uso: vpngo profile add <nome> <wireguard.conf>\n"
                       "  <nome>            Nome usado por start, assign e switch.\n"
                       "  <wireguard.conf>  Configuração existente; copiada, criptografada, para a pasta de perfis do vpngo.",
        "check": "Uso: vpngo check <app>\n"
                 "Linux. Compara o IP público e o país do app aberto com os deste computador e mostra\n"
                 "se cada servidor DNS do namespace dele é alcançado pelo túnel.\n"
                 "Sai com 1 quando o app não está na VPN ou a rede dele não responde.",
        "profile import": "Uso: vpngo profile import <pasta|arquivo.zip|arquivo.conf>...\n"
                          "Salva cada .conf encontrado como um perfil com o nome do arquivo (wg-NL-FREE-12.conf vira\n"
                          "wg-nl-free-12). A pasta é lida sem as subpastas; o .zip é lido sem ser extraído.\n"
                          "Um perfil existente com o mesmo nome é atualizado. Um arquivo recusado não impede os outros.",
        "profile list": "Uso: vpngo profile list\n"
                        "Lista os nomes dos perfis VPN cadastrados.",
        "profile remove": "Uso: vpngo profile remove <nome>\n"
                          "Esquece um perfil e apaga a cópia criptografada do vpngo. Recusado enquanto algum app o usa.",
        "app": "Uso: vpngo app remove <app>\n"
               "Esquece um app parado: caminho cadastrado, perfil salvo, políticas e grupo.\n"
               "O programa em si não muda.",
        "app remove": "Uso: vpngo app remove <app>\n"
                      "Esquece um app parado: caminho cadastrado, perfil salvo, políticas e grupo.\n"
                      "O programa em si não muda.",
        "group": "Uso: vpngo group add <grupo> <app>...\n"
                 "     vpngo group on|off|stop <grupo>\n"
                 "     vpngo group switch <grupo> <perfil>\n"
                 "     vpngo group list\n"
                 "     vpngo group remove <grupo> [app...]\n"
                 "     vpngo group rename <grupo> <novo-nome>\n"
                 "Age sobre vários apps de uma vez. Um app fica em um grupo só; adicioná-lo a outro o move.\n"
                 "  on      Abre os apps parados e volta os diretos para a VPN.\n"
                 "  off     Passa os apps que estão na VPN para a rota direta.\n"
                 "  stop    Fecha todos os apps do grupo.\n"
                 "  switch  Os apps na VPN trocam agora; os outros usam o perfil no próximo start.\n"
                 "  remove  Sem apps, apaga o grupo; os apps continuam cadastrados.",
        "assign": "Uso: vpngo assign <app> <perfil>\n"
                  "Salva o perfil para os próximos starts; não abre o app.\n"
                  "  <app>     Nome do app ou executável cadastrado.\n"
                  "  <perfil>  Perfil VPN cadastrado.",
        "start": "Uso: vpngo start <app> [perfil]\n"
                 "     vpngo start <executável> <perfil> --temp [-d|--detach]\n"
                 "O start normal fecha outras instâncias e abre o app pela VPN.\n"
                 "  [perfil]  Usa e salva esse perfil; sem ele, usa o perfil salvo.\n"
                 "  --temp    Executa uma vez, sem salvar nem fechar outras instâncias.\n"
                 "  -d        Libera o terminal na execução temporária.",
        "--temp": "Uso: vpngo --temp <perfil> <executável> [-d|--detach]\n"
                  "Executa uma vez sem salvar atribuição do app.\n"
                  "  <perfil>      Perfil VPN cadastrado.\n"
                  "  <executável>  Caminho absoluto/relativo, ou nome na pasta atual ou PATH.\n"
                  "  -d, --detach  Libera o terminal; o app continua aberto.",
        "detach": "Uso: vpngo --temp <perfil> <executável> [-d|--detach]\n"
                  "Libera o terminal de origem. A sessão VPN termina quando o app fecha.",
        "switch": "Uso: vpngo switch <app> <perfil>\n"
                  "Troca o perfil VPN de um app aberto sem reiniciá-lo.\n"
                  "  <perfil>  Perfil cadastrado; salvo após a troca funcionar.\n"
                  "O app precisa reconectar. Se estiver em off, execute 'on' primeiro.",
        "stop": "Uso: vpngo stop <app>\n"
                "Fecha o app e a sessão VPN. O perfil salvo permanece.",
        "status": "Uso: vpngo status <app>\n"
                  "     vpngo status --json\n"
                  "Mostra a rota atual e as opções salvas para o próximo start.\n"
                  "  --json  Todos os perfis, grupos e apps com rota, início, tempo em cada rota,\n"
                  "          servidor da VPN, contadores de tráfego e quem abriu (o vpngo ou por fora),\n"
                  "          em JSON; nunca pede senha.",
        "--install-gui": "Uso: vpngo --install-gui\n"
                         "Baixa, confere e instala ou atualiza a interface gráfica (vpngo-gui).\n"
                         "Ela fica num ambiente Python próprio com Qt; a primeira instalação baixa cerca de 250 MB.",
        "on": "Uso: vpngo on <app>\n"
              "Recoloca um app gerenciado na rota VPN sem fechá-lo.",
        "off": "Uso: vpngo off <app>\n"
               "Passa um app gerenciado para a rota direta sem fechá-lo.",
        "policy": "Uso: vpngo policy <app> killswitch|dns on|off\n"
                  "Salva proteções de rota do Linux para o próximo start.\n"
                  "  killswitch  Bloqueia o tráfego se a VPN falhar.\n"
                  "  dns         Isola o DNS; exige kill switch e um IP de DNS.\n"
                  "  on|off      Liga ou desliga a proteção escolhida.\n"
                  "Políticas estritas por app não estão disponíveis no macOS/Windows.",
        "policy killswitch": "Uso: vpngo policy <app> killswitch on|off\n"
                             "Bloqueia o tráfego se a VPN falhar. Ligado por padrão no Linux.\n"
                             "Vale no próximo start; desligue o DNS isolado antes de desligá-lo.",
        "policy dns": "Uso: vpngo policy <app> dns on|off\n"
                      "Isola o DNS no namespace VPN do Linux. Desligado por padrão.\n"
                      "Exige kill switch e um IP no campo DNS do perfil.\n"
                      "Vale no próximo start.",
        "helper": "Uso: vpngo helper add <app> <executável>\n"
                  "Inclui um processo auxiliar na rota Mihomo do app no macOS/Windows.\n"
                  "O executável precisa existir; vale no próximo start.",
        "helper add": "Uso: vpngo helper add <app> <executável>\n"
                      "Roteia o executável auxiliar com o app no macOS/Windows.\n"
                      "O executável precisa existir; vale no próximo start.",
        "config": "Uso: vpngo config <caminho>\n"
                  "Cadastra um executável, uma pasta de executáveis ou um pacote .app do macOS.\n"
                  "Use quando o app não for encontrado automaticamente.",
        "proxy": "Uso: vpngo proxy start <perfil> [--json]\n"
                 "     vpngo proxy stop <perfil>\n"
                 "     vpngo proxy status [--json]\n"
                 "     vpngo proxy list --json\n"
                 "Abre um SOCKS5 em 127.0.0.1 para um perfil; o Mihomo roda o túnel em espaço de usuário.\n"
                 "Sem TUN, sem mudar rotas ou DNS. Toda conexão passa pelo perfil, nunca direto.\n"
                 "  start   Abre o listener (ou reaproveita o aberto) e mostra a porta.\n"
                 "  stop    Fecha o listener do perfil.\n"
                 "  status  Lista os listeners abertos e suas portas.\n"
                 "  list    Perfis, versão e por que 'proxy start' não roda, em JSON.\n"
                 "Precisa do Mihomo no PATH ou em VPNGO_MIHOMO. Usado pelo app Annoy para rotear servidores escolhidos.",
        "update": "Uso: vpngo update [--check]\n"
                  "Baixa a versão mais recente do GitHub, confere com o SHA256SUMS e instala por cima.\n"
                  "Perfis e configurações ficam; se a atualização falhar, a versão anterior volta.\n"
                  "  --check  Só diz se há uma versão mais nova.\n"
                  "Instalações por gerenciador de pacotes atualizam pelo próprio gerenciador; o código-fonte, com git pull.",
        "version": "Uso: vpngo version\n"
                   "Mostra a versão instalada (ou 'dev' no código-fonte).",
        "setup": "Uso: vpngo setup <wireguard.conf> [perfil]\n"
                 "Forma antiga de 'profile add'; sem perfil, usa 'default'.",
        "profiles": "Uso: vpngo profiles\n"
                    "Forma antiga de 'profile list'.",
        "shutdown": "Uso: vpngo shutdown\n"
                    "Windows: encerra os filtros por processo e o proxy local de todos os apps.\n"
                    "Os aplicativos continuam abertos e voltam para a conexao normal.",
    },
}


ALIASES = {"temp": "--temp", "-d": "detach", "--detach": "detach", "proxy start": "proxy", "proxy stop": "proxy",
           "proxy status": "proxy", "proxy list": "proxy"}


def get(topic):
    """Return localized help text, or None for an unknown topic."""
    return TOPICS[language()].get(ALIASES.get(topic, topic))
