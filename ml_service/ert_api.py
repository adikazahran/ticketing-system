# ticketing_system/ml_service/ert_api.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import joblib
import os
import pandas as pd
from typing import Optional # <--- Pastikan ini diimpor untuk Optional

# Path ke model yang sudah terlatih
# Path ini relatif terhadap file ert_api.py
MODEL_PATH = os.path.join(os.path.dirname(__file__), 'data', 'ert_model.pkl')

# Cek apakah model ada saat startup
if not os.path.exists(MODEL_PATH):
    raise RuntimeError(f"Model file not found at {MODEL_PATH}. Please run train_ert_model.py first in ml_service directory.")

# Load model dan preprocessor saat startup aplikasi
try:
    model_assets = joblib.load(MODEL_PATH)
    model = model_assets['model']
    preprocessor = model_assets['preprocessor']
    feature_names = model_assets['features'] # Ambil nama fitur yang digunakan saat pelatihan
    print(f"ML model loaded successfully from {MODEL_PATH}")
except Exception as e:
    raise RuntimeError(f"Failed to load ML model from {MODEL_PATH}: {e}")

# Definisi Pydantic Model untuk input prediksi
class TicketFeatures(BaseModel):
    category: str
    priority: str
    num_comments: int
    is_reopened: bool

    # For Pydantic v2. Field validation ensures correct types from request body
    model_config = {'json_schema_extra': {'example': {
        "category": "Software",
        "priority": "High",
        "num_comments": 5,
        "is_reopened": False
    }}}

# Definisi Pydantic Model untuk output prediksi
class ERTPrediction(BaseModel):
    estimated_resolution_time_hours: float

    model_config = {'json_schema_extra': {'example': {
        "estimated_resolution_time_hours": 24.5
    }}}

# Inisialisasi FastAPI
app = FastAPI(
    title="ERT Prediction API",
    description="API for estimating ticket resolution time.",
    version="1.0.0",
)

# Endpoint untuk kesehatan API
@app.get("/health")
async def health_check():
    return {"status": "ok", "model_loaded": True}

# Endpoint untuk prediksi ERT
@app.post("/predict_ert", response_model=ERTPrediction)
async def predict_ert(features: TicketFeatures):
    """
    Predicts the Estimated Resolution Time (ERT) for a given ticket.
    """
    try:
        # Buat DataFrame dari input Pydantic model
        # Pastikan urutan kolom sesuai dengan yang digunakan saat pelatihan
        # Pydantic v2: features.model_dump()
        input_data_dict = features.model_dump()
        input_data = pd.DataFrame([input_data_dict], columns=feature_names) 
        
        # Preproses input data
        processed_input = preprocessor.transform(input_data)
        
        # Lakukan prediksi
        prediction = model.predict(processed_input)[0] # Ambil hasil prediksi pertama
        
        # Pastikan prediksi tidak negatif (waktu tidak bisa negatif)
        prediction = max(0.01, prediction) 

        return ERTPrediction(estimated_resolution_time_hours=round(prediction, 2))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {e}. Check server logs for more details.")