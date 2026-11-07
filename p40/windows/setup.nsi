Unicode true
!include "MUI2.nsh"
!include "LogicLib.nsh"
!include "FileFunc.nsh"
!include "nsDialogs.nsh"
!include "x64.nsh"
!ifndef PAYLOAD
!error "PAYLOAD must be the verified weights-free release directory"
!endif
!ifndef OUTPUT
!error "OUTPUT must be the new Setup.exe path"
!endif
Name "Strata Legacy GPU"
OutFile "${OUTPUT}"
InstallDir "$LOCALAPPDATA\Strata Legacy GPU"
RequestExecutionLevel user
SetCompressor /FINAL zlib
ShowInstDetails show
Var VerifyOnly
Var ModelDirectory
Var ModelField
!define MUI_ABORTWARNING
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "${PAYLOAD}\THIRD_PARTY_NOTICES.md"
!insertmacro MUI_PAGE_DIRECTORY
Page custom ChooseModels SaveModels
!insertmacro MUI_PAGE_INSTFILES
!define MUI_FINISHPAGE_TEXT "Strata is installed. Swift uses the selected model files and its own local configuration. START.cmd starts the server; STOP.cmd drains it gracefully. No GPU driver is installed."
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_LANGUAGE "English"
!insertmacro MUI_LANGUAGE "Russian"

Function .onInit
  ${IfNot} ${RunningX64}
    MessageBox MB_ICONSTOP "Windows x64 is required."
    Abort
  ${EndIf}
  StrCpy $VerifyOnly "0"
  ${GetParameters} $0
  ClearErrors
  ${GetOptions} $0 "/VERIFYONLY" $1
  ${IfNot} ${Errors}
    StrCpy $VerifyOnly "1"
  ${EndIf}
  StrCpy $ModelDirectory ""
FunctionEnd

Function ChooseModels
  ${If} $VerifyOnly == "1"
    Abort
  ${EndIf}
  ${If} $ModelDirectory == ""
    StrCpy $ModelDirectory "$INSTDIR\models\swift-iq3_s"
  ${EndIf}
  nsDialogs::Create 1018
  Pop $0
  ${If} $0 == error
    Abort
  ${EndIf}
  ${NSD_CreateLabel} 0 0 100% 42u "Swift IQ3_S + Q2 MTP. Choose the folder with both GGUF shards and the CPU projector. Missing files are downloaded with resume and SHA-256 checks (about 84 GB). Existing configuration is never replaced."
  Pop $0
  ${NSD_CreateDirRequest} 0 50u 85% 14u "$ModelDirectory"
  Pop $ModelField
  ${NSD_CreateBrowseButton} 87% 50u 13% 14u "..."
  Pop $0
  ${NSD_OnClick} $0 BrowseModels
  nsDialogs::Show
FunctionEnd

Function BrowseModels
  nsDialogs::SelectFolderDialog "Swift model folder" "$ModelDirectory"
  Pop $0
  ${If} $0 != error
    StrCpy $ModelDirectory $0
    ${NSD_SetText} $ModelField $ModelDirectory
  ${EndIf}
FunctionEnd

Function SaveModels
  ${NSD_GetText} $ModelField $ModelDirectory
  ${If} $ModelDirectory == ""
    MessageBox MB_ICONSTOP "Choose a model folder."
    Abort
  ${EndIf}
FunctionEnd

Section "Strata"
  ; A fresh-folder installer must never overwrite a working installation or private state.
  IfFileExists "$INSTDIR\strata.json" Existing
  IfFileExists "$INSTDIR\runtime\active.json" Existing
  SetOutPath "$INSTDIR"
  File /r "${PAYLOAD}\*"
  ${If} $VerifyOnly == "1"
    nsExec::ExecToLog '"$INSTDIR\runtime\python\python.exe" -I -s -B "$INSTDIR\p40\windows\installer.py" --check-bundle'
    Pop $0
    ${If} $0 != 0
      SetErrorLevel 10
      Quit
    ${EndIf}
    nsExec::ExecToLog '"$INSTDIR\runtime\engine\strata.exe" --version'
    Pop $0
    ${If} $0 != 0
      SetErrorLevel 11
      Quit
    ${EndIf}
    SetErrorLevel 0
    Quit
  ${EndIf}
  DetailPrint "Checking the NVIDIA driver and Microsoft runtime."
  nsExec::ExecToLog '"$WINDIR\Sysnative\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -ExecutionPolicy Bypass -File "$INSTDIR\p40\windows\prerequisites.ps1"'
  Pop $0
  ${If} $0 != 0
    Goto Failed
  ${EndIf}
  DetailPrint "Preparing Swift. Existing model files are verified; partial downloads resume."
  nsExec::ExecToLog '"$INSTDIR\runtime\python\python.exe" -I -s -B "$INSTDIR\p40\windows\installer.py" --backend native --models-dir "$ModelDirectory"'
  Pop $0
  ${If} $0 != 0
    Goto Failed
  ${EndIf}
  nsExec::ExecToLog '"$WINDIR\Sysnative\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -ExecutionPolicy Bypass -File "$INSTDIR\p40\windows\autostart.ps1"'
  Pop $0
  ${If} $0 != 0
    Goto Failed
  ${EndIf}
  CreateShortcut "$DESKTOP\Strata Legacy GPU.lnk" "$INSTDIR\START.cmd" "" "$INSTDIR\runtime\engine\strata.exe"
  CreateShortcut "$DESKTOP\Stop Strata Legacy GPU.lnk" "$INSTDIR\STOP.cmd"
  Goto Done
Existing:
  MessageBox MB_ICONSTOP "Existing Strata settings or runtime state were found. They are preserved. Choose a new empty installation folder; use the managed updater for an existing installation."
  SetErrorLevel 12
  Quit
Failed:
  MessageBox MB_ICONSTOP "Setup did not finish. Existing files and partial downloads are preserved. Run INSTALL.cmd to resume. No process was force-stopped."
  SetErrorLevel 13
Done:
SectionEnd
