Unicode true
!include "MUI2.nsh"
!include "nsDialogs.nsh"
!include "LogicLib.nsh"
!include "x64.nsh"
!include "StrFunc.nsh"
!include "FileFunc.nsh"
${StrStr}

Name "Strata Desktop (P40)"
!ifndef VERSION
  !define VERSION "0.2.15.4"
!endif
VIProductVersion "${VERSION}"
VIAddVersionKey "ProductName" "Strata Desktop P40"
VIAddVersionKey "FileDescription" "Strata Desktop P40 Setup"
VIAddVersionKey "FileVersion" "${VERSION}"
VIAddVersionKey "ProductVersion" "${VERSION}"
VIAddVersionKey "LegalCopyright" "Copyright (c) 2026 the Strata contributors"
OutFile "${OUTPUT}"
InstallDir "$LOCALAPPDATA\Strata Desktop P40"
RequestExecutionLevel user
SetCompressor /FINAL zlib
ShowInstDetails show
Var ModelDir
Var MtpDir
Var ModelInput
Var MtpInput
Var VerifyOnly

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "${PAYLOAD}\licenses\NVIDIA-CUDA-12.9.txt"
!insertmacro MUI_PAGE_DIRECTORY
Page custom ModelPage ModelPageLeave
!insertmacro MUI_PAGE_INSTFILES
!define MUI_FINISHPAGE_RUN
!define MUI_FINISHPAGE_RUN_TEXT "Запустить Strata Desktop"
!define MUI_FINISHPAGE_RUN_FUNCTION StartDesktop
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_LANGUAGE "Russian"
!insertmacro MUI_LANGUAGE "English"

Function StartDesktop
  Exec '"$WINDIR\Sysnative\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File "$INSTDIR\tools\start-desktop.ps1"'
FunctionEnd

Function .onInit
  StrCpy $LANGUAGE ${LANG_RUSSIAN}
  ${IfNot} ${RunningX64}
    MessageBox MB_ICONSTOP "Требуется 64-битная Windows."
    Abort
  ${EndIf}
  StrCpy $ModelDir ""
  StrCpy $MtpDir ""
  StrCpy $VerifyOnly 0
  ${GetParameters} $0
  ClearErrors
  ${GetOptions} $0 "/VERIFYONLY" $1
  ${IfNot} ${Errors}
    StrCpy $VerifyOnly 1
    SetSilent silent
  ${EndIf}
!ifdef QUALIFICATION
  ${If} $VerifyOnly != 1
    SetErrorLevel 20
    Quit
  ${EndIf}
!endif
  InitPluginsDir
  File /oname=$PLUGINSDIR\system-vc-runtime.ps1 "${PAYLOAD}\tools\system-vc-runtime.ps1"
  nsExec::ExecToLog '"$WINDIR\Sysnative\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -NonInteractive -ExecutionPolicy Bypass -File "$PLUGINSDIR\system-vc-runtime.ps1"'
  Pop $0
  ${If} $0 != 0
    SetErrorLevel 28
    IfSilent VcMissing
    MessageBox MB_ICONEXCLAMATION|MB_YESNO "Требуется Microsoft Visual C++ Redistributable x64 версии 14.51.36247 или новее. Открыть официальный сайт загрузки?" IDNO VcMissing
    ExecShell "open" "https://learn.microsoft.com/cpp/windows/latest-supported-vc-redist"
VcMissing:
    Quit
  ${EndIf}
  ${If} $VerifyOnly != 1
    ReadRegStr $0 HKLM "Software\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}" "pv"
    ${If} $0 == ""
    ${OrIf} $0 == "0.0.0.0"
      ReadRegStr $0 HKCU "Software\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}" "pv"
    ${EndIf}
    ${If} $0 == ""
    ${OrIf} $0 == "0.0.0.0"
      SetErrorLevel 27
      IfSilent WebViewMissing
      MessageBox MB_ICONEXCLAMATION|MB_YESNO "Для рабочего окна требуется Microsoft Edge WebView2 Runtime. Открыть официальный сайт загрузки?" IDNO WebViewMissing
      ExecShell "open" "https://developer.microsoft.com/microsoft-edge/webview2/"
WebViewMissing:
      Quit
    ${EndIf}
  ${EndIf}
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
  IfFileExists "$ModelDir\*swift*iq3_s*-00001-of-00002.gguf" +2 0
    Goto MissingModel
  IfFileExists "$ModelDir\*swift*iq3_s*-00002-of-00002.gguf" +2 0
    Goto MissingModel
  ${If} $MtpDir == ""
    MessageBox MB_ICONINFORMATION "Папка Q2 MTP не выбрана. Модель будет работать без MTP."
  ${Else}
    IfFileExists "$MtpDir\dense.bin" +2 0
      Goto MissingMtp
    IfFileExists "$MtpDir\dense.txt" +2 0
      Goto MissingMtp
    IfFileExists "$MtpDir\experts.bin" +2 0
      Goto MissingMtp
    IfFileExists "$MtpDir\draft_vocab.bin" +2 0
      Goto MissingMtp
  ${EndIf}
  Return
MissingModel:
  MessageBox MB_ICONEXCLAMATION "В выбранной папке не найдены обе части Swift IQ3_S GGUF."
  Abort
MissingMtp:
  MessageBox MB_ICONEXCLAMATION "В папке Q2 MTP нет всех обязательных файлов. Выберите подготовленный набор или оставьте поле пустым."
  Abort
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
  nsExec::ExecToLog '"$WINDIR\Sysnative\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -NonInteractive -ExecutionPolicy Bypass -File "$INSTDIR\tools\system-vc-runtime.ps1" -Destination "$INSTDIR\vision"'
  Pop $0
  ${If} $0 != 0
    SetErrorLevel 28
    IfSilent +2
    MessageBox MB_ICONSTOP "Не удалось скопировать проверенные файлы Microsoft Visual C++. Проверьте диагностический вывод утилиты установки."
    Quit
  ${EndIf}
  ${If} $VerifyOnly == 1
    nsExec::ExecToLog '"$INSTDIR\app\control\python\python.exe" -X utf8 -B "$INSTDIR\tools\verify_install.py" "$INSTDIR" "${INTEGRITY_SHA256}"'
    Pop $0
    ${If} $0 != 0
      SetErrorLevel 26
    ${EndIf}
    Goto Done
  ${EndIf}
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
  ClearErrors
  CreateShortcut "$DESKTOP\Strata Desktop P40.lnk" "$WINDIR\System32\WindowsPowerShell\v1.0\powershell.exe" '-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File "$INSTDIR\tools\start-desktop.ps1"' "$INSTDIR\app\strata-desktop.exe"
  IfErrors ShortcutFailed
  Goto ShortcutDone
ExistingShortcut:
  IfFileExists "$DESKTOP\Strata Desktop P40 (новый).lnk" ShortcutFailed
  ClearErrors
  CreateShortcut "$DESKTOP\Strata Desktop P40 (новый).lnk" "$WINDIR\System32\WindowsPowerShell\v1.0\powershell.exe" '-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File "$INSTDIR\tools\start-desktop.ps1"' "$INSTDIR\app\strata-desktop.exe"
  IfErrors ShortcutFailed
  DetailPrint "Существующий ярлык сохранён; создан отдельный новый ярлык."
  Goto ShortcutDone
ShortcutFailed:
  SetErrorLevel 25
  MessageBox MB_ICONEXCLAMATION "Не удалось создать новый ярлык. Существующие ярлыки сохранены."
ShortcutDone:
  ReadRegStr $0 HKCU "Software\Microsoft\Windows\CurrentVersion\Run" "Strata Desktop P40"
  ${If} $0 == ""
    ReadRegStr $0 HKCU "Software\Microsoft\Windows\CurrentVersion\Run" "Strata Desktop"
  ${EndIf}
  ${If} $0 != ""
    SetErrorLevel 23
    MessageBox MB_ICONEXCLAMATION "Существующий автозапуск Strata Desktop P40 сохранён. Новый автозапуск не настроен; проверьте его вручную."
  ${Else}
    ReadRegStr $0 HKCU "Software\Microsoft\Windows\CurrentVersion\Run" "Strata Legacy GPU"
    ${If} $0 != ""
      SetErrorLevel 23
      MessageBox MB_ICONEXCLAMATION "Старый автозапуск Strata сохранён. Новый не зарегистрирован, чтобы не запустить два движка."
    ${Else}
      nsExec::ExecToLog '"$WINDIR\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -NonInteractive -ExecutionPolicy Bypass -File "$INSTDIR\tools\check-old-task.ps1"'
      Pop $0
      ${If} $0 != 0
        SetErrorLevel 23
        MessageBox MB_ICONEXCLAMATION "Планировщик содержит прежнюю задачу или недоступен. Новый автозапуск не зарегистрирован."
      ${Else}
        WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Run" "Strata Desktop P40" '"$WINDIR\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File "$INSTDIR\tools\start-desktop.ps1"'
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
  IfSilent +2
  MessageBox MB_ICONSTOP "В этой папке уже есть Strata. Выберите новую папку."
  SetErrorLevel 12
  Quit
Done:
SectionEnd
