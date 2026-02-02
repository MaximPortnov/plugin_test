@echo off
setlocal

rem Usage: run_tests.bat [venv_path] [port] [start]
set "VENV_PATH=%~1"
if "%VENV_PATH%"=="" set "VENV_PATH=.venv"

set "PORT=%~2"
if "%PORT%"=="" set "PORT=9222"

set "START_OO=%~3"

set "SCRIPT_DIR=%~dp0"
set "REPO_ROOT=%SCRIPT_DIR%.."
set "PYTHON_EXE=%REPO_ROOT%\%VENV_PATH%\Scripts\python.exe"

if not exist "%PYTHON_EXE%" (
    echo Python executable not found at "%PYTHON_EXE%". Run scripts\setup_env.bat first.
    exit /b 1
)

set "CHROMEDRIVER_PATH=%REPO_ROOT%\chromedriver-win64\chromedriver.exe"
if exist "%CHROMEDRIVER_PATH%" (
    set "CHROMEDRIVER_PATH=%CHROMEDRIVER_PATH%"
) else (
    echo chromedriver not found at %CHROMEDRIVER_PATH%. Run scripts\install_chromedriver.bat
)

if /I "%START_OO%"=="start" (
    call "%SCRIPT_DIR%start_onlyoffice.bat" %PORT%
    timeout /t 3 >nul
)

echo Running tests with %PYTHON_EXE% ...
"%PYTHON_EXE%" "%REPO_ROOT%\test\my_test.py"

endlocal
