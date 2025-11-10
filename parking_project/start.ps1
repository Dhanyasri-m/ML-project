# 🚗 Quick Start Script for Parking Prediction System

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "🚗 PARKING PREDICTION SYSTEM - QUICK START" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Check if virtual environment exists
if (!(Test-Path "venv\Scripts\Activate.ps1")) {
    Write-Host "❌ Virtual environment not found. Creating..." -ForegroundColor Yellow
    python -m venv venv
    Write-Host "✅ Virtual environment created" -ForegroundColor Green
    Write-Host ""
}

# Activate virtual environment
Write-Host "🔄 Activating virtual environment..." -ForegroundColor Yellow
& .\venv\Scripts\Activate.ps1

# Check if dependencies are installed
Write-Host "🔄 Checking dependencies..." -ForegroundColor Yellow
$pipList = pip list
if (!($pipList -match "tensorflow")) {
    Write-Host "📦 Installing dependencies..." -ForegroundColor Yellow
    pip install -r requirements.txt
    Write-Host "✅ Dependencies installed" -ForegroundColor Green
} else {
    Write-Host "✅ Dependencies already installed" -ForegroundColor Green
}
Write-Host ""

# Check if data exists
if (!(Test-Path "data\parking_data.csv")) {
    Write-Host "📊 Generating data..." -ForegroundColor Yellow
    python scripts\generate_data.py
    Write-Host ""
} else {
    Write-Host "✅ Data file exists" -ForegroundColor Green
}

# Check if model exists
if (!(Test-Path "models\parking_predictor.h5")) {
    Write-Host "🧠 Training model..." -ForegroundColor Yellow
    python scripts\train_model.py
    Write-Host ""
} else {
    Write-Host "✅ Model exists" -ForegroundColor Green
}

# Start the API server
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "🚀 STARTING API SERVER..." -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📍 Dashboard: http://127.0.0.1:5000" -ForegroundColor Green
Write-Host "📍 API Status: http://127.0.0.1:5000/api/status" -ForegroundColor Green
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

python api\main.py
