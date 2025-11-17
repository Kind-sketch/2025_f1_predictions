#!/usr/bin/env python3
"""
CLI tool for generating F1 race predictions
Usage: python run_prediction.py --race <race_id>
"""
import argparse
import json
import sys
from pathlib import Path
import pandas as pd

# Add model directory to path
sys.path.insert(0, str(Path(__file__).parent))

from model.collect_data import (
    load_race_session,
    extract_lap_times,
    get_average_sector_times,
    get_average_lap_times
)
from model.weather import get_weather_forecast
from model.feature_engineering import (
    normalize_driver_names,
    add_team_features,
    add_driver_features,
    add_weather_features,
    add_sector_features,
    create_feature_matrix,
    adjust_qualifying_time_for_weather
)
from model.train_model import train_gradient_boosting_model
from model.predict import (
    generate_predictions,
    format_predictions_for_json,
    save_predictions_json
)


def load_race_config(race_id: str) -> dict:
    """Load race configuration from JSON file"""
    config_path = Path("races") / f"{race_id}.json"
    if not config_path.exists():
        raise FileNotFoundError(f"Race config not found: {config_path}")
    
    with open(config_path, "r") as f:
        return json.load(f)


def prepare_qualifying_data(config: dict) -> pd.DataFrame:
    """Prepare qualifying DataFrame from config"""
    qualifying_list = []
    for entry in config["qualifying_data"]:
        driver = entry["driver"]
        quali_time = entry.get("qualifying_time")
        if quali_time is None:
            continue  # Skip drivers with no qualifying time
        qualifying_list.append({
            "Driver": driver,
            "QualifyingTime (s)": quali_time
        })
    
    return pd.DataFrame(qualifying_list)


def add_custom_features(df: pd.DataFrame, config: dict) -> pd.DataFrame:
    """Add custom features from config (season points, position changes, etc.)"""
    df = df.copy()
    
    # Add season points if available
    if "season_points" in config:
        season_points = config["season_points"]
        df["SeasonPoints"] = df["DriverCode"].map(season_points).fillna(0)
    
    # Add average position change if available
    if "average_position_change" in config:
        pos_change = config["average_position_change"]
        df["AveragePositionChange"] = df["DriverCode"].map(pos_change).fillna(0.0)
    
    return df


def main():
    parser = argparse.ArgumentParser(description="Generate F1 race predictions")
    parser.add_argument(
        "--race",
        type=str,
        required=True,
        help="Race ID (e.g., 'australia', 'china', 'japan')"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="predictions",
        help="Output directory for predictions (default: predictions)"
    )
    parser.add_argument(
        "--train-model",
        action="store_true",
        help="Train a new model (otherwise uses existing or trains per-race)"
    )
    
    args = parser.parse_args()
    
    print(f"🏎️  Generating predictions for {args.race.upper()}")
    print("=" * 60)
    
    # Load race configuration
    try:
        config = load_race_config(args.race)
        print(f"✅ Loaded config for {config['race_name']}")
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    
    # Load training data (2024 race)
    print("\n📊 Loading training data...")
    try:
        training_race = config["training_race"]
        session_2024 = load_race_session(
            training_race["year"],
            training_race["identifier"],
            training_race["type"]
        )
        laps_2024 = extract_lap_times(session_2024, include_sectors=True)
        sector_times_2024 = get_average_sector_times(laps_2024)
        avg_lap_times = get_average_lap_times(laps_2024)
        print(f"✅ Loaded {len(laps_2024)} laps from {training_race['year']} race")
    except Exception as e:
        print(f"❌ Error loading training data: {e}")
        sys.exit(1)
    
    # Prepare 2025 qualifying data
    print("\n🏁 Preparing 2025 qualifying data...")
    qualifying_2025 = prepare_qualifying_data(config)
    qualifying_2025 = normalize_driver_names(qualifying_2025)
    qualifying_2025 = add_team_features(qualifying_2025)
    qualifying_2025 = add_driver_features(qualifying_2025)
    qualifying_2025 = add_custom_features(qualifying_2025, config)
    print(f"✅ Prepared data for {len(qualifying_2025)} drivers")
    
    # Get weather data
    print("\n🌤️  Fetching weather data...")
    weather_config = config.get("weather", {})
    rain_prob, temperature = get_weather_forecast(
        weather_config.get("latitude", 0),
        weather_config.get("longitude", 0),
        weather_config.get("forecast_time", "2025-01-01 12:00:00")
    )
    print(f"✅ Rain probability: {rain_prob:.2%}, Temperature: {temperature:.1f}°C")
    
    # Add weather features
    qualifying_2025 = add_weather_features(qualifying_2025, rain_prob, temperature)
    
    # Adjust qualifying times for weather if needed
    if rain_prob >= 0.75:
        qualifying_2025["QualifyingTime"] = qualifying_2025.apply(
            lambda row: adjust_qualifying_time_for_weather(
                row["QualifyingTime (s)"],
                rain_prob,
                row["WetPerformanceFactor"]
            ),
            axis=1
        )
    else:
        qualifying_2025["QualifyingTime"] = qualifying_2025["QualifyingTime (s)"]
    
    # Merge with sector times
    qualifying_2025 = add_sector_features(qualifying_2025, sector_times_2024)
    
    # Filter to drivers present in training data
    valid_drivers = qualifying_2025["DriverCode"].isin(avg_lap_times.index)
    qualifying_2025 = qualifying_2025[valid_drivers].copy()
    
    if len(qualifying_2025) == 0:
        print("❌ Error: No valid drivers found after merging with training data")
        sys.exit(1)
    
    # Prepare features and target
    print("\n🔧 Engineering features...")
    feature_list = config.get("features", ["QualifyingTime (s)"])
    X = create_feature_matrix(qualifying_2025, feature_list)
    
    # Get target values (average lap times from 2024)
    y = avg_lap_times.reindex(qualifying_2025["DriverCode"]).dropna()
    X = X.loc[y.index]
    qualifying_2025 = qualifying_2025[qualifying_2025["DriverCode"].isin(y.index)]
    
    if len(X) == 0:
        print("❌ Error: No matching drivers between qualifying and training data")
        sys.exit(1)
    
    # Train model
    print("\n🤖 Training model...")
    model_params = config.get("model_params", {})
    model, mae, feature_names = train_gradient_boosting_model(
        X, y,
        random_state=model_params.get("random_state", 42),
        n_estimators=model_params.get("n_estimators", 200),
        learning_rate=model_params.get("learning_rate", 0.1),
        max_depth=model_params.get("max_depth", None)
    )
    print(f"✅ Model trained - MAE: {mae:.2f} seconds")
    
    # Generate predictions
    print("\n🔮 Generating predictions...")
    predictions_df = generate_predictions(
        model, X, qualifying_2025, feature_names
    )
    
    # Format and save JSON
    predictions_json = format_predictions_for_json(
        predictions_df,
        config["race_name"],
        config["year"],
        mae,
        feature_list,
        "GradientBoostingRegressor"
    )
    
    output_path = Path(args.output_dir) / f"{args.race}.json"
    save_predictions_json(predictions_json, output_path)
    
    # Print top 3
    print("\n🏆 Top 3 Predictions:")
    for i, pred in enumerate(predictions_json["predictions"][:3], 1):
        medal = ["🥇", "🥈", "🥉"][i-1]
        print(f"{medal} P{i}: {pred['driver']} - {pred['predicted_time']:.3f}s")
    
    print(f"\n✅ Predictions saved to {output_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()

