# Setup and run Flask application
Write-Host "Creating virtual environment..." -ForegroundColor Green
python -m venv venv

Write-Host "Activating virtual environment..." -ForegroundColor Green
& .\venv\Scripts\Activate.ps1

Write-Host "Installing dependencies..." -ForegroundColor Green
pip install -r requirements.txt

Write-Host "Setting up environment variables..." -ForegroundColor Green
if (-not (Test-Path .env)) {
    Write-Host "Creating .env file from .env.example..." -ForegroundColor Yellow
    Copy-Item .env.example .env
}

Write-Host "Initializing database..." -ForegroundColor Green
if (-not (Test-Path migrations)) {
    python -m flask db init
}
python -m flask db migrate -m "Initial migration"
python -m flask db upgrade

Write-Host "Starting Flask application..." -ForegroundColor Green
python run.py
