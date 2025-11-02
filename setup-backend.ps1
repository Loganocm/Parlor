# Setup script for Parlor backend
Write-Host "Setting up Parlor Backend..." -ForegroundColor Green

# Check if Python is installed
try {
    $pythonVersion = python --version
    Write-Host "Python found: $pythonVersion" -ForegroundColor Green
}
catch {
    Write-Host "Error: Python is not installed or not in PATH" -ForegroundColor Red
    exit 1
}

# Navigate to backend directory
$backendPath = Join-Path $PSScriptRoot "backend"
Set-Location $backendPath

# Create virtual environment
Write-Host "`nCreating virtual environment..." -ForegroundColor Yellow
if (Test-Path "venv") {
    Write-Host "Virtual environment already exists. Skipping creation." -ForegroundColor Cyan
}
else {
    python -m venv venv
    Write-Host "Virtual environment created successfully!" -ForegroundColor Green
}

# Activate virtual environment
Write-Host "`nActivating virtual environment..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"

# Upgrade pip
Write-Host "`nUpgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

# Install dependencies
Write-Host "`nInstalling dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

# Create .env file if it doesn't exist
if (-not (Test-Path ".env")) {
    Write-Host "`nCreating .env file from .env.example..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "Created .env file. Please edit it with your API keys!" -ForegroundColor Cyan
}
else {
    Write-Host "`n.env file already exists." -ForegroundColor Cyan
}

Write-Host "`n========================================" -ForegroundColor Green
Write-Host "Backend setup complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "`nNext steps:" -ForegroundColor Yellow
Write-Host "1. Edit backend\.env with your API keys" -ForegroundColor White
Write-Host "2. Run tests: cd backend; .\venv\Scripts\Activate.ps1; pytest tests/ -v" -ForegroundColor White
Write-Host "3. Start server: cd backend; .\venv\Scripts\Activate.ps1; python -m uvicorn app.main:app --reload --port 5000" -ForegroundColor White
Write-Host "`nFor frontend:" -ForegroundColor Yellow
Write-Host "1. npm install" -ForegroundColor White
Write-Host "2. npm start" -ForegroundColor White
