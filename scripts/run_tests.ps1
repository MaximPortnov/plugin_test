param(
    [string]$VenvPath = ".venv",
    [int]$Port = 9222,
    [switch]$StartOnlyOffice
)

$repoRoot = Split-Path $PSScriptRoot -Parent
$venvFull = Join-Path $repoRoot $VenvPath
$python = Join-Path $VenvPath "Scripts\python.exe"
if (-not (Test-Path (Join-Path $repoRoot $python))) {
    Write-Error "Python executable not found at $python. Run scripts/setup_env.ps1 first."
    exit 1
}

$python = Join-Path $venvFull "Scripts\python.exe"
$driverPath = Join-Path $repoRoot "chromedriver-win64\chromedriver.exe"
if (-not (Test-Path $driverPath)) {
    Write-Warning "chromedriver not found at $driverPath. Run scripts/install_chromedriver.ps1."
} else {
    $env:CHROMEDRIVER_PATH = (Resolve-Path $driverPath)
}

if ($StartOnlyOffice) {
    & "$PSScriptRoot\start_onlyoffice.ps1" -Port $Port
    Start-Sleep -Seconds 3
}

Write-Host "Running tests with $python ..."
& $python (Join-Path $repoRoot "test\my_test.py")
