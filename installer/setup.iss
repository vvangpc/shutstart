; Inno Setup script for ShutStart.
; Compiled in CI by: ISCC.exe installer\setup.iss
; Output: dist\ShutStart-Setup.exe

#define MyAppName "ShutStart"
#define MyAppVersion "1.2.0"
#define MyAppPublisher "ShutStart"
#define MyAppExeName "ShutStart.exe"

[Setup]
AppId={{B7E2A0F1-9F2B-4F5A-9B6C-5C9D3E1B7A21}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
VersionInfoVersion={#MyAppVersion}
DefaultDirName={localappdata}\Programs\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputBaseFilename=ShutStart-Setup
OutputDir=..\dist
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
UninstallDisplayName={#MyAppName}
UninstallDisplayIcon={app}\{#MyAppExeName}
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
CloseApplications=force
RestartApplications=no
#define IconFile "..\shutstart\resources\icon.ico"
#if FileExists(AddBackslash(SourcePath) + IconFile)
SetupIconFile={#IconFile}
#endif

[Languages]
Name: "chinesesimp"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; GroupDescription: "附加快捷方式:"; Flags: unchecked

[Files]
Source: "..\dist\ShutStart\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{#MyAppName} 设置"; Filename: "{app}\{#MyAppExeName}"; Parameters: "--settings"
Name: "{group}\卸载 {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Registry]
; Clean up the HKCU\Run value on uninstall so we don't leave a dangling autostart entry.
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; \
  ValueType: none; ValueName: "ShutStart"; Flags: deletevalue uninsdeletevalue

[Run]
Filename: "{app}\{#MyAppExeName}"; Parameters: "--settings"; \
  Description: "立即配置 {#MyAppName}"; Flags: nowait postinstall skipifsilent

[UninstallRun]
; Best-effort: close any running ShutStart instance before removing files.
Filename: "{cmd}"; Parameters: "/C taskkill /F /IM {#MyAppExeName}"; Flags: runhidden; RunOnceId: "KillShutStart"
; Best-effort: remove the scheduled logon task. Deleting a /rl highest task needs
; admin; if the uninstaller runs as a normal user this will silently fail and the
; user must remove it via Task Scheduler. The README documents that.
Filename: "{cmd}"; Parameters: "/C schtasks /delete /tn ""\ShutStart\ShutStart Logon"" /f"; Flags: runhidden; RunOnceId: "DelShutStartTask"
