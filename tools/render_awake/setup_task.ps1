# Registers render_awake.py with Task Scheduler: starts at sign-in and keeps running in the background
# (no time limit, restarted if it crashes), and starts it now. It turns PowerToys Awake on while a render
# runs (USER 2026-11-25). Re-running this script replaces the task and restarts the watcher.
#
#   powershell -ExecutionPolicy Bypass -File tools\render_awake\setup_task.ps1
#   powershell -ExecutionPolicy Bypass -File tools\render_awake\setup_task.ps1 -Remove

param([switch]$Remove)

$name = "WAT-RenderAwake"
if ($Remove) {
    Stop-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue
    Unregister-ScheduledTask -TaskName $name -Confirm:$false -ErrorAction SilentlyContinue
    Write-Output "Removed $name."
    return
}

$script = Join-Path $PSScriptRoot "render_awake.py"
$pythonw = (Get-Command pythonw.exe -ErrorAction Stop).Source
$action = New-ScheduledTaskAction -Execute $pythonw -Argument "`"$script`"" -WorkingDirectory $PSScriptRoot
$trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
    -MultipleInstances IgnoreNew -ExecutionTimeLimit ([TimeSpan]::Zero) `
    -RestartCount 5 -RestartInterval (New-TimeSpan -Minutes 1)
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited

Stop-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue
Register-ScheduledTask -TaskName $name -Action $action -Trigger $trigger -Settings $settings -Principal $principal `
    -Description "Turns PowerToys Awake on while a render runs. Log: .tmp\render_awake\render_awake.log" -Force | Out-Null
Start-ScheduledTask -TaskName $name
Write-Output "Registered ${name}: starts at sign-in, running now."
