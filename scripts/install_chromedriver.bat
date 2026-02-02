@echo off
setlocal

rem Usage: install_chromedriver.bat [version] [channel] [destination]
set "VERSION=%~1"
if "%VERSION%"=="" set "VERSION=143.0.7499.169"

set "CHANNEL=%~2"
if "%CHANNEL%"=="" set "CHANNEL=win64"

set "DEST=%~3"
if "%DEST%"=="" set "DEST=%~dp0..\chromedriver-win64"

set "URL=https://storage.googleapis.com/chrome-for-testing-public/%VERSION%/%CHANNEL%/chromedriver-%CHANNEL%.zip"
set "ZIP=%TEMP%\chromedriver-%CHANNEL%.zip"

echo Downloading ChromeDriver from %URL% ...
powershell -NoLogo -NoProfile -Command "Invoke-WebRequest -Uri '%URL%' -OutFile '%ZIP%' -UseBasicParsing"
if errorlevel 1 (
    echo Failed to download ChromeDriver.
    exit /b 1
)

echo Extracting to %DEST% ...
powershell -NoLogo -NoProfile -Command "New-Item -ItemType Directory -Path '%DEST%' -Force ^| Out-Null; Expand-Archive -Path '%ZIP%' -DestinationPath '%DEST%' -Force"
if errorlevel 1 (
    echo Failed to extract ChromeDriver.
    exit /b 1
)

if exist "%DEST%\chromedriver-%CHANNEL%\chromedriver.exe" (
    copy /Y "%DEST%\chromedriver-%CHANNEL%\chromedriver.exe" "%DEST%\chromedriver.exe" >nul
)

echo Cleaning up temporary files...
del "%ZIP%" >nul 2>&1

echo ChromeDriver installed to %DEST%\chromedriver.exe
endlocal
