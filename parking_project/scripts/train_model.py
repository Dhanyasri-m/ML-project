"""
LSTM Model Training for Spatio-Temporal Parking Prediction
Trains a deep learning model to predict parking occupancy 1 hour ahead
"""
import os
import pandas as pd
import numpy as np
from datetime import datetime
import pickle

# Suppress TensorFlow warnings
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint

# Paths
DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'parking_data.csv')
MODEL_PATH = os.path.join(os.path.dirname(__file__), '..', 'models', 'parking_predictor.h5')
SCALER_PATH = os.path.join(os.path.dirname(__file__), '..', 'models', 'scaler.pkl')
ENCODER_PATH = os.path.join(os.path.dirname(__file__), '..', 'models', 'encoder.pkl')

# Hyperparameters
SEQUENCE_LENGTH = 12  # Use last 3 hours (12 x 15-min intervals)
PREDICTION_HORIZON = 4  # Predict 1 hour ahead
BATCH_SIZE = 64
EPOCHS = 50

def load_and_prepare_data():
    """Load and preprocess parking data"""
    print("📂 Loading data...")
    df = pd.read_csv(DATA_PATH)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    print(f"✅ Loaded {len(df):,} records")
    print(f"   Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
    
    return df

def create_sequences(data, seq_length, pred_horizon):
    """Create sequences for LSTM training"""
    X, y = [], []
    
    for i in range(len(data) - seq_length - pred_horizon):
        X.append(data[i:i + seq_length])
        y.append(data[i + seq_length + pred_horizon - 1, 0])  # Predict occupancy_rate
    
    return np.array(X), np.array(y)

def prepare_features(df):
    """Engineer features for the model"""
    print("\n🔧 Engineering features...")
    
    # Encode categorical features
    zone_encoder = LabelEncoder()
    df['zone_encoded'] = zone_encoder.fit_transform(df['zone_type'])
    
    # Select features for training
    feature_cols = [
        'occupancy_rate',
        'hour',
        'day_of_week',
        'is_weekend',
        'is_holiday',
        'zone_encoded',
        'occupancy_1h_ago',
        'occupancy_3h_ago',
        'occupancy_24h_ago',
    ]
    
    # Normalize features
    scaler = StandardScaler()
    
    # Process each parking lot separately to maintain temporal order
    all_sequences_X = []
    all_sequences_y = []
    
    for lot_id in df['lot_id'].unique():
        lot_data = df[df['lot_id'] == lot_id][feature_cols].values
        
        # Skip if not enough data
        if len(lot_data) < SEQUENCE_LENGTH + PREDICTION_HORIZON:
            continue
        
        # Create sequences for this parking lot
        X_seq, y_seq = create_sequences(lot_data, SEQUENCE_LENGTH, PREDICTION_HORIZON)
        all_sequences_X.append(X_seq)
        all_sequences_y.append(y_seq)
    
    # Combine all sequences
    X = np.vstack(all_sequences_X)
    y = np.hstack(all_sequences_y)
    
    # Fit scaler on all data
    X_reshaped = X.reshape(-1, X.shape[-1])
    scaler.fit(X_reshaped)
    X_scaled = scaler.transform(X_reshaped).reshape(X.shape)
    
    print(f"✅ Created {len(X):,} sequences")
    print(f"   Input shape: {X.shape}")
    print(f"   Output shape: {y.shape}")
    
    return X_scaled, y, scaler, zone_encoder, feature_cols

def build_lstm_model(input_shape):
    """Build LSTM neural network"""
    print("\n🏗️  Building LSTM model...")
    
    model = keras.Sequential([
        # First LSTM layer with return sequences
        layers.LSTM(128, return_sequences=True, input_shape=input_shape),
        layers.Dropout(0.2),
        
        # Second LSTM layer
        layers.LSTM(64, return_sequences=False),
        layers.Dropout(0.2),
        
        # Dense layers
        layers.Dense(32, activation='relu'),
        layers.Dropout(0.2),
        layers.Dense(16, activation='relu'),
        
        # Output layer (occupancy rate between 0 and 1)
        layers.Dense(1, activation='sigmoid')
    ])
    
    model.compile(
        optimizer='adam',
        loss='mse',
        metrics=['mae', 'mse']
    )
    
    print("✅ Model architecture:")
    model.summary()
    
    return model

def train_model(model, X_train, y_train, X_val, y_val):
    """Train the LSTM model"""
    print("\n🚀 Training model...")
    
    # Callbacks
    early_stop = EarlyStopping(
        monitor='val_loss',
        patience=5,
        restore_best_weights=True,
        verbose=1
    )
    
    checkpoint = ModelCheckpoint(
        MODEL_PATH,
        monitor='val_loss',
        save_best_only=True,
        verbose=0
    )
    
    # Train
    history = model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=EPOCHS,
        batch_size=BATCH_SIZE,
        callbacks=[early_stop, checkpoint],
        verbose=1
    )
    
    return history

def evaluate_model(model, X_test, y_test):
    """Evaluate model performance"""
    print("\n📊 Evaluating model...")
    
    # Predictions
    y_pred = model.predict(X_test, verbose=0).flatten()
    
    # Metrics
    mae = np.mean(np.abs(y_test - y_pred))
    mse = np.mean((y_test - y_pred) ** 2)
    rmse = np.sqrt(mse)
    mape = np.mean(np.abs((y_test - y_pred) / (y_test + 1e-10))) * 100
    
    # Accuracy within 10% threshold
    accuracy_10 = np.mean(np.abs(y_test - y_pred) < 0.1) * 100
    
    print(f"\n✅ Model Performance:")
    print(f"   MAE:  {mae:.4f}")
    print(f"   RMSE: {rmse:.4f}")
    print(f"   MAPE: {mape:.2f}%")
    print(f"   Accuracy (±10%): {accuracy_10:.2f}%")
    
    return {
        'mae': float(mae),
        'rmse': float(rmse),
        'mape': float(mape),
        'accuracy_10': float(accuracy_10)
    }

def main():
    """Main training pipeline"""
    print("="*60)
    print("🚗 SPATIO-TEMPORAL PARKING PREDICTION - MODEL TRAINING")
    print("="*60)
    
    # Load data
    df = load_and_prepare_data()
    
    # Prepare features
    X, y, scaler, zone_encoder, feature_cols = prepare_features(df)
    
    # Split data (chronological split to avoid data leakage)
    split_idx = int(len(X) * 0.8)
    X_train, X_temp = X[:split_idx], X[split_idx:]
    y_train, y_temp = y[:split_idx], y[split_idx:]
    
    # Further split temp into validation and test
    val_idx = int(len(X_temp) * 0.5)
    X_val, X_test = X_temp[:val_idx], X_temp[val_idx:]
    y_val, y_test = y_temp[:val_idx], y_temp[val_idx:]
    
    print(f"\n📊 Data split:")
    print(f"   Training:   {len(X_train):,} samples")
    print(f"   Validation: {len(X_val):,} samples")
    print(f"   Test:       {len(X_test):,} samples")
    
    # Build model
    model = build_lstm_model(input_shape=(X_train.shape[1], X_train.shape[2]))
    
    # Train
    history = train_model(model, X_train, y_train, X_val, y_val)
    
    # Evaluate
    metrics = evaluate_model(model, X_test, y_test)
    
    # Save artifacts
    print("\n💾 Saving model artifacts...")
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    
    model.save(MODEL_PATH)
    print(f"   ✅ Model saved to: {MODEL_PATH}")
    
    with open(SCALER_PATH, 'wb') as f:
        pickle.dump(scaler, f)
    print(f"   ✅ Scaler saved to: {SCALER_PATH}")
    
    with open(ENCODER_PATH, 'wb') as f:
        pickle.dump(zone_encoder, f)
    print(f"   ✅ Encoder saved to: {ENCODER_PATH}")
    
    # Save feature names
    feature_info = {
        'feature_cols': feature_cols,
        'sequence_length': SEQUENCE_LENGTH,
        'prediction_horizon': PREDICTION_HORIZON,
        'metrics': metrics
    }
    
    with open(os.path.join(os.path.dirname(MODEL_PATH), 'model_info.pkl'), 'wb') as f:
        pickle.dump(feature_info, f)
    
    print("\n" + "="*60)
    print("🎉 TRAINING COMPLETE!")
    print("="*60)
    print(f"\n📈 Final Results:")
    print(f"   Model Accuracy: {metrics['accuracy_10']:.2f}%")
    print(f"   Ready for deployment! ✨")

if __name__ == '__main__':
    main()
