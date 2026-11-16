@echo off
if "%~1"=="" (
  echo Usage: CONFIGURE.cmd "model folder" [--mtp-dir "Q2 MTP folder"]
  exit /b 2
)
"%~dp0runtime\python\python.exe" -B "%~dp0tools\configure-swift.py" %*
if errorlevel 1 exit /b %errorlevel%
powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File "%~dp0tools\autostart.ps1"
exit /b %errorlevel%
