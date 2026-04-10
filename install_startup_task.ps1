#Requires -RunAsAdministrator

<#
.SYNOPSIS
    Install Project Manager as a Windows startup task
.DESCRIPTION
    Creates a scheduled task that starts the Project Manager on Windows login
.NOTES
    Run this script as Administrator
#>

$TaskName = "ProjectControlDashboard"
$ScriptPath = Join-Path $PSScriptRoot "run_manager.bat"
$WorkingDir = $PSScriptRoot

# Check if running as admin
if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Error "This script must be run as Administrator. Right-click and select 'Run as Administrator'."
    exit 1
}

# Verify script exists
if (-not (Test-Path $ScriptPath)) {
    Write-Error "Could not find run_manager.bat in the current directory."
    Write-Host "Current directory: $PSScriptRoot" -ForegroundColor Yellow
    exit 1
}

Write-Host "Installing Project Manager startup task..." -ForegroundColor Cyan
Write-Host "Task Name: $TaskName" -ForegroundColor Gray
Write-Host "Script Path: $ScriptPath" -ForegroundColor Gray

# Remove existing task if present
$existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existingTask) {
    Write-Host "Removing existing task..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

# Create the action
$Action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$ScriptPath`"" -WorkingDirectory $WorkingDir

# Create the trigger (on logon of any user)
$Trigger = New-ScheduledTaskTrigger -AtLogon

# Create the principal (run as current user with highest privileges)
$Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Highest

# Create the settings
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

# Register the task
try {
    Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Principal $Principal -Settings $Settings -Description "Project Control Dashboard - Auto-starts on login"
    
    Write-Host "`nSuccess! Startup task installed." -ForegroundColor Green
    Write-Host "`nThe Project Manager will now start automatically when you log in to Windows." -ForegroundColor White
    Write-Host "`nTo remove the startup task, run: Unregister-ScheduledTask -TaskName '$TaskName' -Confirm:`$false" -ForegroundColor Gray
} catch {
    Write-Error "Failed to install startup task: $_"
    exit 1
}

Write-Host "`nPress any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
