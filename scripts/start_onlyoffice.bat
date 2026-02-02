@echo off
setlocal

rem Usage: start_onlyoffice.bat [port] [extra_args]
set "PORT=%~1"
if "%PORT%"=="" set "PORT=9222"

set "EXTRA=%~2"

set "OO_PATH=%ONLYOFFICE_PATH%"
if "%OO_PATH%"=="" set "OO_PATH=C:\Program Files\ONLYOFFICE\DesktopEditors\DesktopEditors.exe"

if not exist "%OO_PATH%" (
    echo OnlyOffice executable not found. Set ONLYOFFICE_PATH or edit this script.
    exit /b 1
)

set "ARGS=--remote-debugging-port=%PORT% %EXTRA%"
echo Starting OnlyOffice: "%OO_PATH%" %ARGS%
start "" "%OO_PATH%" %ARGS%

endlocal
