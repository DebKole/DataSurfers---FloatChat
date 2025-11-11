@echo off
setlocal enableextensions enabledelayedexpansion

rem ===== Configuration =====
set DEST=D:\argo\indian_ocean
set ACCEPT=
set LOGDIR=D:\argo\logs
rem ==========================

if not exist "%LOGDIR%" mkdir "%LOGDIR%"

for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyy-MM-dd_HHmmss"') do set TS=%%i

set ACCEPT_FLAG=
if not "%ACCEPT%"=="" set ACCEPT_FLAG=--accept "%ACCEPT%"

python "f:\windsurf\scripts\argo_mirror.py" --dest "%DEST%" !ACCEPT_FLAG! >> "%LOGDIR%\mirror-!TS!.log" 2>&1

endlocal
