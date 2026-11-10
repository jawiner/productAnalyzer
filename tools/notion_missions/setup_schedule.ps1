# Registers the WAT-NotionMissions task: runs run_missions.py every hour (or -EveryMinutes)
# as you, only while you're logged on, with no console window, never two at once.
#
#   powershell -ExecutionPolicy Bypass -File tools\notion_missions\setup_schedule.ps1 [-EveryMinutes 60]
#   Remove: Unregister-ScheduledTask -TaskName WAT-NotionMissions -Confirm:$false

param([int]$EveryMinutes = 60)

$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)

# Use the first Python that has the runner's packages (the Store Python on PATH has them,
# the one in Programs\Python312 used by the daily summary task doesn't).
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

$action = New-ScheduledTaskAction -Execute $pythonw -Argument 'tools\notion_missions\run_missions.py' -WorkingDirectory $root
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(2) -RepetitionInterval (New-TimeSpan -Minutes $EveryMinutes)
$settings = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Hours 4) `
    -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited

Register-ScheduledTask -TaskName 'WAT-NotionMissions' -Action $action -Trigger $trigger -Settings $settings `
    -Principal $principal -Description 'Runs Ready missions from the Claude Missions board in Notion (wat-framework).' -Force | Out-Null

Write-Host "WAT-NotionMissions registered: every $EveryMinutes min, first run in about 2 minutes ($pythonw)."
Write-Host "Log: $root\.tmp\notion_missions\runner.log"
