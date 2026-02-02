param(
    [string]$Version = "143.0.7499.169",
    [string]$Channel = "win64",
    [string]$Destination = ""
)

$repoRoot = Split-Path $PSScriptRoot -Parent
if (-not $Destination) {
    $Destination = Join-Path $repoRoot "chromedriver-win64"
} else {
    $Destination = Resolve-Path -Path $Destination -ErrorAction SilentlyContinue -ErrorVariable ev
    if (-not $Destination) { $Destination = Join-Path $repoRoot "chromedriver-win64" }
}

$url = "https://storage.googleapis.com/chrome-for-testing-public/$Version/$Channel/chromedriver-$Channel.zip"
$tmpZip = Join-Path $env:TEMP "chromedriver-$Channel.zip"

Write-Host "Downloading $url ..."
Invoke-WebRequest -Uri $url -OutFile $tmpZip -UseBasicParsing

if (-not (Test-Path $tmpZip)) {
    Write-Error "Download failed: $tmpZip not found."
    exit 1
}

Write-Host "Extracting to $Destination ..."
New-Item -ItemType Directory -Path $Destination -Force | Out-Null
Expand-Archive -Path $tmpZip -DestinationPath $Destination -Force

# ChromeForTesting archive contains nested folder chromedriver-<channel>
$nested = Join-Path $Destination "chromedriver-$Channel"
$exeSrc = Join-Path $nested "chromedriver.exe"
if (Test-Path $exeSrc) {
    Copy-Item $exeSrc (Join-Path $Destination "chromedriver.exe") -Force
}

Remove-Item $tmpZip -Force
Write-Host "Chromedriver ready at $(Join-Path $Destination 'chromedriver.exe')"
