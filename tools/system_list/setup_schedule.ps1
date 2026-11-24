# Registers the WAT-SystemList task: the System list reminders, once a day.
# Triggers: 09:15 daily, at log-on, and every 3 hours. The script itself skips when
# today's run already succeeded (--if-due), so the extra triggers only matter when the
# PC was off or offline at 09:15. The weekly summary goes out on the first run each Sunday.
#
#   powershell -ExecutionPolicy Bypass -File tools\system_list\setup_schedule.ps1
#   Remove: Unregister-ScheduledTask -TaskName WAT-SystemList -Confirm:$false

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

$action = New-ScheduledTaskAction -Execute $pythonw -Argument 'tools\system_list\remind.py --if-due' -WorkingDirectory $root
$daily = New-ScheduledTaskTrigger -Daily -At '09:15'
$logon = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
$repeat = New-ScheduledTaskTrigger -Once -At (Get-Date).Date.AddHours(9).AddMinutes(45) -RepetitionInterval (New-TimeSpan -Hours 3)
$settings = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 10) `
    -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited

Register-ScheduledTask -TaskName 'WAT-SystemList' -Action $action -Trigger @($daily, $logon, $repeat) -Settings $settings `
    -Principal $principal -Description 'Telegram reminders for the System list in Notion (wat-framework).' -Force | Out-Null

Write-Host "WAT-SystemList registered: daily at 09:15, with catch-up at log-on and every 3 hours ($pythonw)."
Write-Host "Log: $root\.tmp\system_list\runner.log"
