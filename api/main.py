"""
FastAPI backend for F1 Race Predictions
Serves predictions in JSON format for frontend consumption
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any, Optional
import json
import os
from pathlib import Path
from datetime import datetime

app = FastAPI(title="F1 Predictions API", version="1.0.0")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Vite default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Paths
PREDICTIONS_DIR = Path("predictions")
RACES_DIR = Path("races")

# Available races (loaded from race configs)
def get_available_races() -> List[Dict[str, str]]:
    """Load available races from race config files"""
    races = []
    if RACES_DIR.exists():
        for config_file in RACES_DIR.glob("*.json"):
            try:
                with open(config_file, "r") as f:
                    config = json.load(f)
                    races.append({
                        "id": config.get("race_id", config_file.stem),
                        "name": config.get("race_name", config_file.stem.title())
                    })
            except Exception:
                continue
    return races if races else [
        {"id": "australia", "name": "Australian GP 2025"},
        {"id": "china", "name": "Chinese GP 2025"},
        {"id": "japan", "name": "Japanese GP 2025"},
        {"id": "bahrain", "name": "Bahrain GP 2025"},
        {"id": "monaco", "name": "Monaco GP 2025"},
    ]


def load_prediction(race_id: str) -> Optional[Dict[str, Any]]:
    """
    Load prediction from JSON file
    
    Args:
        race_id: Race identifier
    
    Returns:
        Prediction data dictionary or None if not found
    """
    prediction_file = PREDICTIONS_DIR / f"{race_id}.json"
    if prediction_file.exists():
        try:
            with open(prediction_file, "r") as f:
                data = json.load(f)
                # Convert to frontend-compatible format
                return convert_to_frontend_format(data)
        except Exception as e:
            print(f"Error loading prediction: {e}")
            return None
    return None


def convert_to_frontend_format(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert prediction JSON to frontend-compatible format
    Maps from new schema to frontend expected format
    """
    predictions = []
    for pred in data.get("predictions", []):
        predictions.append({
            "driver": pred.get("driver", ""),
            "predicted_race_time": pred.get("predicted_time", 0.0),
            "qualifying_time": pred.get("qualifying_time", 0.0),
            "team": pred.get("team", "Unknown")
        })
    
    model_metadata = data.get("model_metadata", {})
    
    return {
        "race": data.get("race", "Unknown Race"),
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "features_used": model_metadata.get("features_used", []),
        "predictions": predictions,
        "model": {
            "type": model_metadata.get("model_type", "GradientBoostingRegressor"),
            "mae": model_metadata.get("mae", 0.0)
        }
    }


@app.get("/")
def root():
    return {"message": "F1 Predictions API", "version": "1.0.0"}


@app.get("/available-races")
def get_available_races_endpoint():
    """Return list of available races"""
    return {"races": get_available_races()}


@app.get("/drivers")
def get_drivers():
    """Return list of all F1 drivers"""
    drivers = [
        {"code": "VER", "name": "Max Verstappen", "team": "Red Bull"},
        {"code": "NOR", "name": "Lando Norris", "team": "McLaren"},
        {"code": "PIA", "name": "Oscar Piastri", "team": "McLaren"},
        {"code": "LEC", "name": "Charles Leclerc", "team": "Ferrari"},
        {"code": "RUS", "name": "George Russell", "team": "Mercedes"},
        {"code": "HAM", "name": "Lewis Hamilton", "team": "Mercedes"},
        {"code": "SAI", "name": "Carlos Sainz", "team": "Ferrari"},
        {"code": "ALB", "name": "Alexander Albon", "team": "Williams"},
        {"code": "TSU", "name": "Yuki Tsunoda", "team": "Racing Bulls"},
        {"code": "GAS", "name": "Pierre Gasly", "team": "Alpine"},
        {"code": "OCO", "name": "Esteban Ocon", "team": "Alpine"},
        {"code": "ALO", "name": "Fernando Alonso", "team": "Aston Martin"},
        {"code": "STR", "name": "Lance Stroll", "team": "Aston Martin"},
        {"code": "HUL", "name": "Nico Hülkenberg", "team": "Kick Sauber"},
    ]
    return {"drivers": drivers}


@app.get("/predict/race/{race_name}")
def predict_race(race_name: str):
    """
    Get predictions for a specific race
    
    Args:
        race_name: Race identifier (e.g., 'australia', 'china', 'japan')
    
    Returns:
        JSON prediction data matching the required schema
    """
    available_races = get_available_races()
    race_ids = [r["id"] for r in available_races]
    
    # Check if race exists
    if race_name not in race_ids:
        raise HTTPException(
            status_code=404,
            detail=f"Race '{race_name}' not found. Available races: {', '.join(race_ids)}"
        )
    
    # Try to load prediction
    prediction = load_prediction(race_name)
    
    if prediction:
        return prediction
    else:
        # Return error if prediction doesn't exist
        raise HTTPException(
            status_code=404,
            detail=f"Prediction for '{race_name}' not found. Run: python run_prediction.py --race {race_name}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

