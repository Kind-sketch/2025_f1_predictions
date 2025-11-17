"""
Prediction module for F1 race predictions
Generates predictions using trained model and outputs JSON
"""
import pandas as pd
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from sklearn.impute import SimpleImputer
try:
    from model.utils import get_driver_name, get_team
except ImportError:
    # For direct execution
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from model.utils import get_driver_name, get_team


# Required JSON schema for predictions
PREDICTION_SCHEMA = {
    "race": str,
    "year": int,
    "predictions": List[Dict[str, Any]],
    "model_metadata": Dict[str, Any]
}


def validate_prediction_schema(data: Dict[str, Any]) -> bool:
    """
    Validate that prediction data matches required schema
    
    Args:
        data: Prediction data dictionary
    
    Returns:
        True if valid, raises ValueError if invalid
    """
    required_keys = ["race", "year", "predictions", "model_metadata"]
    for key in required_keys:
        if key not in data:
            raise ValueError(f"Missing required key: {key}")
    
    if not isinstance(data["predictions"], list):
        raise ValueError("'predictions' must be a list")
    
    if not isinstance(data["model_metadata"], dict):
        raise ValueError("'model_metadata' must be a dictionary")
    
    # Validate each prediction entry
    required_prediction_keys = ["driver", "predicted_time", "qualifying_time", "team"]
    for i, pred in enumerate(data["predictions"]):
        for key in required_prediction_keys:
            if key not in pred:
                raise ValueError(f"Prediction {i} missing required key: {key}")
    
    return True


def generate_predictions(
    model,
    X: pd.DataFrame,
    qualifying_df: pd.DataFrame,
    feature_names: List[str],
    use_imputation: bool = True
) -> pd.DataFrame:
    """
    Generate predictions using trained model
    
    Args:
        model: Trained GradientBoostingRegressor
        X: Feature matrix
        qualifying_df: Original qualifying DataFrame with driver info
        feature_names: List of feature names used by model
        use_imputation: Whether to use imputation (must match training)
    
    Returns:
        DataFrame with predictions added
    """
    # Prepare features
    available_features = [f for f in feature_names if f in X.columns]
    X_pred = X[available_features].copy()
    
    # Handle missing features
    for feat in feature_names:
        if feat not in X_pred.columns:
            X_pred[feat] = 0.0
    
    X_pred = X_pred[feature_names]  # Ensure correct order
    
    # Impute if needed
    if use_imputation:
        imputer = SimpleImputer(strategy="median")
        X_processed = imputer.fit_transform(X_pred)
    else:
        X_processed = X_pred.fillna(X_pred.median()).values
    
    # Predict
    predictions = model.predict(X_processed)
    
    # Add predictions to DataFrame
    result_df = qualifying_df.copy()
    result_df["PredictedRaceTime (s)"] = predictions
    
    return result_df


def format_predictions_for_json(
    predictions_df: pd.DataFrame,
    race_name: str,
    year: int,
    mae: float,
    features_used: List[str],
    model_type: str = "GradientBoostingRegressor"
) -> Dict[str, Any]:
    """
    Format predictions DataFrame into JSON schema
    
    Args:
        predictions_df: DataFrame with predictions
        race_name: Name of the race
        year: Year of the race
        mae: Model MAE
        features_used: List of features used
        model_type: Type of model used
    
    Returns:
        Dictionary matching required JSON schema
    """
    # Sort by predicted time (fastest first)
    sorted_df = predictions_df.sort_values("PredictedRaceTime (s)").copy()
    
    predictions = []
    for _, row in sorted_df.iterrows():
        driver_code = row.get("DriverCode", row.get("Driver", "UNK"))
        driver_name = get_driver_name(driver_code) or driver_code
        team = row.get("Team") or get_team(driver_code) or "Unknown"
        
        prediction = {
            "driver": driver_name,
            "predicted_time": float(row["PredictedRaceTime (s)"]),
            "qualifying_time": float(row.get("QualifyingTime (s)", 0.0)),
            "team": team
        }
        predictions.append(prediction)
    
    result = {
        "race": race_name,
        "year": year,
        "predictions": predictions,
        "model_metadata": {
            "mae": float(mae),
            "features_used": features_used,
            "model_type": model_type
        }
    }
    
    return result


def save_predictions_json(
    predictions_data: Dict[str, Any],
    output_path: Path
):
    """
    Save predictions to JSON file with schema validation
    
    Args:
        predictions_data: Prediction data dictionary
        output_path: Path to save JSON file
    """
    # Validate schema
    validate_prediction_schema(predictions_data)
    
    # Create directory if needed
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save JSON
    with open(output_path, "w") as f:
        json.dump(predictions_data, f, indent=2)
    
    print(f"✅ Predictions saved to {output_path}")

