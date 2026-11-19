# Registers the content studio worker with Task Scheduler: every 2 minutes while you're
# signed in to Windows, waking the PC from sleep if needed. A pass with no approved idea
# ends in about a second. Passes may overlap (MultipleInstances Parallel): the worker makes
# up to two videos side by side and a pass that finds both slots busy exits at once
# (USER 2026-11-19). Re-running this script replaces the task; a pass already running goes on.
#
#   powershell -ExecutionPolicy Bypass -File tools\content_studio\setup_schedule.ps1
#   powershell -ExecutionPolicy Bypass -File tools\content_studio\setup_schedule.ps1 -Remove

param([switch]$Remove)

$name = "WAT-ContentStudio"
if ($Remove) {
    Unregister-ScheduledTask -TaskName $name -Confirm:$false -ErrorAction SilentlyContinue
    Write-Output "Removed $name."
    return
}

$worker = Join-Path $PSScriptRoot "worker.py"
$pythonw = (Get-Command pythonw.exe -ErrorAction Stop).Source
$action = New-ScheduledTaskAction -Execute $pythonw -Argument "`"$worker`" --once" -WorkingDirectory $PSScriptRoot
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes 2)
$settings = New-ScheduledTaskSettingsSet -WakeToRun -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
    -MultipleInstances Parallel -ExecutionTimeLimit (New-TimeSpan -Hours 3)
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited

Register-ScheduledTask -TaskName $name -Action $action -Trigger $trigger -Settings $settings -Principal $principal `
    -Description "Makes the videos approved on Telegram (content engine). Logs: .tmp\content_studio\worker.log" -Force | Out-Null
Write-Output "Registered ${name}: every 2 minutes, up to two videos at once, wakes the PC from sleep."
