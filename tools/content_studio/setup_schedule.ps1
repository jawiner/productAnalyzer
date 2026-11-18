# Registers the content studio worker with Task Scheduler: every 10 minutes while you're
# signed in to Windows, waking the PC from sleep if needed. A pass with no approved idea
# ends in about a second. Re-running this script replaces the task.
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
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes 10)
$settings = New-ScheduledTaskSettingsSet -WakeToRun -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
    -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Hours 3)
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited

Register-ScheduledTask -TaskName $name -Action $action -Trigger $trigger -Settings $settings -Principal $principal `
    -Description "Makes the videos approved on Telegram (content engine). Logs: .tmp\content_studio\worker.log" -Force | Out-Null
Write-Output "Registered ${name}: every 10 minutes, wakes the PC from sleep."
