# Registers the WAT-ExpiryWatch task: the renewal check, once a day.
# Triggers: 09:00 daily, at log-on, and every 3 hours. The script itself skips when
# today's run already succeeded (--if-due), so the extra triggers only matter when the
# PC was off or offline at 09:00.
#
#   powershell -ExecutionPolicy Bypass -File tools\expiry_watch\setup_schedule.ps1
#   Remove: Unregister-ScheduledTask -TaskName WAT-ExpiryWatch -Confirm:$false

$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)

# Use the first Python that has the packages (the Store Python on PATH has them,
# the one in Programs\Python312 doesn't).
$candidates = @((& python -c "import sys; print(sys.executable)").Trim()) +
    @(Get-ChildItem "$env:LOCALAPPDATA\Programs\Python\Python3*\python.exe" -ErrorAction SilentlyContinue | ForEach-Object FullName)
$pythonw = $null
foreach ($python in $candidates) {
    $w = Join-Path (Split-Path $python) 'pythonw.exe'
    if (-not (Test-Path $w)) { continue }
    & $python -c "import requests, dotenv" 2>$null
    if ($LASTEXITCODE -eq 0) { $pythonw = $w; break }
}
if (-not $pythonw) { throw "No Python with requests + python-dotenv found. Run: python -m pip install requests python-dotenv" }

$action = New-ScheduledTaskAction -Execute $pythonw -Argument 'tools\expiry_watch\watch.py --if-due' -WorkingDirectory $root
$daily = New-ScheduledTaskTrigger -Daily -At '09:00'
$logon = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
$repeat = New-ScheduledTaskTrigger -Once -At (Get-Date).Date.AddHours(9).AddMinutes(30) -RepetitionInterval (New-TimeSpan -Hours 3)
$settings = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 20) `
    -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited

Register-ScheduledTask -TaskName 'WAT-ExpiryWatch' -Action $action -Trigger @($daily, $logon, $repeat) -Settings $settings `
    -Principal $principal -Description 'Warns on Telegram before subscriptions, domains and API keys run out (wat-framework).' -Force | Out-Null

Write-Host "WAT-ExpiryWatch registered: daily at 09:00, with catch-up at log-on and every 3 hours ($pythonw)."
Write-Host "Log: $root\.tmp\expiry_watch\runner.log"
