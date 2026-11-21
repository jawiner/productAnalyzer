# Registers the WAT-EmailWatch task: the email check, once a day.
# Triggers: 09:10 daily, at log-on, and every 3 hours. The script itself skips when today's
# check already succeeded (--if-due), so the extra triggers only matter when the PC was off
# or offline at 09:10.
#
#   powershell -ExecutionPolicy Bypass -File tools\email_watch\setup_schedule.ps1
#   Remove: Unregister-ScheduledTask -TaskName WAT-EmailWatch -Confirm:$false

$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)

# Use the first Python that has the packages (same search as Expiry Watch).
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

$action = New-ScheduledTaskAction -Execute $pythonw -Argument 'tools\email_watch\watch.py --if-due' -WorkingDirectory $root
$daily = New-ScheduledTaskTrigger -Daily -At '09:10'
$logon = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
$repeat = New-ScheduledTaskTrigger -Once -At (Get-Date).Date.AddHours(9).AddMinutes(40) -RepetitionInterval (New-TimeSpan -Hours 3)
$settings = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 15) `
    -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited

Register-ScheduledTask -TaskName 'WAT-EmailWatch' -Action $action -Trigger @($daily, $logon, $repeat) -Settings $settings `
    -Principal $principal -Description 'Checks Gmail once a day for the things on the Email Watch list and reports on Telegram (wat-framework).' -Force | Out-Null

Write-Host "WAT-EmailWatch registered: daily at 09:10, with catch-up at log-on and every 3 hours ($pythonw)."
Write-Host "Log: $root\.tmp\email_watch\runner.log"
