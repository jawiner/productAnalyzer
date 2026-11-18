# Registers the build log with Task Scheduler: every hour at :50 while you're signed in to
# Windows (so the 20:00 report has the day's work), catching up when the PC comes back on.
# It doesn't wake the PC: a missed hour is sent on the next run. Re-running replaces the task.
#
#   powershell -ExecutionPolicy Bypass -File tools\build_log\setup_schedule.ps1
#   powershell -ExecutionPolicy Bypass -File tools\build_log\setup_schedule.ps1 -Remove

param([switch]$Remove)

$name = "WAT-BuildLog"
if ($Remove) {
    Unregister-ScheduledTask -TaskName $name -Confirm:$false -ErrorAction SilentlyContinue
    Write-Output "Removed $name."
    return
}

$script = Join-Path $PSScriptRoot "collect.py"
$pythonw = (Get-Command pythonw.exe -ErrorAction Stop).Source
$action = New-ScheduledTaskAction -Execute $pythonw -Argument "`"$script`"" -WorkingDirectory $PSScriptRoot
$first = (Get-Date).Date.AddHours((Get-Date).Hour).AddMinutes(50)
if ($first -lt (Get-Date)) { $first = $first.AddHours(1) }
$trigger = New-ScheduledTaskTrigger -Once -At $first -RepetitionInterval (New-TimeSpan -Hours 1)
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
    -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 20)
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited

Register-ScheduledTask -TaskName $name -Action $action -Trigger $trigger -Settings $settings -Principal $principal `
    -Description "Sends what got built (commits, new tools, skills) to the Mapflow work report. Log: .tmp\build_log\collect.log" -Force | Out-Null
Write-Output "Registered ${name}: every hour at :50, first run $($first.ToString('HH:mm'))."
