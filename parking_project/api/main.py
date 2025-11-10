"""
Flask API for Real-Time Parking Prediction
Serves predictions and current parking availability
"""
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import pandas as pd
import numpy as np
import pickle
import os
from datetime import datetime, timedelta

# Suppress TensorFlow warnings
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

try:
    from tensorflow import keras
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False
    print("⚠️  TensorFlow not installed. Install with: pip install tensorflow")

app = Flask(__name__, static_folder='../web', static_url_path='')
CORS(app)

# Paths
BASE_DIR = os.path.dirname(__file__)
DATA_PATH = os.path.join(BASE_DIR, '..', 'data', 'parking_data.csv')
MODEL_PATH = os.path.join(BASE_DIR, '..', 'models', 'parking_predictor.h5')
SCALER_PATH = os.path.join(BASE_DIR, '..', 'models', 'scaler.pkl')
ENCODER_PATH = os.path.join(BASE_DIR, '..', 'models', 'encoder.pkl')
INFO_PATH = os.path.join(BASE_DIR, '..', 'models', 'model_info.pkl')

# Global variables for loaded models
model = None
scaler = None
zone_encoder = None
model_info = None
df_data = None

def load_models():
    """Load trained model and preprocessing artifacts"""
    global model, scaler, zone_encoder, model_info, df_data
    
    print("🔄 Loading models...")
    
    try:
        # Load data
        if os.path.exists(DATA_PATH):
            df_data = pd.read_csv(DATA_PATH)
            df_data['timestamp'] = pd.to_datetime(df_data['timestamp'])
            print(f"✅ Data loaded: {len(df_data):,} records")
        else:
            print("⚠️  Data not found. Run generate_data.py first.")
            return False
        
        # Load model
        if TENSORFLOW_AVAILABLE and os.path.exists(MODEL_PATH):
            model = keras.models.load_model(MODEL_PATH)
            print("✅ Model loaded")
        else:
            print("⚠️  Model not found. Run train_model.py first.")
            return False
        
        # Load preprocessing artifacts
        if os.path.exists(SCALER_PATH):
            with open(SCALER_PATH, 'rb') as f:
                scaler = pickle.load(f)
            print("✅ Scaler loaded")
        
        if os.path.exists(ENCODER_PATH):
            with open(ENCODER_PATH, 'rb') as f:
                zone_encoder = pickle.load(f)
            print("✅ Encoder loaded")
        
        if os.path.exists(INFO_PATH):
            with open(INFO_PATH, 'rb') as f:
                model_info = pickle.load(f)
            print("✅ Model info loaded")
        
        print("🎉 All models loaded successfully!\n")
        return True
        
    except Exception as e:
        print(f"❌ Error loading models: {e}")
        return False

def get_current_data():
    """Get most recent data for all parking lots"""
    if df_data is None:
        return None
    
    # Get latest timestamp
    latest_time = df_data['timestamp'].max()
    current_data = df_data[df_data['timestamp'] == latest_time].copy()
    
    return current_data

def predict_occupancy(lot_id, hours_ahead=1):
    """Predict parking occupancy for a specific lot"""
    if model is None or df_data is None:
        return None
    
    try:
        # Get historical data for this lot
        lot_data = df_data[df_data['lot_id'] == lot_id].copy()
        
        if len(lot_data) < model_info['sequence_length']:
            return None
        
        # Get last sequence
        feature_cols = model_info['feature_cols']
        
        # Get recent data
        recent = lot_data.tail(model_info['sequence_length']).copy()
        
        # Prepare zone encoding for recent data if not present
        if 'zone_encoded' not in recent.columns:
            zone = recent.iloc[-1]['zone_type']
            zone_encoded = zone_encoder.transform([zone])[0]
            recent['zone_encoded'] = zone_encoded
        
        # Create feature array
        sequence = recent[feature_cols].values
        
        # Scale features
        sequence_scaled = scaler.transform(sequence.reshape(-1, sequence.shape[-1])).reshape(1, sequence.shape[0], sequence.shape[1])
        
        # Predict
        prediction = model.predict(sequence_scaled, verbose=0)[0][0]
        
        # Calculate confidence based on recent variability
        recent_std = recent['occupancy_rate'].std()
        confidence = max(0, 100 - (recent_std * 200))  # Higher std = lower confidence
        
        return {
            'predicted_occupancy': float(prediction),
            'confidence': float(confidence),
            'current_occupancy': float(recent.iloc[-1]['occupancy_rate'])
        }
        
    except Exception as e:
        print(f"Error predicting for {lot_id}: {e}")
        return None

@app.route('/')
def index():
    """Serve the web dashboard"""
    return send_from_directory('../web', 'index.html')

@app.route('/api/status')
def status():
    """API health check"""
    return jsonify({
        'status': 'online',
        'model_loaded': model is not None,
        'data_loaded': df_data is not None,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/parking/current')
def get_current_parking():
    """Get current parking availability for all lots"""
    current = get_current_data()
    
    if current is None:
        return jsonify({'error': 'No data available'}), 404
    
    lots = []
    for _, row in current.iterrows():
        lots.append({
            'lot_id': row['lot_id'],
            'lot_name': row['lot_name'],
            'zone_type': row['zone_type'],
            'latitude': row['latitude'],
            'longitude': row['longitude'],
            'capacity': int(row['capacity']),
            'occupied_slots': int(row['occupied_slots']),
            'available_slots': int(row['available_slots']),
            'occupancy_rate': float(row['occupancy_rate']),
            'status': 'full' if row['occupancy_rate'] > 0.9 else 'busy' if row['occupancy_rate'] > 0.7 else 'available',
            'timestamp': row['timestamp'].isoformat()
        })
    
    return jsonify({
        'timestamp': current.iloc[0]['timestamp'].isoformat(),
        'parking_lots': lots,
        'total_capacity': int(current['capacity'].sum()),
        'total_occupied': int(current['occupied_slots'].sum()),
        'total_available': int(current['available_slots'].sum()),
        'average_occupancy': float(current['occupancy_rate'].mean())
    })

@app.route('/api/parking/predict/<lot_id>')
def predict_parking(lot_id):
    """Predict parking availability for a specific lot"""
    hours_ahead = request.args.get('hours', default=1, type=int)
    
    if model is None:
        return jsonify({'error': 'Model not loaded'}), 500
    
    prediction = predict_occupancy(lot_id, hours_ahead)
    
    if prediction is None:
        return jsonify({'error': 'Prediction failed'}), 500
    
    # Get current data for this lot
    current = get_current_data()
    lot_current = current[current['lot_id'] == lot_id].iloc[0]
    
    predicted_occupied = int(prediction['predicted_occupancy'] * lot_current['capacity'])
    predicted_available = lot_current['capacity'] - predicted_occupied
    
    return jsonify({
        'lot_id': lot_id,
        'lot_name': lot_current['lot_name'],
        'hours_ahead': hours_ahead,
        'prediction': {
            'occupancy_rate': prediction['predicted_occupancy'],
            'occupied_slots': predicted_occupied,
            'available_slots': predicted_available,
            'confidence': prediction['confidence'],
            'status': 'full' if prediction['predicted_occupancy'] > 0.9 else 'busy' if prediction['predicted_occupancy'] > 0.7 else 'available'
        },
        'current': {
            'occupancy_rate': prediction['current_occupancy'],
            'occupied_slots': int(lot_current['occupied_slots']),
            'available_slots': int(lot_current['available_slots'])
        },
        'change': {
            'occupancy_delta': prediction['predicted_occupancy'] - prediction['current_occupancy'],
            'trend': 'increasing' if prediction['predicted_occupancy'] > prediction['current_occupancy'] else 'decreasing'
        },
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/parking/predict/all')
def predict_all():
    """Get predictions for all parking lots"""
    current = get_current_data()
    
    if current is None:
        return jsonify({'error': 'No data available'}), 404
    
    predictions = []
    
    for _, row in current.iterrows():
        pred = predict_occupancy(row['lot_id'])
        
        if pred:
            predicted_occupied = int(pred['predicted_occupancy'] * row['capacity'])
            predicted_available = row['capacity'] - predicted_occupied
            
            predictions.append({
                'lot_id': row['lot_id'],
                'lot_name': row['lot_name'],
                'zone_type': row['zone_type'],
                'latitude': row['latitude'],
                'longitude': row['longitude'],
                'current_occupancy': float(pred['current_occupancy']),
                'predicted_occupancy': float(pred['predicted_occupancy']),
                'predicted_available': predicted_available,
                'confidence': float(pred['confidence']),
                'trend': 'up' if pred['predicted_occupancy'] > pred['current_occupancy'] else 'down'
            })
    
    return jsonify({
        'timestamp': datetime.now().isoformat(),
        'predictions': predictions
    })

@app.route('/api/analytics/summary')
def get_analytics():
    """Get analytics summary"""
    if df_data is None:
        return jsonify({'error': 'No data available'}), 404
    
    current = get_current_data()
    
    # Calculate statistics
    stats = {
        'total_records': len(df_data),
        'date_range': {
            'start': df_data['timestamp'].min().isoformat(),
            'end': df_data['timestamp'].max().isoformat()
        },
        'parking_lots': int(df_data['lot_id'].nunique()),
        'current_stats': {
            'average_occupancy': float(current['occupancy_rate'].mean()),
            'busiest_lot': current.nlargest(1, 'occupancy_rate').iloc[0]['lot_name'],
            'most_available_lot': current.nsmallest(1, 'occupancy_rate').iloc[0]['lot_name'],
            'total_capacity': int(current['capacity'].sum()),
            'total_available': int(current['available_slots'].sum())
        }
    }
    
    if model_info:
        stats['model_performance'] = model_info.get('metrics', {})
    
    return jsonify(stats)

@app.route('/api/parking/history/<lot_id>')
def get_history(lot_id):
    """Get historical data for a parking lot"""
    if df_data is None:
        return jsonify({'error': 'No data available'}), 404
    
    hours = request.args.get('hours', default=24, type=int)
    
    # Get data for last N hours
    end_time = df_data['timestamp'].max()
    start_time = end_time - timedelta(hours=hours)
    
    lot_history = df_data[
        (df_data['lot_id'] == lot_id) & 
        (df_data['timestamp'] >= start_time)
    ].copy()
    
    if len(lot_history) == 0:
        return jsonify({'error': 'No history found'}), 404
    
    history = []
    for _, row in lot_history.iterrows():
        history.append({
            'timestamp': row['timestamp'].isoformat(),
            'occupancy_rate': float(row['occupancy_rate']),
            'occupied_slots': int(row['occupied_slots']),
            'available_slots': int(row['available_slots'])
        })
    
    return jsonify({
        'lot_id': lot_id,
        'lot_name': lot_history.iloc[0]['lot_name'],
        'hours': hours,
        'history': history
    })

if __name__ == '__main__':
    print("="*60)
    print("🚗 PARKING PREDICTION API - STARTING")
    print("="*60)
    
    # Load models on startup
    if load_models():
        print("\n🌐 Starting Flask server...")
        print("   API: http://127.0.0.1:5000/api/status")
        print("   Dashboard: http://127.0.0.1:5000")
        print("\n✨ Server is ready!\n")
        
        app.run(host='127.0.0.1', port=5000, debug=True, use_reloader=False)
    else:
        print("\n❌ Failed to load models. Please run:")
        print("   1. python scripts/generate_data.py")
        print("   2. python scripts/train_model.py")
        print("   3. python api/main.py")
