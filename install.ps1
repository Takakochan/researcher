# Researcher installer for Windows (PowerShell)
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$uv = Get-Command uv -ErrorAction SilentlyContinue
if ($uv) {
    $uvExe = $uv.Source
} else {
    Write-Host "Installing uv..."
    Invoke-RestMethod https://astral.sh/uv/install.ps1 | Invoke-Expression
    $uvExe = Join-Path $env:USERPROFILE ".local\bin\uv.exe"
    if (-not (Test-Path $uvExe)) { throw "uv installation failed" }
}

Write-Host "Installing dependencies..."
& $uvExe sync
if ($LASTEXITCODE -ne 0) { throw "uv sync failed" }

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Created .env - open it and fill in TOKEN_FACTORY_API_KEY and TAVILY_API_KEY."
}

Write-Host ""
Write-Host "Done. Usage:  .\research.bat ""your research topic"""
