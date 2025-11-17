# F1 Predictions Refactoring Guide

## Overview

This project has been refactored from multiple standalone prediction scripts into a unified, modular ML pipeline system.

## New Structure

```
2025_f1_predictions/
├── model/                    # Unified ML pipeline
│   ├── __init__.py
│   ├── utils.py             # Driver mappings, team data, constants
│   ├── collect_data.py      # FastF1 data loading
│   ├── weather.py            # Weather API integration
│   ├── feature_engineering.py # Feature creation
│   ├── train_model.py        # Model training
│   └── predict.py            # Prediction generation & JSON output
│
├── races/                    # Race configuration files
│   ├── australia.json
│   ├── china.json
│   ├── japan.json
│   ├── bahrain.json
│   └── monaco.json
│
├── predictions/             # Generated prediction JSON files
│   └── <race>.json
│
├── api/                     # FastAPI backend
│   └── main.py
│
├── frontend/                 # React frontend
│   └── ...
│
├── run_prediction.py        # CLI tool for generating predictions
└── .env.example            # Environment variables template
```

## Usage

### 1. Set Up Environment Variables

```bash
cp .env.example .env
# Edit .env and add your OpenWeatherMap API key
export OPENWEATHER_API_KEY=your_key_here
```

### 2. Generate Predictions

```bash
# Activate virtual environment
source .venv/bin/activate

# Generate prediction for a race
python run_prediction.py --race australia
python run_prediction.py --race china
python run_prediction.py --race japan
```

This will:
- Load the race configuration from `races/<race>.json`
- Fetch 2024 race data from FastF1
- Get weather forecasts
- Train a model (or use existing)
- Generate predictions
- Save JSON to `predictions/<race>.json`

### 3. Run Backend API

```bash
source .venv/bin/activate
python api/main.py
```

The API will:
- Load available races from `races/` directory
- Serve predictions from `predictions/` directory
- Provide endpoints:
  - `GET /available-races` - List all races
  - `GET /predict/race/{race_id}` - Get predictions for a race
  - `GET /drivers` - List all drivers

### 4. Run Frontend

```bash
cd frontend
npm run dev
```

The frontend will fetch predictions from the backend API and display charts.

## Race Configuration Format

Each race has a JSON configuration file in `races/`:

```json
{
  "race_id": "australia",
  "race_name": "Australian Grand Prix",
  "year": 2025,
  "training_race": {
    "year": 2024,
    "identifier": 3,
    "type": "R"
  },
  "qualifying_data": [
    {"driver": "Lando Norris", "qualifying_time": 75.096},
    ...
  ],
  "weather": {
    "latitude": -37.8497,
    "longitude": 144.9681,
    "forecast_time": "2025-03-23 15:00:00"
  },
  "features": [
    "QualifyingTime (s)",
    "Sector1Time (s)",
    ...
  ],
  "model_params": {
    "n_estimators": 100,
    "learning_rate": 0.1,
    "random_state": 39
  }
}
```

## JSON Output Schema

All predictions are saved in a standardized JSON format:

```json
{
  "race": "Australian Grand Prix",
  "year": 2025,
  "predictions": [
    {
      "driver": "Lando Norris",
      "predicted_time": 82.67,
      "qualifying_time": 74.123,
      "team": "McLaren"
    },
    ...
  ],
  "model_metadata": {
    "mae": 3.12,
    "features_used": [
      "QualifyingTime",
      "TotalSectorTime",
      ...
    ],
    "model_type": "GradientBoostingRegressor"
  }
}
```

## Adding a New Race

1. Create a new JSON file in `races/` (e.g., `spain.json`)
2. Fill in the configuration:
   - Race details
   - 2024 training race identifier
   - 2025 qualifying times
   - Weather location
   - Feature list
   - Model parameters
3. Run: `python run_prediction.py --race spain`

## Features Supported

The unified pipeline supports these features:
- `QualifyingTime (s)` - Qualifying lap time
- `Sector1Time (s)`, `Sector2Time (s)`, `Sector3Time (s)` - Sector times
- `TotalSectorTime (s)` - Sum of all sectors
- `CleanAirRacePace (s)` - Clean air race pace
- `WetPerformanceFactor` - Driver wet weather performance
- `RainProbability` - Weather forecast rain probability
- `Temperature` - Weather forecast temperature
- `TeamPerformanceScore` - Normalized team performance
- `SeasonPoints` - Driver season points (if configured)
- `AveragePositionChange` - Track-specific position change (if configured)

## Migration from Old Scripts

The old `prediction1.py` through `prediction8.py` scripts are preserved but no longer used. They can be:
- Referenced for historical context
- Used to extract qualifying data for new race configs
- Eventually archived or removed

## Key Improvements

1. **Unified Pipeline**: Single codebase for all races
2. **Configuration-Driven**: Races defined in JSON, not code
3. **Standardized Output**: All predictions use the same JSON schema
4. **Modular Design**: Easy to add features or modify behavior
5. **API Integration**: Backend automatically loads predictions
6. **Environment Variables**: API keys managed securely
7. **Schema Validation**: Predictions validated before saving

## Troubleshooting

### "Race config not found"
- Ensure the race JSON file exists in `races/` directory
- Check the race ID matches the filename (without .json)

### "No valid drivers found"
- Verify driver names/codes match those in `model/utils.py`
- Check that drivers exist in the 2024 training race data

### "OpenWeatherMap API key not set"
- Set `OPENWEATHER_API_KEY` environment variable
- Or create `.env` file with the key
- Predictions will use default weather values if key is missing

### "Prediction not found" (API)
- Run `python run_prediction.py --race <race_id>` first
- Check that `predictions/<race_id>.json` exists

