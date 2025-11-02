# Build script for Parlor frontend
# This script builds the Angular app for production deployment

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Parlor Frontend Production Build" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if environment.prod.ts has been configured
$envFile = "src\environments\environment.prod.ts"
$envContent = Get-Content $envFile -Raw

if ($envContent -match "YOUR_BACKEND_URL") {
    Write-Host "⚠️  WARNING: Production environment not configured!" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Please update $envFile" -ForegroundColor Yellow
    Write-Host "Replace 'YOUR_BACKEND_URL' with your actual backend URL" -ForegroundColor Yellow
    Write-Host ""
    $continue = Read-Host "Continue anyway? (y/N)"
    if ($continue -ne "y" -and $continue -ne "Y") {
        Write-Host "Build cancelled." -ForegroundColor Red
        exit 1
    }
}

Write-Host "🔨 Building for production..." -ForegroundColor Green
Write-Host ""

# Clean previous build
if (Test-Path "dist") {
    Write-Host "Cleaning previous build..." -ForegroundColor Gray
    Remove-Item -Recurse -Force dist
}

# Build the app
npm run build

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ Build completed successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Production files are in: dist\demo" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "1. Deploy the files in dist\demo to your hosting platform" -ForegroundColor White
    Write-Host "2. Update backend CORS to include your frontend domain" -ForegroundColor White
    Write-Host "3. Test your deployed application" -ForegroundColor White
    Write-Host ""
    Write-Host "To test locally first:" -ForegroundColor Yellow
    Write-Host "  npx http-server dist\demo -p 8080 -o" -ForegroundColor Cyan
    Write-Host ""
}
else {
    Write-Host ""
    Write-Host "❌ Build failed!" -ForegroundColor Red
    Write-Host "Please fix the errors above and try again." -ForegroundColor Red
    exit 1
}
