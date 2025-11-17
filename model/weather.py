"""
Weather data collection module
Fetches weather forecasts from OpenWeatherMap API
"""
import requests
import os
from typing import Dict, Optional, Tuple
from datetime import datetime
try:
    from model.utils import get_openweather_api_key, validate_api_key
except ImportError:
    # For direct execution
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from model.utils import get_openweather_api_key, validate_api_key


def get_weather_forecast(
    latitude: float,
    longitude: float,
    forecast_time: str,
    api_key: Optional[str] = None
) -> Tuple[float, float]:
    """
    Get weather forecast for a specific location and time
    
    Args:
        latitude: Latitude of the location
        longitude: Longitude of the location
        forecast_time: Forecast time in format "YYYY-MM-DD HH:MM:SS"
        api_key: OpenWeatherMap API key (if None, uses environment variable)
    
    Returns:
        Tuple of (rain_probability, temperature)
        Returns (0.0, 20.0) if API call fails or key is missing
    """
    if api_key is None:
        api_key = get_openweather_api_key()
    
    if not api_key or api_key == "YOURAPIKEY":
        print("⚠️  Warning: OpenWeatherMap API key not set. Using default values.")
        return (0.0, 20.0)
    
    try:
        url = (
            f"http://api.openweathermap.org/data/2.5/forecast"
            f"?lat={latitude}&lon={longitude}&appid={api_key}&units=metric"
        )
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        weather_data = response.json()
        
        # Find the forecast closest to the requested time
        forecast_data = None
        for forecast in weather_data.get("list", []):
            if forecast.get("dt_txt") == forecast_time:
                forecast_data = forecast
                break
        
        if forecast_data:
            rain_probability = forecast_data.get("pop", 0.0)
            temperature = forecast_data.get("main", {}).get("temp", 20.0)
            return (rain_probability, temperature)
        else:
            print(f"⚠️  Warning: No forecast found for {forecast_time}. Using default values.")
            return (0.0, 20.0)
    
    except requests.exceptions.RequestException as e:
        print(f"⚠️  Warning: Failed to fetch weather data: {e}. Using default values.")
        return (0.0, 20.0)
    except Exception as e:
        print(f"⚠️  Warning: Error processing weather data: {e}. Using default values.")
        return (0.0, 20.0)


# Race location coordinates (latitude, longitude)
RACE_LOCATIONS: Dict[str, Tuple[float, float]] = {
    "australia": (-37.8497, 144.9681),  # Melbourne
    "china": (31.3389, 121.2206),  # Shanghai
    "japan": (34.8823, 136.5845),  # Suzuka
    "bahrain": (26.0325, 50.5106),  # Sakhir
    "monaco": (43.7384, 7.4246),  # Monte Carlo
    "spain": (41.5700, 2.2611),  # Barcelona
    "canada": (45.5017, -73.5228),  # Montreal
    "austria": (47.2197, 14.7647),  # Spielberg
    "britain": (52.0786, -1.0169),  # Silverstone
    "hungary": (47.5789, 19.2486),  # Budapest
    "belgium": (50.4372, 5.9714),  # Spa-Francorchamps
    "italy": (45.6156, 9.2811),  # Monza
    "singapore": (1.2914, 103.8640),  # Marina Bay
    "usa": (30.1327, -97.6351),  # Austin
    "mexico": (19.4042, -99.0907),  # Mexico City
    "brazil": (-23.7036, -46.6997),  # São Paulo
    "qatar": (25.4901, 51.4542),  # Lusail
    "abu_dhabi": (24.4672, 54.6031),  # Yas Marina
    "las_vegas": (36.1147, -115.1728),  # Las Vegas Strip Circuit
}


def get_race_location(race_name: str) -> Optional[Tuple[float, float]]:
    """Get latitude/longitude for a race location"""
    race_key = race_name.lower().replace(" ", "_")
    return RACE_LOCATIONS.get(race_key)

