param(
    [string]$PythonExe = "python",
    [string]$VenvPath = ".venv"
)

$repoRoot = Split-Path $PSScriptRoot -Parent
$venvFull = Join-Path $repoRoot $VenvPath

if (-not (Get-Command $PythonExe -ErrorAction SilentlyContinue)) {
    Write-Error "Python executable '$PythonExe' not found in PATH."
    exit 1
}

if (-not (Test-Path $venvFull)) {
    & $PythonExe -m venv $venvFull
}

$venvPython = Join-Path $venvFull "Scripts\python.exe"

& $venvPython -m pip install --upgrade pip

$reqRoot = Join-Path $repoRoot "requirements.txt"
if (Test-Path $reqRoot) {
    & $venvPython -m pip install -r $reqRoot
} else {
    Write-Warning "requirements.txt not found; skipping package install."
}

Write-Host "Virtual env ready at $venvFull"
