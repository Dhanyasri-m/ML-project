# 🚀 QUICK REFERENCE CARD

## One-Command Start
```powershell
.\start.ps1
```

## Manual Start (3 Steps)
```powershell
# 1. Activate environment
.\venv\Scripts\Activate.ps1

# 2. Install dependencies (first time only)
pip install -r requirements.txt

# 3. Start server
python api\main.py
```

## URLs
- **Dashboard**: http://127.0.0.1:5000
- **API Status**: http://127.0.0.1:5000/api/status
- **Current Data**: http://127.0.0.1:5000/api/parking/current
- **All Predictions**: http://127.0.0.1:5000/api/parking/predict/all
- **Specific Lot**: http://127.0.0.1:5000/api/parking/predict/LOT_001

## Key Stats to Remember
- **Accuracy**: 92.79% (±10%)
- **Training Data**: 57,600 records (60 days × 10 lots)
- **Parking Lots**: 10 different zones
- **Prediction Horizon**: 1 hour ahead
- **Model Size**: 479 KB
- **Training Time**: ~1 minute

## Files Structure
```
parking_project/
├── data/parking_data.csv          # Generated data
├── models/parking_predictor.h5    # Trained model
├── scripts/
│   ├── generate_data.py          # Data generation
│   └── train_model.py            # Model training
├── api/main.py                   # Flask server
├── web/index.html                # Dashboard
└── requirements.txt              # Dependencies
```

## Regenerate Everything
```powershell
# Delete old files
Remove-Item data\parking_data.csv -ErrorAction SilentlyContinue
Remove-Item models\* -ErrorAction SilentlyContinue

# Regenerate
python scripts\generate_data.py
python scripts\train_model.py
python api\main.py
```

## Troubleshooting
### Server won't start?
```powershell
# Check if port is in use
netstat -ano | findstr :5000

# Kill process (replace PID)
taskkill /PID <PID> /F
```

### Predictions showing errors?
- Check that models/ folder has all files
- Rerun: `python scripts\train_model.py`

### Dependencies issue?
```powershell
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall
```

## API Examples (PowerShell)
```powershell
# Get current parking status
Invoke-RestMethod http://127.0.0.1:5000/api/parking/current

# Get prediction for LOT_001
Invoke-RestMethod http://127.0.0.1:5000/api/parking/predict/LOT_001

# Get all predictions
Invoke-RestMethod http://127.0.0.1:5000/api/parking/predict/all
```

## Demo Talking Points
1. **"93% accuracy predicting parking 1 hour ahead"**
2. **"Trained on 2 months of realistic data"**
3. **"Real-time dashboard with live predictions"**
4. **"Different patterns for office/commercial/entertainment zones"**
5. **"RESTful API ready for mobile apps"**

## Key Features to Show
✅ Color-coded occupancy (Green/Yellow/Red)
✅ 1-hour predictions with confidence scores
✅ Trend indicators (filling up 📈 / emptying 📉)
✅ Auto-refresh every 30 seconds
✅ Zone-specific behavior (office busy 9-5, etc.)

## Stop Server
Press `Ctrl + C` in terminal

---

## Emergency Commands
```powershell
# Fresh start (if something breaks)
Remove-Item venv -Recurse -Force
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python scripts\generate_data.py
python scripts\train_model.py
python api\main.py
```

## Performance Specs
- **Data Generation**: ~30 seconds
- **Model Training**: ~1 minute (CPU)
- **Prediction Speed**: < 100ms
- **Dashboard Load**: < 1 second
- **Memory Usage**: ~500 MB

---

**For more details, see README.md and PRESENTATION_GUIDE.md**
