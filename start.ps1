# Start both backend and frontend servers
Write-Host "🍕 Starting Parlor Pizza Recommendation System..." -ForegroundColor Green

# Start Backend
Write-Host "`n🔧 Starting Backend Server (port 8000)..." -ForegroundColor Cyan
$backendPath = Join-Path $PSScriptRoot "backend"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$backendPath'; .\venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000"

# Wait a moment for backend to start
Start-Sleep -Seconds 3

# Start Frontend
Write-Host "🎨 Starting Frontend Server (port 4200)..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot'; npm start"

Write-Host "`n✅ Both servers starting!" -ForegroundColor Green
Write-Host "   Backend:  http://localhost:8000" -ForegroundColor Yellow
Write-Host "   Frontend: http://localhost:4200" -ForegroundColor Yellow
Write-Host "   API Docs: http://localhost:8000/docs" -ForegroundColor Yellow
