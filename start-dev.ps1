# Sobe backend (Django :8000) e frontend (Vite) em janelas separadas.
$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
$py = Join-Path $root "backend\venv\Scripts\python.exe"

if (-not (Test-Path $py)) {
    Write-Host "Criando venv e instalando dependencias do backend..." -ForegroundColor Yellow
    python -m venv (Join-Path $root "backend\venv")
    & $py -m pip install -r (Join-Path $root "backend\requirements.txt")
}

# Garante migracoes e seed na primeira execucao.
$db = Join-Path $root "backend\hivee.db"
& $py (Join-Path $root "backend\manage.py") migrate
if (-not (Test-Path $db) -or ((& $py (Join-Path $root "backend\manage.py") shell -c "from catalog.models import Provider; print(Provider.objects.count())") -eq "0")) {
    & $py (Join-Path $root "backend\manage.py") seed
}

Write-Host "Subindo backend (http://127.0.0.1:8000) e frontend (Vite)..." -ForegroundColor Green

Start-Process powershell -ArgumentList @(
    "-NoExit", "-Command",
    "`$env:PYTHONIOENCODING='utf-8'; & '$py' '$root\backend\manage.py' runserver 127.0.0.1:8000"
)

Start-Process powershell -ArgumentList @(
    "-NoExit", "-Command",
    "Set-Location '$root\frontend'; npm run dev"
)
