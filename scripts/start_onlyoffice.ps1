param(
    [string]$OnlyOfficePath = $env:ONLYOFFICE_PATH,
    [int]$Port = 9222,
    [string]$ExtraArgs = ""
)

if (-not $OnlyOfficePath) {
    # Typical install path; adjust if differs
    $OnlyOfficePath = "C:\Program Files\ONLYOFFICE\DesktopEditors\DesktopEditors.exe"
}

if (-not (Test-Path $OnlyOfficePath)) {
    Write-Error "OnlyOffice executable not found. Set ONLYOFFICE_PATH env var or edit this script."
    exit 1
}

$args = "--remote-debugging-port=$Port $ExtraArgs"
Write-Host "Starting OnlyOffice: $OnlyOfficePath $args"
Start-Process -FilePath $OnlyOfficePath -ArgumentList $args
