@echo off
setlocal

REM Resolve paths relative to this script
set "SCRIPT_DIR=%~dp0..\"
set "PLUGIN_DIR=%SCRIPT_DIR%plugin"
set "OUTPUT_ZIP=%SCRIPT_DIR%plugin.zip"
set "OUTPUT_PLUGIN=%SCRIPT_DIR%plugin.plugin"

if not exist "%PLUGIN_DIR%" (
    echo Plugin folder not found at "%PLUGIN_DIR%".
    exit /b 1
)

REM Remove previous archive if it exists
if exist "%OUTPUT_ZIP%" del "%OUTPUT_ZIP%"
if exist "%OUTPUT_PLUGIN%" del "%OUTPUT_PLUGIN%"

REM Create zip archive of the plugin folder
powershell -NoLogo -NoProfile -Command "Compress-Archive -Path \"%PLUGIN_DIR%\\*\" -DestinationPath \"%OUTPUT_ZIP%\" -Force"

if not exist "%OUTPUT_ZIP%" (
    echo Failed to create archive.
    exit /b 1
)

REM Rename to .plugin extension
rename "%OUTPUT_ZIP%" "plugin.plugin" >nul 2>&1

REM Ensure the file ends up at the expected path
if exist "%SCRIPT_DIR%plugin.plugin" move /Y "%SCRIPT_DIR%plugin.plugin" "%OUTPUT_PLUGIN%" >nul

if exist "%OUTPUT_PLUGIN%" (
    echo Archive created: "%OUTPUT_PLUGIN%"
) else (
    echo Failed to rename archive to .plugin.
    exit /b 1
)

endlocal
