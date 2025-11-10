# api/main.py
from fastapi import FastAPI
from tensorflow.keras.models import load_model
import numpy as np
import pandas as pd
import os

app = FastAPI()

MODEL_PATH = os.path.join(os.path.dirname(__file__), "../models/parking_predictor.h5")
DATA_PATH = os.path.join(os.path.dirname(__file__), "../data/parking_data.csv")

# load model (ensure model exists)
model = load_model(MODEL_PATH)
df = pd.read_csv(DATA_PATH)

@app.get("/current")
def current_status(slot: str = "S1"):
    last = df[df.slot_id == slot].tail(1)
    if last.empty:
        return {"error": "slot not found"}
    return {"slot": slot, "timestamp": last.timestamp.values[0], "status": int(last.status.values[0])}

@app.get("/predict")
def predict(slot: str = "S1"):
    slot_df = df[df.slot_id == slot]["status"].values
    if len(slot_df) < 10:
        return {"error": "not enough data"}
    last_seq = slot_df[-10:]
    X = np.array(last_seq).reshape(1, 10, 1)
    pred_prob = float(model.predict(X)[0][0])
    pred_label = 1 if pred_prob >= 0.5 else 0
    return {"slot": slot, "prediction_prob": pred_prob, "predicted_status": int(pred_label)}
