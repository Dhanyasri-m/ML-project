"""
Spatio-Temporal Parking Data Generator
Generates realistic parking occupancy data with spatial and temporal patterns
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

# Configuration
NUM_PARKING_LOTS = 10
DAYS_TO_GENERATE = 60  # 2 months of data
SAMPLES_PER_HOUR = 4   # Every 15 minutes
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'parking_data.csv')

# Define parking lots with spatial features
PARKING_LOTS = {
    'LOT_001': {'name': 'Downtown Mall', 'capacity': 200, 'zone': 'commercial', 'lat': 40.7128, 'lon': -74.0060},
    'LOT_002': {'name': 'City Hospital', 'capacity': 150, 'zone': 'healthcare', 'lat': 40.7148, 'lon': -74.0070},
    'LOT_003': {'name': 'Tech Park', 'capacity': 300, 'zone': 'office', 'lat': 40.7108, 'lon': -74.0050},
    'LOT_004': {'name': 'Sports Stadium', 'capacity': 500, 'zone': 'entertainment', 'lat': 40.7158, 'lon': -74.0040},
    'LOT_005': {'name': 'University Campus', 'capacity': 250, 'zone': 'education', 'lat': 40.7098, 'lon': -74.0080},
    'LOT_006': {'name': 'Residential Area A', 'capacity': 100, 'zone': 'residential', 'lat': 40.7138, 'lon': -74.0030},
    'LOT_007': {'name': 'Shopping District', 'capacity': 180, 'zone': 'commercial', 'lat': 40.7118, 'lon': -74.0065},
    'LOT_008': {'name': 'Train Station', 'capacity': 400, 'zone': 'transport', 'lat': 40.7168, 'lon': -74.0055},
    'LOT_009': {'name': 'Beach Front', 'capacity': 220, 'zone': 'recreation', 'lat': 40.7088, 'lon': -74.0045},
    'LOT_010': {'name': 'Airport Parking', 'capacity': 600, 'zone': 'transport', 'lat': 40.7178, 'lon': -74.0025},
}

def get_base_occupancy_rate(hour, day_of_week, zone):
    """Calculate base occupancy rate based on time and zone type"""
    # Weekend vs Weekday
    is_weekend = day_of_week >= 5
    
    # Zone-specific patterns
    if zone == 'office':
        if is_weekend:
            return 0.1 + 0.1 * np.random.random()
        if 8 <= hour <= 18:
            return 0.7 + 0.2 * np.random.random()
        return 0.2 + 0.1 * np.random.random()
    
    elif zone == 'commercial':
        if 10 <= hour <= 21:
            return 0.6 + 0.3 * np.random.random()
        return 0.2 + 0.15 * np.random.random()
    
    elif zone == 'healthcare':
        # Hospital parking is busy during day
        if 7 <= hour <= 20:
            return 0.5 + 0.3 * np.random.random()
        return 0.3 + 0.2 * np.random.random()
    
    elif zone == 'entertainment':
        # Busy evenings and weekends
        if is_weekend or (18 <= hour <= 23):
            return 0.6 + 0.3 * np.random.random()
        return 0.15 + 0.1 * np.random.random()
    
    elif zone == 'education':
        if is_weekend:
            return 0.1 + 0.05 * np.random.random()
        if 8 <= hour <= 17:
            return 0.7 + 0.2 * np.random.random()
        return 0.2 + 0.1 * np.random.random()
    
    elif zone == 'residential':
        # Inverse of office hours (people leave for work)
        if not is_weekend and 8 <= hour <= 18:
            return 0.3 + 0.1 * np.random.random()
        return 0.7 + 0.2 * np.random.random()
    
    elif zone == 'transport':
        # Busy during commute hours
        if hour in [7, 8, 9, 17, 18, 19]:
            return 0.8 + 0.15 * np.random.random()
        return 0.4 + 0.2 * np.random.random()
    
    elif zone == 'recreation':
        # Busy during good weather and weekends
        if is_weekend and 10 <= hour <= 18:
            return 0.7 + 0.2 * np.random.random()
        return 0.2 + 0.15 * np.random.random()
    
    return 0.3 + 0.2 * np.random.random()

def generate_parking_data():
    """Generate spatio-temporal parking occupancy dataset"""
    print("🚗 Generating spatio-temporal parking data...")
    
    data = []
    start_date = datetime.now() - timedelta(days=DAYS_TO_GENERATE)
    
    # Generate data for each time step
    total_samples = DAYS_TO_GENERATE * 24 * SAMPLES_PER_HOUR
    
    for i in range(total_samples):
        timestamp = start_date + timedelta(minutes=i * (60 // SAMPLES_PER_HOUR))
        hour = timestamp.hour
        day_of_week = timestamp.weekday()
        is_holiday = (timestamp.month == 12 and timestamp.day >= 20) or (timestamp.month == 1 and timestamp.day <= 5)
        
        # Generate data for each parking lot
        for lot_id, lot_info in PARKING_LOTS.items():
            # Base occupancy from temporal and zone patterns
            base_rate = get_base_occupancy_rate(hour, day_of_week, lot_info['zone'])
            
            # Add holiday effect
            if is_holiday and lot_info['zone'] in ['commercial', 'entertainment', 'recreation']:
                base_rate *= 1.3
            elif is_holiday and lot_info['zone'] in ['office', 'education']:
                base_rate *= 0.3
            
            # Add some temporal correlation (smooth transitions)
            if len(data) >= NUM_PARKING_LOTS and data[-NUM_PARKING_LOTS]['lot_id'] == lot_id:
                prev_rate = data[-NUM_PARKING_LOTS]['occupancy_rate']
                base_rate = 0.7 * prev_rate + 0.3 * base_rate
            
            # Clip to valid range
            occupancy_rate = np.clip(base_rate, 0.0, 1.0)
            occupied_slots = int(occupancy_rate * lot_info['capacity'])
            available_slots = lot_info['capacity'] - occupied_slots
            
            data.append({
                'timestamp': timestamp,
                'lot_id': lot_id,
                'lot_name': lot_info['name'],
                'zone_type': lot_info['zone'],
                'latitude': lot_info['lat'],
                'longitude': lot_info['lon'],
                'capacity': lot_info['capacity'],
                'occupied_slots': occupied_slots,
                'available_slots': available_slots,
                'occupancy_rate': occupancy_rate,
                'hour': hour,
                'day_of_week': day_of_week,
                'is_weekend': int(day_of_week >= 5),
                'is_holiday': int(is_holiday),
            })
        
        if i % 10000 == 0:
            print(f"  Progress: {i}/{total_samples} samples ({100*i/total_samples:.1f}%)")
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    # Add temporal features (lagged values)
    print("📊 Adding temporal features...")
    for lot_id in PARKING_LOTS.keys():
        lot_mask = df['lot_id'] == lot_id
        df.loc[lot_mask, 'occupancy_1h_ago'] = df.loc[lot_mask, 'occupancy_rate'].shift(4)
        df.loc[lot_mask, 'occupancy_3h_ago'] = df.loc[lot_mask, 'occupancy_rate'].shift(12)
        df.loc[lot_mask, 'occupancy_24h_ago'] = df.loc[lot_mask, 'occupancy_rate'].shift(96)
    
    # Fill NaN with current occupancy for first rows
    df['occupancy_1h_ago'].fillna(df['occupancy_rate'], inplace=True)
    df['occupancy_3h_ago'].fillna(df['occupancy_rate'], inplace=True)
    df['occupancy_24h_ago'].fillna(df['occupancy_rate'], inplace=True)
    
    # Save to CSV
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False)
    
    print(f"✅ Generated {len(df):,} records")
    print(f"📁 Saved to: {OUTPUT_PATH}")
    print(f"\n📈 Dataset Statistics:")
    print(f"  - Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
    print(f"  - Parking lots: {df['lot_id'].nunique()}")
    print(f"  - Average occupancy: {df['occupancy_rate'].mean():.2%}")
    print(f"  - Peak occupancy: {df['occupancy_rate'].max():.2%}")
    
    return df

if __name__ == '__main__':
    df = generate_parking_data()
    print("\n🎉 Data generation complete!")
