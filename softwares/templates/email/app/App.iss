DIRC      h>�4s� h>�              ��          F3ߞf
wuv��2`U���D 	.DS_Store hI�' hLz              ��           ������jR'�,o��m Inno Setup.txt    hI�X; h�2              ��          {��-N����~Ӫ� LICENSE.txt       h>�6� h>�              ��          0E��\��J_�Д]0�e0��o email/.gitignore  h>�7n��h>�              ��         ��+D�N;U����w��w�4� email/app.py      hMOC� hMP              ��          �} f�Q�~uB�ݚ0�dG�< email/app/App.iss hV����hMP              ��          �} f�Q�~uB�ݚ0�dG�< email/apps/App.iss        hV��w�hM~              ��        .Q@@�݁2��[n)A���� email/apps/templatesemail.exe     h>�p�h>�              ��          ��әu1-}�`���@�A�U email/run.py      h>�bZ h>�              ��         ����x@#߲�5��E)�8� email/versions/macos/run  hI�� hI�              ��         ��A��A�6 �|=�g[&|dj�� email/versions/windows/run.exe    h>�ׄ hI�              ��           �/V�^�C��7�������| requirements.txt  TREE   � -1 1
email -1 2
app 1 0
t�D�lC,II��jj_�qPsversions 2 2
r��Olâ��0����R3{}macos 1 0
��5��<?���%�3�����windows 1 0
p?���Z�M	�n[�	����"4P�f0�1F:�C>W�T                                                                                                                                                                                                                                                                                                                                                                    emplates\LICENSE.txt
; Uncomment the following line to run in non administrative install mode (install for current user only).
;PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputDir=F:\Documents\LTD\templates\email\app
OutputBaseFilename=templatesemail
SetupIconFile=F:\Documents\LTD\templates\email\images\logo.ico
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "F:\Documents\LTD\templates\email\versions\windows\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "F:\Documents\LTD\templates\email\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; NOTE: Don't use "Flags: ignoreversion" on any shared system files

[Registry]
Root: HKA; Subkey: "Software\Classes\{#MyAppAssocExt}\OpenWithProgids"; ValueType: string; ValueName: "{#MyAppAssocKey}"; ValueData: ""; Flags: uninsdeletevalue
Root: HKA; Subkey: "Software\Classes\{#MyAppAssocKey}"; ValueType: string; ValueName: ""; ValueData: "{#MyAppAssocName}"; Flags: uninsdeletekey
Root: HKA; Subkey: "Software\Classes\{#MyAppAssocKey}\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\{#MyAppExeName},0"
Root: HKA; Subkey: "Software\Classes\{#MyAppAssocKey}\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" ""%1"""

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

