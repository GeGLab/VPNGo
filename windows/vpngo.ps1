param(
    [Parameter(Position=0)][string]$Application,
    [Parameter(Position=1)][string]$Action,
    [Parameter(Position=2)][string]$Profile,
    [Parameter(ValueFromRemainingArguments=$true)][string[]]$RemainingArgs
)

$ErrorActionPreference = 'Stop'
$Project = Split-Path -Parent $PSScriptRoot
$State = Join-Path $env:LOCALAPPDATA 'vpngo\mihomo'
$Python = if ($env:VPNGO_PYTHON) { $env:VPNGO_PYTHON } else { 'python' }
$Controller = Join-Path $Project 'shared/control.py'

function Invoke-Python([string]$Script, [string[]]$Arguments) {
    $Result = & $Python (Join-Path $Project $Script) @Arguments
    if ($LASTEXITCODE -ne 0) { throw "vpngo command failed: $Script" }
    return $Result
}

function Invoke-Control([string]$Name, [string]$Command) {
    Invoke-Python 'shared/control.py' @($Name, $Command)
}

function Test-MihomoReady([string]$Name) {
    # Windows PowerShell can turn redirected native stderr into a terminating
    # error with Stop. An unavailable controller is expected during startup.
    $ErrorActionPreference = 'Continue'
    & $Python (Join-Path $Project 'shared/windows_backend.py') probe $Name *> $null
    return $LASTEXITCODE -eq 0
}

function Assert-AppOnlyRouting {
    & (Join-Path $PSScriptRoot 'proxy-service.ps1') -Mode Check | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'Per-application routing is unavailable. Install the Windows backend with windows\install-backend.ps1. No VPN was started.' }
}

function Sync-AppRouting([string]$Mode = 'Apply') {
    $Helper = Join-Path $PSScriptRoot 'proxy-service.ps1'
    $Desired = Join-Path $State 'proxifyre.json'
    $Owner = [Security.Principal.WindowsIdentity]::GetCurrent().User.Value
    if ($Mode -eq 'Apply') {
        $Check = & $Helper -Mode Check -ConfigPath $Desired -OwnerSid $Owner | ConvertFrom-Json
        if ($LASTEXITCODE -ne 0) { throw 'Could not validate the per-application routing backend.' }
        if (-not $Check.needsApply) { return }
    }
    $ResultPath = Join-Path $State ('proxy-result-' + [Guid]::NewGuid().ToString('N') + '.json')
    $Command = "& '" + $Helper.Replace("'", "''") + "' -Mode '$Mode' -ConfigPath '" +
        $Desired.Replace("'", "''") + "' -OwnerSid '$Owner' -ResultPath '" + $ResultPath.Replace("'", "''") + "'; exit `$LASTEXITCODE"
    $Encoded = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($Command))
    try {
        $Operation = Start-Process -FilePath (Join-Path $PSHOME 'powershell.exe') `
            -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-EncodedCommand',$Encoded) `
            -Verb RunAs -WindowStyle Hidden -PassThru -Wait
        if (-not (Test-Path -LiteralPath $ResultPath)) { throw 'Process-filter update did not finish. No application was launched.' }
        $Result = Get-Content -LiteralPath $ResultPath -Raw | ConvertFrom-Json
        if ($Operation.ExitCode -ne 0 -or $Result.error) { throw "Process-filter update failed: $($Result.error)" }
    } finally {
        if (Test-Path -LiteralPath $ResultPath) { Remove-Item -LiteralPath $ResultPath -Force }
    }
}

function Close-App([string]$Name) {
    # Ask first, like SIGTERM on Linux and macOS: a forced kill can lose settings the app had
    # not written yet (issue #2). Apps that only hide to the tray are forced after 6 seconds.
    foreach ($Running in @(Get-Process -Name $Name -ErrorAction SilentlyContinue)) {
        if ($Running.MainWindowHandle -ne 0) { [void]$Running.CloseMainWindow() }
    }
    $Deadline = (Get-Date).AddSeconds(6)
    while ((Get-Process -Name $Name -ErrorAction SilentlyContinue) -and (Get-Date) -lt $Deadline) {
        Start-Sleep -Milliseconds 200
    }
    Get-Process -Name $Name -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
}

function Start-App($App) {
    # Squirrel apps (Discord, Slack...) start through Update.exe, which runs the current version.
    if ($App.start_with) {
        $Arguments = @($App.start_with | Select-Object -Skip 1)
        Start-Process -FilePath $App.start_with[0] -ArgumentList $Arguments
    } else {
        Start-Process -FilePath $App.launch
    }
}

function Start-MihomoEngine([string]$Name) {
    if (Test-MihomoReady $Name) { return }
    $Mihomo = if ($env:VPNGO_MIHOMO) { $env:VPNGO_MIHOMO } else {
        (Get-Command mihomo.exe -ErrorAction Stop).Source
    }
    $Config = Join-Path $State 'config.yaml'
    $Arguments = @('-d', ('"' + $State + '"'), '-f', ('"' + $Config + '"'))
    $Validation = Start-Process -FilePath $Mihomo -ArgumentList (@('-t') + $Arguments) `
        -WindowStyle Hidden -PassThru -Wait `
        -RedirectStandardOutput (Join-Path $State 'config-check.log') `
        -RedirectStandardError (Join-Path $State 'config-check-error.log')
    if ($Validation.ExitCode -ne 0) { throw "Mihomo rejected the config. Check $State\config-check-error.log." }
    # The Windows config has no TUN or global proxy. Mihomo needs no elevation.
    $Engine = Start-Process -FilePath $Mihomo -ArgumentList $Arguments -WindowStyle Hidden -PassThru `
        -RedirectStandardOutput (Join-Path $State 'mihomo.log') `
        -RedirectStandardError (Join-Path $State 'mihomo-error.log')
    try {
        for ($Attempt = 0; $Attempt -lt 30; $Attempt++) {
            Start-Sleep -Milliseconds 500
            $Engine.Refresh()
            if ($Engine.HasExited) { throw "Mihomo stopped. Check $State\mihomo-error.log." }
            if (Test-MihomoReady $Name) {
                @{ id = $Engine.Id; started = $Engine.StartTime.ToUniversalTime().Ticks } |
                    ConvertTo-Json | Set-Content -LiteralPath (Join-Path $State 'engine.json') -Encoding UTF8
                return
            }
        }
        throw "Mihomo did not become ready. Check $State\mihomo.log."
    } catch {
        if (-not $Engine.HasExited) { $Engine | Stop-Process -Force -ErrorAction SilentlyContinue }
        throw
    }
}

try {
    if ($Application -in @('start','on','temp','temp-wait')) {
        Assert-AppOnlyRouting
    }
    # PowerShell may bind a leading --flag to the remaining arguments instead of $Application.
    if ($Application -eq '--install-gui' -or (-not $Application -and $RemainingArgs -contains '--install-gui')) {
        & $Python (Join-Path $Project 'shared/commands.py') '--install-gui'
        exit $LASTEXITCODE
    }
    if (-not $Application) {
        & $Python (Join-Path $Project 'shared/commands.py')
        exit 2
    }
    if ($Application -eq 'shutdown') {
        if ($Action -or $Profile -or $RemainingArgs) { throw 'Usage: vpngo shutdown' }
        Assert-AppOnlyRouting
        Sync-AppRouting 'Stop'
        $EngineFile = Join-Path $State 'engine.json'
        if (Test-Path -LiteralPath $EngineFile) {
            $Record = Get-Content -LiteralPath $EngineFile -Raw | ConvertFrom-Json
            $Engine = Get-Process -Id $Record.id -ErrorAction SilentlyContinue
            if ($Engine -and $Engine.StartTime.ToUniversalTime().Ticks -eq $Record.started) {
                $Engine | Stop-Process -Force
            }
            Remove-Item -LiteralPath $EngineFile -Force
        }
        Write-Output 'VPNGo process filters and its local proxy stopped. Applications now use their usual connection.'
        exit 0
    }
    if ($Application -eq 'temp-wait') {
        if (-not $Action -or -not $Profile -or $RemainingArgs.Count -ne 1) { throw 'Invalid temporary worker arguments.' }
        $Session = [string]$RemainingArgs[0]
        try {
            Invoke-Python 'shared/managed.py' @('temp-bind', $Action, $Session, [string]$PID) | Out-Null
            $Child = Start-Process -FilePath $Profile -Wait -PassThru
            $ChildExitCode = $Child.ExitCode
        } finally {
            Invoke-Python 'shared/managed.py' @('temp-cleanup', $Action, $Session) | Out-Null
            Sync-AppRouting
        }
        exit $ChildExitCode
    }
    if ($Application -eq 'temp') {
        if (-not $Action -or -not $Profile -or $RemainingArgs.Count -gt 1 -or
            ($RemainingArgs.Count -eq 1 -and $RemainingArgs[0] -ne 'detach')) {
            throw 'Usage: vpngo --temp <profile> <executable> [-d|--detach]'
        }
        $Detached = $RemainingArgs.Count -eq 1
        $Resolved = Invoke-Python 'shared/managed.py' @('temp-resolve', $Profile) | ConvertFrom-Json
        $ProcessName = [System.IO.Path]::GetFileNameWithoutExtension($Resolved.process)
        if (Get-Process -Name $ProcessName -ErrorAction SilentlyContinue) {
            throw "$ProcessName is already running; close it before a temporary VPN run."
        }
        $AppJson = Invoke-Python 'shared/managed.py' @('temp-prepare', $Profile, $Action)
        $App = $AppJson | ConvertFrom-Json
        $TempPrepared = $true
        try {
            Start-MihomoEngine $App.process
            Sync-AppRouting
            if ($Detached) {
                $WorkerScript = $PSCommandPath.Replace("'", "''")
                $WorkerProcess = $App.process.Replace("'", "''")
                $WorkerLaunch = $App.launch.Replace("'", "''")
                $WorkerSession = $App.session.Replace("'", "''")
                $WorkerCommand = "& '$WorkerScript' temp-wait '$WorkerProcess' '$WorkerLaunch' '$WorkerSession'"
                $Encoded = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($WorkerCommand))
                $Worker = Start-Process -FilePath (Join-Path $PSHOME 'powershell.exe') `
                    -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-EncodedCommand',$Encoded) `
                    -WindowStyle Hidden -PassThru `
                    -RedirectStandardOutput (Join-Path $State 'temp.log') `
                    -RedirectStandardError (Join-Path $State 'temp-error.log')
                $TempPrepared = $false
                Write-Output "$Profile started through the VPN (PID $($Worker.Id)). You can close this terminal."
                exit 0
            }
            Invoke-Python 'shared/managed.py' @('temp-bind', $App.process, $App.session, [string]$PID) | Out-Null
            $Child = Start-Process -FilePath $App.launch -Wait -PassThru
            $ChildExitCode = $Child.ExitCode
        } finally {
            if ($TempPrepared) {
                Invoke-Python 'shared/managed.py' @('temp-cleanup', $App.process, $App.session) | Out-Null
                Sync-AppRouting
            }
        }
        exit $ChildExitCode
    }
    if ($Application -in @('profile','assign','start','stop','switch','status','on','off','policy','helper','version','help','--install-gui','group','app','update','proxy')) {
        $CliArgs = @($Application)
        if ($Action) { $CliArgs += $Action }
        if ($Profile) { $CliArgs += $Profile }
        if ($RemainingArgs) { $CliArgs += $RemainingArgs }
        & $Python (Join-Path $Project 'shared/commands.py') @CliArgs
        exit $LASTEXITCODE
    }
    if ($Application -eq 'profiles') {
        if ($Action -or $Profile) { throw 'Usage: vpngo profiles' }
        Invoke-Python 'shared/profiles.py' @('list')
        exit 0
    }
    if ($Application -eq 'config') {
        if (-not $Action -or $Profile) { throw 'Usage: vpngo config <bin-dir|executable>' }
        Invoke-Python 'shared/apps.py' @('config', $Action)
        exit 0
    }
    if ($Application -eq 'setup') {
        if (-not $Action) { throw 'Usage: vpngo setup <wireguard.conf> [profile]' }
        if ($Profile) {
            Invoke-Python 'shared/generate_mihomo.py' @($Action, $Profile)
        } else {
            Invoke-Python 'shared/generate_mihomo.py' @($Action)
        }
        exit 0
    }
    if (-not $Action) { $Action = 'start' }
    if ($Action -notin @('start','stop','on','off','status')) {
        throw 'Usage: vpngo <application> [start|stop|on|off|status]'
    }
    if ($Action -in @('start','on')) {
        Assert-AppOnlyRouting
    }
    if ($Profile -and $Action -ne 'start') { throw 'A profile can only be supplied with start.' }
    if ($Action -ne 'start') {
        if ($Action -eq 'stop') {
            $AppJson = Invoke-Python 'shared/managed.py' @('inspect', $Application)
            if (-not $AppJson -or $AppJson -eq 'null') {
                Write-Output "$Application`: already stopped."
                exit 0
            }
            $App = $AppJson | ConvertFrom-Json
            $ProcessName = [System.IO.Path]::GetFileNameWithoutExtension($App.process)
            $Protected = @('python','python3','powershell','pwsh','cmd','conhost','explorer','svchost','system')
            if ($ProcessName -in $Protected) {
                throw "Refusing to close shared system process '$ProcessName' automatically."
            }
            $BlockFailed = $false
            try { Invoke-Control $Application 'block' | Out-Null } catch { $BlockFailed = $true }
            Close-App $ProcessName
            foreach ($HelperPath in $App.helpers) {
                $HelperName = [System.IO.Path]::GetFileNameWithoutExtension($HelperPath)
                if ($HelperName -and $HelperName -notin $Protected) {
                    Close-App $HelperName
                }
            }
            if ($BlockFailed -or (Get-Process -Name $ProcessName -ErrorAction SilentlyContinue)) {
                throw "$Application stop incomplete; the route remains blocked if Mihomo accepted it."
            }
            if ($App.temporary) {
                Invoke-Python 'shared/managed.py' @('temp-cleanup', $App.process, $App.session) | Out-Null
                Sync-AppRouting
                Write-Output "$Application`: application closed; temporary Mihomo route removed."
            } else {
                Write-Output "$Application`: application closed; its Mihomo route is blocked. Other applications stay connected."
            }
            exit 0
        }
        if ($Action -eq 'on') {
            if (-not (Test-MihomoReady $Application)) { throw 'The local proxy is stopped. Run vpngo start <app> first.' }
            Sync-AppRouting
        }
        Invoke-Control $Application $Action
        exit 0
    }

    if (-not $Profile) { $Profile = 'default' }
    $AppJson = Invoke-Python 'shared/managed.py' @('prepare', $Application, $Profile)
    $App = $AppJson | ConvertFrom-Json
    $ProcessName = [System.IO.Path]::GetFileNameWithoutExtension($App.process)
    if ($ProcessName -in @('python','python3','powershell','pwsh','cmd','conhost','explorer','svchost','system')) {
        throw "Refusing to close shared system process '$ProcessName' automatically."
    }
    Start-MihomoEngine $Application
    Sync-AppRouting
    Invoke-Control $Application 'on'
    Close-App $ProcessName
    Invoke-Control $Application 'reconnect' | Out-Null
    Start-Sleep -Seconds 1
    Start-App $App
    Write-Output "$Application started through the VPN using per-process TCP/UDP filters. Windows routes and system proxy were not changed."
} catch {
    [Console]::Error.WriteLine("vpngo: $($_.Exception.Message)")
    exit 1
}
