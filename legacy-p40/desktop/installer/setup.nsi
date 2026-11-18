!pragma codepage UTF8
Unicode true
!include "MUI2.nsh"
!include "nsDialogs.nsh"
!include "LogicLib.nsh"
!include "x64.nsh"
!include "StrFunc.nsh"
${StrStr}

Name "Strata Desktop (P40)"
OutFile "${OUTPUT}"
InstallDir "$LOCALAPPDATA\Strata Desktop P40"
RequestExecutionLevel user
SetCompressor /FINAL zlib
ShowInstDetails show
Var ModelDir
Var MtpDir
Var ModelInput
Var MtpInput

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "${PAYLOAD}\licenses\NVIDIA-CUDA-12.9.txt"
!insertmacro MUI_PAGE_DIRECTORY
Page custom ModelPage ModelPageLeave
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_LANGUAGE "Russian"
!insertmacro MUI_LANGUAGE "English"

Function .onInit
  StrCpy $LANGUAGE ${LANG_RUSSIAN}
  ${IfNot} ${RunningX64}
    MessageBox MB_ICONSTOP "Требуется 64-битная Windows."
    Abort
  ${EndIf}
  StrCpy $ModelDir ""
  StrCpy $MtpDir ""
FunctionEnd

Function PickModel
  nsDialogs::SelectFolderDialog "Выберите папку с ОБЕИМИ частями Swift IQ3_S GGUF" "$ModelDir"
  Pop $0
  ${If} $0 != error
    ${NSD_SetText} $ModelInput $0
  ${EndIf}
FunctionEnd

Function PickMtp
  nsDialogs::SelectFolderDialog "Выберите папку подготовленного Q2 MTP (необязательно)" "$MtpDir"
  Pop $0
  ${If} $0 != error
    ${NSD_SetText} $MtpInput $0
  ${EndIf}
FunctionEnd

Function ModelPage
  nsDialogs::Create 1018
  Pop $0
  ${If} $0 == error
    Abort
  ${EndIf}
  ${NSD_CreateLabel} 0 0 100% 28u "Выберите существующую папку Swift IQ3_S. Файлы модели не входят в установщик и не копируются."
  Pop $0
  ${NSD_CreateDirRequest} 0 31u 78% 13u "$ModelDir"
  Pop $ModelInput
  ${NSD_CreateBrowseButton} 80% 31u 20% 13u "Обзор..."
  Pop $0
  ${NSD_OnClick} $0 PickModel
  ${NSD_CreateLabel} 0 55u 100% 25u "Необязательно: выберите подготовленную папку Q2 MTP. Без неё MTP будет выключен."
  Pop $0
  ${NSD_CreateDirRequest} 0 83u 78% 13u "$MtpDir"
  Pop $MtpInput
  ${NSD_CreateBrowseButton} 80% 83u 20% 13u "Обзор..."
  Pop $0
  ${NSD_OnClick} $0 PickMtp
  nsDialogs::Show
FunctionEnd

Function ModelPageLeave
  ${NSD_GetText} $ModelInput $ModelDir
  ${NSD_GetText} $MtpInput $MtpDir
  ${StrStr} $0 $ModelDir '$\"'
  ${If} $0 != ""
    MessageBox MB_ICONEXCLAMATION "Путь к модели не должен содержать кавычки."
    Abort
  ${EndIf}
  ${StrStr} $0 $MtpDir '$\"'
  ${If} $0 != ""
    MessageBox MB_ICONEXCLAMATION "Путь к MTP не должен содержать кавычки."
    Abort
  ${EndIf}
  ${If} $ModelDir == ""
    MessageBox MB_ICONEXCLAMATION "Выберите папку модели Swift IQ3_S."
    Abort
  ${EndIf}
  ${If} $MtpDir == ""
    MessageBox MB_ICONINFORMATION "Папка Q2 MTP не выбрана. Модель будет работать без MTP."
  ${EndIf}
FunctionEnd

Section "Install"
  ClearErrors
  FindFirst $0 $1 "$INSTDIR\*"
  ${IfNot} ${Errors}
    ${DoWhile} $1 != ""
      ${If} $1 != "."
      ${AndIf} $1 != ".."
        FindClose $0
        Goto Existing
      ${EndIf}
      ClearErrors
      FindNext $0 $1
      ${If} ${Errors}
        ${ExitDo}
      ${EndIf}
    ${Loop}
    FindClose $0
  ${EndIf}
  SetOutPath "$INSTDIR"
  File /r "${PAYLOAD}\*"
  CreateDirectory "$INSTDIR\runtime"
  FileOpen $0 "$INSTDIR\runtime\server.lock" w
  FileClose $0
  DetailPrint "Подготавливаются файлы из вашей модели GGUF. Это может занять несколько минут."
  ${If} $MtpDir == ""
    nsExec::ExecToLog '"$INSTDIR\app\control\python\python.exe" -X utf8 -B "$INSTDIR\tools\configure_profile.py" --install-root "$INSTDIR" --model-dir "$ModelDir"'
  ${Else}
    nsExec::ExecToLog '"$INSTDIR\app\control\python\python.exe" -X utf8 -B "$INSTDIR\tools\configure_profile.py" --install-root "$INSTDIR" --model-dir "$ModelDir" --mtp-dir "$MtpDir"'
  ${EndIf}
  Pop $0
  ${If} $0 != 0
    SetErrorLevel 21
    MessageBox MB_ICONSTOP "Не удалось подготовить модель. Существующие файлы модели не удалены. Проверьте подробности установки."
    Quit
  ${EndIf}
  nsExec::ExecToLog '"$INSTDIR\app\control\python\python.exe" -B "$INSTDIR\tools\prepare_receipt.py" --root "$INSTDIR" --integrity-sha256 "${INTEGRITY_SHA256}" --create'
  Pop $0
  ${If} $0 != 0
    SetErrorLevel 22
    MessageBox MB_ICONSTOP "Не удалось создать проверочную квитанцию. Автозапуск не зарегистрирован."
    Quit
  ${EndIf}
  nsExec::ExecToLog '"$INSTDIR\app\control\python\python.exe" -X utf8 -B "$INSTDIR\tools\install_skill.py" --root "$INSTDIR"'
  Pop $0
  ${If} $0 != 0
    SetErrorLevel 24
    MessageBox MB_ICONSTOP "Не удалось подготовить навык Ponytail. Автозапуск не зарегистрирован."
    Quit
  ${EndIf}
  IfFileExists "$DESKTOP\Strata Desktop P40.lnk" ExistingShortcut
  CreateShortcut "$DESKTOP\Strata Desktop P40.lnk" "$WINDIR\System32\WindowsPowerShell\v1.0\powershell.exe" '-NoProfile -ExecutionPolicy Bypass -File "$INSTDIR\tools\start-desktop.ps1"' "$INSTDIR\app\strata-desktop.exe"
  Goto ShortcutDone
ExistingShortcut:
  DetailPrint "Существующий ярлык Strata Desktop P40 сохранён."
ShortcutDone:
  ReadRegStr $0 HKCU "Software\Microsoft\Windows\CurrentVersion\Run" "Strata Desktop P40"
  ${If} $0 != ""
    DetailPrint "Существующий автозапуск Strata Desktop P40 сохранён. Настройте новый только после проверки."
  ${Else}
    ReadRegStr $0 HKCU "Software\Microsoft\Windows\CurrentVersion\Run" "Strata Legacy GPU"
    ${If} $0 != ""
      DetailPrint "Старый автозапуск Strata сохранён. Новый не зарегистрирован, чтобы не запустить два движка."
    ${Else}
      nsExec::ExecToLog '"$WINDIR\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -NonInteractive -ExecutionPolicy Bypass -File "$INSTDIR\tools\check-old-task.ps1"'
      Pop $0
      ${If} $0 != 0
        DetailPrint "Планировщик содержит прежнюю задачу или недоступен. Новый автозапуск не зарегистрирован."
      ${Else}
        WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Run" "Strata Desktop P40" '"$WINDIR\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -ExecutionPolicy Bypass -File "$INSTDIR\tools\start-desktop.ps1"'
        ReadRegStr $0 HKCU "Software\Microsoft\Windows\CurrentVersion\Run" "Strata Desktop P40"
        ${If} $0 == ""
          SetErrorLevel 23
          MessageBox MB_ICONEXCLAMATION "Программа установлена, но автозапуск зарегистрировать не удалось."
        ${EndIf}
      ${EndIf}
    ${EndIf}
  ${EndIf}
  Goto Done
Existing:
  MessageBox MB_ICONSTOP "В этой папке уже есть Strata. Выберите новую папку."
  SetErrorLevel 12
  Quit
Done:
SectionEnd
