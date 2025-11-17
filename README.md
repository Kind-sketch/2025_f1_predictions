# 2025_f1_predictions

# 🏎️ F1 Predictions 2025 - Machine Learning Model

Welcome to the **F1 Predictions 2025** repository! This project uses **machine learning, FastF1 API data, and historical F1 race results** to predict race outcomes for the 2025 Formula 1 season.

## 🚀 Project Overview
This repository contains a **Gradient Boosting Machine Learning model** that predicts race results based on past performance, qualifying times, and other structured F1 data. The model leverages:
- FastF1 API for historical race data
- 2024 race results
- 2025 qualifying session results
- Over the course of the season we will be adding additional data to improve our model as well
- Feature engineering techniques to improve predictions

## 📊 Data Sources
- **FastF1 API**: Fetches lap times, race results, and telemetry data
- **2025 Qualifying Data**: Used for prediction
- **Historical F1 Results**: Processed from FastF1 for training the model

## 🏁 How It Works
1. **Data Collection**: The script pulls relevant F1 data using the FastF1 API.
2. **Preprocessing & Feature Engineering**: Converts lap times, normalizes driver names, and structures race data.
3. **Model Training**: A **Gradient Boosting Regressor** is trained using 2024 race results.
4. **Prediction**: The model predicts race times for 2025 and ranks drivers accordingly.
5. **Evaluation**: Model performance is measured using **Mean Absolute Error (MAE)**.

### Dependencies
- `fastf1`
- `numpy`
- `pandas`
- `scikit-learn`
- `matplotlib`

## 📁 Project Structure

```
2025_f1_predictions/
├── model/              # Unified ML pipeline modules
├── races/              # Race configuration files (JSON)
├── predictions/        # Generated prediction outputs (JSON)
├── api/                # FastAPI backend
├── frontend/           # React frontend
├── run_prediction.py   # CLI tool for generating predictions
└── docs/               # Documentation
```

See `docs/REFACTORING_GUIDE.md` for detailed architecture documentation.

## 🔧 Usage

### Quick Start

1. **Set up environment:**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. **Set environment variables (optional, for weather data):**
```bash
export OPENWEATHER_API_KEY=your_api_key_here
# Or create a .env file
```

3. **Generate predictions:**
```bash
python run_prediction.py --race australia
python run_prediction.py --race china
python run_prediction.py --race japan
```

4. **Run the API backend:**
```bash
python api/main.py
```

5. **Run the frontend:**
```bash
cd frontend
npm install
npm run dev
```

### Old Scripts (Legacy)

The original `prediction1.py` through `prediction8.py` scripts are preserved for reference but are no longer the primary method. See `docs/REFACTORING_GUIDE.md` for migration details.

## 📈 Model Performance
The Mean Absolute Error (MAE) is used to evaluate how well the model predicts race times. Lower MAE values indicate more accurate predictions.

## ✨ Recent Improvements

- ✅ **Unified ML Pipeline**: Single codebase for all races
- ✅ **Configuration-Driven**: Races defined in JSON configs
- ✅ **Standardized JSON Output**: Consistent prediction format
- ✅ **FastAPI Backend**: RESTful API for predictions
- ✅ **React Frontend**: Interactive charts and visualizations
- ✅ **Environment Variables**: Secure API key management
- ✅ **Schema Validation**: Predictions validated before saving

## 📌 Future Improvements
- Add **pit stop strategies** into the model
- Explore **deep learning** models for improved accuracy
- Add more feature engineering options
- @mar_antaya on Instagram and TikTok will update with the latest predictions before every race of the 2025 F1 season

## 📜 License
This project is licensed under the MIT License.


🏎️ **Start predicting F1 races like a data scientist!** 🚀

