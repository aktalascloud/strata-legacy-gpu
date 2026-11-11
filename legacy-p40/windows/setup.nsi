Unicode true
!include "MUI2.nsh"
!include "LogicLib.nsh"
!include "FileFunc.nsh"
!include "x64.nsh"

Name "Strata Legacy GPU"
OutFile "${OUTPUT}"
InstallDir "$LOCALAPPDATA\Strata Legacy GPU"
RequestExecutionLevel user
SetCompressor /FINAL zlib
ShowInstDetails show
Var VerifyOnly

!insertmacro MUI_PAGE_LICENSE "${PAYLOAD}\licenses\NVIDIA-CUDA-12.9.txt"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!define MUI_FINISHPAGE_TEXT "Strata Legacy GPU is installed. Run CONFIGURE.cmd with the folder containing your Swift IQ3_S GGUF shards. Run START.cmd to serve it and STOP.cmd to stop it. Model files are supplied separately."
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_LANGUAGE "English"
!insertmacro MUI_LANGUAGE "Russian"

Function .onInit
  ${IfNot} ${RunningX64}
    MessageBox MB_ICONSTOP "Windows x64 is required."
    Abort
  ${EndIf}
  StrCpy $VerifyOnly 0
  ${GetParameters} $0
  ClearErrors
  ${GetOptions} $0 "/VERIFYONLY" $1
  ${IfNot} ${Errors}
    StrCpy $VerifyOnly 1
  ${EndIf}
FunctionEnd

Section "Strata Legacy GPU"
  IfFileExists "$INSTDIR\runtime\strata.json" Existing
  IfFileExists "$INSTDIR\runtime\ready.json" Existing
  IfFileExists "$INSTDIR\runtime\engine\strata.exe" Existing
  SetOutPath "$INSTDIR"
  File /r "${PAYLOAD}\*"
  ${If} $VerifyOnly == 1
    SetOutPath "$INSTDIR\runtime\cuda"
    nsExec::ExecToLog '"$INSTDIR\runtime\engine\strata.exe" --version'
    Pop $0
    ${If} $0 != 0
      SetErrorLevel 10
      Quit
    ${EndIf}
    nsExec::ExecToLog '"$INSTDIR\runtime\python\python.exe" -B "$INSTDIR\tools\serve-swift.py" --check-import'
    Pop $0
    ${If} $0 != 0
      SetErrorLevel 11
      Quit
    ${EndIf}
  ${EndIf}
  Goto Done
Existing:
  IfSilent +2
  MessageBox MB_ICONSTOP "Existing Strata files found. Choose a new folder."
  SetErrorLevel 12
  Quit
Done:
SectionEnd
