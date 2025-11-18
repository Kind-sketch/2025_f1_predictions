#!/usr/bin/env python3
"""
FastAPI backend for F1 Race Predictions
Serves predictions in JSON format for frontend consumption
"""
import json
import os
from pathlib import Path
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any, Optional

app = FastAPI(title="F1 Predictions API", version="1.0.0")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Vite default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Use absolute paths
BASE_DIR = Path(__file__).resolve().parent.parent
PREDICTIONS_DIR = BASE_DIR / "predictions"
RACES_DIR = BASE_DIR / "races"

def list_available_races() -> List[str]:
    """List available races from race JSON files"""
    races = []
    if RACES_DIR.exists():
        for config_file in RACES_DIR.glob("*.json"):
            races.append(config_file.stem)
    return races


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
                        "name": config.get("race_name", config_file.stem.replace("_", " ").title())
                    })
            except Exception as e:
                print(f"Error loading race config {config_file}: {e}")
                # Still include the race even if config is invalid
                races.append({
                    "id": config_file.stem,
                    "name": config_file.stem.replace("_", " ").title()
                })
    return races


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
    # Transform the new schema to match frontend expectations
    predictions = []
    for driver_data in data.get("drivers", []):
        predictions.append({
            "driver": driver_data.get("driver", ""),
            "predicted_race_time": driver_data.get("predicted_time", 0.0),
            "qualifying_time": 0.0,  # Not available in new schema
            "team": driver_data.get("team", "Unknown")
        })
    
    return {
        "race": data.get("race", "Unknown Race"),
        "timestamp": data.get("timestamp", datetime.utcnow().isoformat() + "Z"),
        "features_used": [],  # Not available in new schema
        "predictions": predictions,
        "model": {
            "type": "GradientBoostingRegressor",
            "mae": 0.0
        }
    }


@app.get("/")
def root():
    return {"message": "F1 Predictions API", "version": "1.0.0"}


@app.get("/races")
def get_races():
    """Return list of race IDs"""
    return list_available_races()


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


@app.get("/predict/race/{race_id}")
def predict_race(race_id: str):
    """
    Get predictions for a specific race
    
    Args:
        race_id: Race identifier (e.g., 'australia', 'china', 'japan', 'las_vegas')
    
    Returns:
        JSON prediction data matching the required schema
    """
    # Normalize race_id
    race_id = race_id.lower()
    
    # Validate file existence directly
    race_file = RACES_DIR / f"{race_id}.json"
    if not race_file.exists():
        available_races = list_available_races()
        raise HTTPException(
            status_code=404,
            detail=f"Race '{race_id}' not found. Available races: {available_races}"
        )
    
    # Try to load prediction
    prediction = load_prediction(race_id)
    
    if prediction:
        return prediction
    else:
        # Return error if prediction doesn't exist
        raise HTTPException(
            status_code=404,
            detail=f"Prediction for '{race_id}' not found. Run: python run_prediction.py --race {race_id}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)