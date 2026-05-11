; Project Manager - Inno Setup Script
; Creates professional Windows installer
; Requires: Inno Setup 6.2+ (https://jrsoftware.org/isinfo.php)

#define MyAppName "Project Manager"
#define MyAppVersion "2.1.0"
#define MyAppPublisher "Rehar.Lab"
#define MyAppURL "https://github.com/reharlab/project-manager"
#define MyAppExeName "ProjectManager.exe"
#define MyAppAssocName MyAppName + " File"
#define MyAppAssocExt ".pjm"
#define MyAppAssocKey StringChange(MyAppAssocName, " ", "") + MyAppAssocExt

[Setup]
; Application information
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}

; Default installation directory
DefaultDirName={autopf}\{#MyAppName}
DisableProgramGroupPage=no

; Output configuration
OutputDir=dist\installer
OutputBaseFilename=ProjectManager-{#MyAppVersion}-Setup
Compression=lzma2/ultra64
SolidCompression=yes

; Visual styles and appearance
WizardStyle=modern
SetupIconFile=assets\icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}

; Version info
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription={#MyAppName} - Production-ready project manager
VersionInfoProductName={#MyAppName}
VersionInfoProductVersion={#MyAppVersion}
VersionInfoVersion={#MyAppVersion}

; Privileges
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

; Architecture (build separate installers or combined)
ArchitecturesInstallIn64BitMode=x64 arm64
ArchitecturesAllowed=x86 x64 arm64

; Signing (enable when certificate is available)
; SignTool=signtool
; SignedUninstaller=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "french"; MessagesFile: "compiler:Languages\French.isl"
Name: "german"; MessagesFile: "compiler:Languages\German.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode
Name: "autostart"; Description: "Start Project Manager on Windows login"; GroupDescription: "Startup Options:"
Name: "associate"; Description: "Associate .pjm files with Project Manager"; GroupDescription: "File Associations:"

[Files]
; Main executable and data files
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; Data directory (create empty)
Source: "projects.json"; DestDir: "{userappdata}\{#MyAppName}"; Flags: onlyifdoesntexist
Source: "settings.json"; DestDir: "{userappdata}\{#MyAppName}"; Flags: onlyifdoesntexist

; License and documentation
Source: "LICENSE"; DestDir: "{app}"; Flags: ignoreversion
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion

; NOTE: Don't use "Flags: ignoreversion" on any shared system files

[Icons]
; Start Menu shortcuts
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:ProgramOnTheWeb,{#MyAppName}}"; Filename: "{#MyAppURL}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"

; Desktop shortcut (optional)
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

; Quick Launch shortcut (optional)
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon

[Registry]
; Application registration (for Add/Remove Programs details)
Root: HKA; Subkey: "Software\Microsoft\Windows\CurrentVersion\Uninstall\{#MyAppAssocKey}_is1"; ValueType: string; ValueName: "DisplayIcon"; ValueData: "{app}\{#MyAppExeName}"

; File association for .pjm files
Root: HKA; Subkey: "Software\Classes\{#MyAppAssocExt}"; ValueType: string; ValueName: ""; ValueData: "{#MyAppAssocKey}"; Flags: uninsdeletevalue; Tasks: associate
Root: HKA; Subkey: "Software\Classes\{#MyAppAssocKey}"; ValueType: string; ValueName: ""; ValueData: "{#MyAppAssocName}"; Flags: uninsdeletekey; Tasks: associate
Root: HKA; Subkey: "Software\Classes\{#MyAppAssocKey}\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\{#MyAppExeName},0"; Tasks: associate
Root: HKA; Subkey: "Software\Classes\{#MyAppAssocKey}\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" ""%1"""; Tasks: associate

[Run]
; Launch application after installation
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
const
  WM_CLOSE = $0010;

var
  ErrorCode: Integer;

// Check if application is running
function IsAppRunning(): Boolean;
var
  ResultCode: Integer;
begin
  Result := not Exec('taskkill', '/F /IM {#MyAppExeName} /FI "STATUS eq RUNNING" /FO CSV /NH', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
end;

// Custom page to check prerequisites
function InitializeSetup(): Boolean;
begin
  Result := true;
  
  // Check if already running
  if IsAppRunning() then
  begin
    if MsgBox('{#MyAppName} is currently running. Setup will close it to continue. Do you want to proceed?', mbConfirmation, MB_YESNO) = IDYES then
    begin
      Exec('taskkill', '/F /IM {#MyAppExeName}', '', SW_HIDE, ewWaitUntilTerminated, ErrorCode);
      Sleep(2000);
    end else
    begin
      Result := false;
    end;
  end;
end;

// Create scheduled task for auto-start
procedure CurStepChanged(CurStep: TSetupStep);
begin
  if (CurStep = ssPostInstall) and WizardIsTaskSelected('autostart') then
  begin
    // Create scheduled task for auto-start
    Exec('schtasks', '/Create /F /TN "{#MyAppName}" /TR "\"{app}\{#MyAppExeName}\"" /SC ONLOGON /RL LIMITED /NP', '', SW_HIDE, ewWaitUntilTerminated, ErrorCode);
  end;
end;

// Remove scheduled task on uninstall
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usPostUninstall then
  begin
    Exec('schtasks', '/Delete /F /TN "{#MyAppName}"', '', SW_HIDE, ewWaitUntilTerminated, ErrorCode);
  end;
end;

// Handle program files directory selection
function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := true;
  if CurPageID = wpSelectDir then
  begin
    // Warn if installing to Program Files without admin rights
    if (not IsAdminInstallMode) and (Pos(ExpandConstant('{pf}'), WizardDirValue) = 1) then
    begin
      MsgBox('Warning: You are installing to Program Files without administrator rights. Some features may not work correctly.', mbWarning, MB_OK);
    end;
  end;
end;
