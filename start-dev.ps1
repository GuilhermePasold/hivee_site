# Starts the HIVEE backend (Daphne/ASGI on :8000) and frontend (Vite on :5200).
# Use this script for local visual tests, especially the chat WebSocket.

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
$backend = Join-Path $root "backend"
$frontend = Join-Path $root "frontend"
$py = Join-Path $backend "venv\Scripts\python.exe"
$daphne = Join-Path $backend "venv\Scripts\daphne.exe"
$logDir = Join-Path $root ".run-logs"

New-Item -ItemType Directory -Force -Path $logDir | Out-Null

if (-not (Test-Path $py)) {
    Write-Host "Creating backend venv and installing dependencies..." -ForegroundColor Yellow
    python -m venv (Join-Path $backend "venv")
    & $py -m pip install -r (Join-Path $backend "requirements.txt")
}

if (-not (Test-Path $daphne)) {
    Write-Host "Installing backend dependencies missing Daphne..." -ForegroundColor Yellow
    & $py -m pip install -r (Join-Path $backend "requirements.txt")
}

if (-not (Test-Path (Join-Path $frontend "node_modules"))) {
    Write-Host "Installing frontend dependencies..." -ForegroundColor Yellow
    Push-Location $frontend
    npm install
    Pop-Location
}

Write-Host "Applying migrations..." -ForegroundColor Cyan
& $py (Join-Path $backend "manage.py") migrate

$providerCountOutput = & $py (Join-Path $backend "manage.py") shell -c "from catalog.models import Provider; print(Provider.objects.count())"
$providerCount = [int]($providerCountOutput | Select-Object -Last 1)
if ($providerCount -eq 0) {
    Write-Host "Seeding demo providers..." -ForegroundColor Cyan
    & $py (Join-Path $backend "manage.py") seed
}

$faqCountOutput = & $py (Join-Path $backend "manage.py") shell -c "from catalog.models import FAQArticle; print(FAQArticle.objects.count())"
$faqCount = [int]($faqCountOutput | Select-Object -Last 1)
if ($faqCount -eq 0) {
    Write-Host "Seeding support FAQ..." -ForegroundColor Cyan
    & $py (Join-Path $backend "manage.py") seed_support
}

Write-Host "Stopping previous listeners on ports 8000 and 5200..." -ForegroundColor Cyan
foreach ($port in @(8000, 5200)) {
    $owners = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue |
        Select-Object -ExpandProperty OwningProcess -Unique
    foreach ($owner in $owners) {
        Stop-Process -Id $owner -Force -ErrorAction SilentlyContinue
    }
}

Write-Host "Starting backend: http://127.0.0.1:8000" -ForegroundColor Green
Start-Process powershell -ArgumentList @(
    "-NoExit", "-Command",
    "Set-Location '$backend'; `$env:PYTHONIOENCODING='utf-8'; & '$daphne' -p 8000 hivee.asgi:application"
)

Write-Host "Starting frontend: http://localhost:5200" -ForegroundColor Green
Start-Process powershell -ArgumentList @(
    "-NoExit", "-Command",
    "Set-Location '$frontend'; npm run dev"
)

Write-Host "Done. Open http://localhost:5200" -ForegroundColor Green
