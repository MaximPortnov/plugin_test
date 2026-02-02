@echo off
setlocal

set "PYTHON_EXE=%~1"
if "%PYTHON_EXE%"=="" set "PYTHON_EXE=python"

set "VENV_PATH=%~2"
if "%VENV_PATH%"=="" set "VENV_PATH=.venv"

set "SCRIPT_DIR=%~dp0"
set "REPO_ROOT=%SCRIPT_DIR%.."
set "VENV_FULL=%REPO_ROOT%\%VENV_PATH%"

where %PYTHON_EXE% >nul 2>&1
if errorlevel 1 (
    echo Python executable "%PYTHON_EXE%" not found in PATH.
    exit /b 1
)

if not exist "%VENV_FULL%" (
    %PYTHON_EXE% -m venv "%VENV_FULL%"
    if errorlevel 1 exit /b 1
)

set "VENV_PY=%VENV_FULL%\Scripts\python.exe"
"%VENV_PY%" -m pip install --upgrade pip
if errorlevel 1 exit /b 1

if exist "%REPO_ROOT%\requirements.txt" (
    "%VENV_PY%" -m pip install -r "%REPO_ROOT%\requirements.txt"
    if errorlevel 1 exit /b 1
) else (
    echo requirements.txt not found; skipping package install.
)

echo Virtual env ready at "%VENV_FULL%"
endlocal
