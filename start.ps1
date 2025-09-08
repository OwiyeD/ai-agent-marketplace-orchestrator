# AI Agent Marketplace Orchestrator - Windows Startup Script
# Run this script in PowerShell to start the orchestrator

Write-Host "🚀 AI Agent Marketplace Orchestrator - Starting up..." -ForegroundColor Green
Write-Host "=" * 60 -ForegroundColor Cyan

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found. Please install Python 3.8+ and add it to PATH" -ForegroundColor Red
    exit 1
}

# Check if pip is available
try {
    $pipVersion = pip --version 2>&1
    Write-Host "✅ pip found: $pipVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ pip not found. Please install pip" -ForegroundColor Red
    exit 1
}

# Install dependencies
Write-Host "📦 Installing dependencies..." -ForegroundColor Yellow
try {
    pip install -r requirements.txt
    Write-Host "✅ Dependencies installed successfully" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to install dependencies" -ForegroundColor Red
    exit 1
}

# Check if Docker is available for services
Write-Host "🐳 Checking Docker availability..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version 2>&1
    Write-Host "✅ Docker found: $dockerVersion" -ForegroundColor Green
    
    # Start services with Docker Compose
    Write-Host "🚀 Starting PostgreSQL and Redis with Docker Compose..." -ForegroundColor Yellow
    docker-compose up -d
    
    # Wait for services to be ready
    Write-Host "⏳ Waiting for services to be ready..." -ForegroundColor Yellow
    Start-Sleep -Seconds 10
    
} catch {
    Write-Host "⚠️  Docker not found. Please ensure PostgreSQL and Redis are running manually:" -ForegroundColor Yellow
    Write-Host "   - PostgreSQL on localhost:5432" -ForegroundColor White
    Write-Host "   - Redis on localhost:6379" -ForegroundColor White
    Write-Host "   Press any key to continue..." -ForegroundColor Cyan
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}

# Start Celery worker in background
Write-Host "🌱 Starting Celery worker..." -ForegroundColor Yellow
Start-Process -FilePath "celery" -ArgumentList "-A celery_app worker --loglevel=info" -WindowStyle Minimized

# Wait a moment for Celery to start
Start-Sleep -Seconds 3

# Start the main application
Write-Host "🚀 Starting FastAPI application..." -ForegroundColor Yellow
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "✅ Orchestrator is starting up!" -ForegroundColor Green
Write-Host "📖 API Documentation will be available at: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "🔍 Health Check: http://localhost:8000/health" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan

# Start the application
python start.py




