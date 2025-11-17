"""
Utility functions for F1 prediction pipeline
Includes driver mapping, team mapping, and common constants
"""
import os
from typing import Dict, Optional

# Driver name to 3-letter code mapping
DRIVER_MAPPING: Dict[str, str] = {
    "Lando Norris": "NOR",
    "Oscar Piastri": "PIA",
    "Max Verstappen": "VER",
    "George Russell": "RUS",
    "Yuki Tsunoda": "TSU",
    "Alexander Albon": "ALB",
    "Charles Leclerc": "LEC",
    "Lewis Hamilton": "HAM",
    "Pierre Gasly": "GAS",
    "Carlos Sainz": "SAI",
    "Carlos Sainz Jr.": "SAI",
    "Lance Stroll": "STR",
    "Fernando Alonso": "ALO",
    "Esteban Ocon": "OCO",
    "Nico Hülkenberg": "HUL",
    "Isack Hadjar": "HAD",
    "Andrea Kimi Antonelli": "ANT",
    "Oliver Bearman": "BEA",
    "Jack Doohan": "DOO",
    "Gabriel Bortoleto": "BOR",
    "Liam Lawson": "LAW",
}

# Driver code to full name mapping (reverse)
DRIVER_CODE_TO_NAME: Dict[str, str] = {v: k for k, v in DRIVER_MAPPING.items()}

# Driver to team mapping
DRIVER_TO_TEAM: Dict[str, str] = {
    "VER": "Red Bull",
    "NOR": "McLaren",
    "PIA": "McLaren",
    "LEC": "Ferrari",
    "RUS": "Mercedes",
    "HAM": "Mercedes",
    "GAS": "Alpine",
    "ALO": "Aston Martin",
    "TSU": "Racing Bulls",
    "SAI": "Ferrari",
    "HUL": "Kick Sauber",
    "OCO": "Alpine",
    "STR": "Aston Martin",
    "ALB": "Williams",
    "BEA": "Ferrari",
    "DOO": "Alpine",
    "BOR": "Racing Bulls",
    "LAW": "Racing Bulls",
    "HAD": "Red Bull",
    "ANT": "Mercedes",
}

# Wet performance factors (driver-specific)
WET_PERFORMANCE_FACTORS: Dict[str, float] = {
    "VER": 0.975196,
    "HAM": 0.976464,
    "LEC": 0.975862,
    "NOR": 0.978179,
    "ALO": 0.972655,
    "RUS": 0.968678,
    "SAI": 0.978754,
    "TSU": 0.996338,
    "OCO": 0.981810,
    "GAS": 0.978832,
    "STR": 0.979857,
    "PIA": 0.978000,  # Default for missing drivers
    "ALB": 0.980000,
}

# Clean air race pace (from racepace.py)
CLEAN_AIR_RACE_PACE: Dict[str, float] = {
    "VER": 93.191067,
    "HAM": 94.020622,
    "LEC": 93.418667,
    "NOR": 93.428600,
    "ALO": 94.784333,
    "PIA": 93.232111,
    "RUS": 93.833378,
    "SAI": 94.497444,
    "STR": 95.318250,
    "HUL": 95.345455,
    "OCO": 95.682128,
    "GAS": 95.500000,  # Default
    "TSU": 95.400000,
    "ALB": 95.600000,
}

# Team performance scores (normalized)
TEAM_PERFORMANCE_SCORES: Dict[str, float] = {
    "McLaren": 1.0,  # 279 points (max)
    "Mercedes": 0.527,  # 147 points
    "Red Bull": 0.470,  # 131 points
    "Ferrari": 0.409,  # 114 points
    "Williams": 0.183,  # 51 points
    "Haas": 0.072,  # 20 points
    "Aston Martin": 0.050,  # 14 points
    "Racing Bulls": 0.036,  # 10 points
    "Alpine": 0.025,  # 7 points
    "Kick Sauber": 0.022,  # 6 points
}


def get_driver_code(driver_name: str) -> Optional[str]:
    """Convert full driver name to 3-letter code"""
    return DRIVER_MAPPING.get(driver_name)


def get_driver_name(driver_code: str) -> Optional[str]:
    """Convert 3-letter code to full driver name"""
    return DRIVER_CODE_TO_NAME.get(driver_code)


def get_team(driver_code: str) -> Optional[str]:
    """Get team name for a driver code"""
    return DRIVER_TO_TEAM.get(driver_code)


def get_wet_performance_factor(driver_code: str) -> float:
    """Get wet performance factor for a driver"""
    return WET_PERFORMANCE_FACTORS.get(driver_code, 0.98)  # Default 0.98


def get_clean_air_race_pace(driver_code: str) -> Optional[float]:
    """Get clean air race pace for a driver"""
    return CLEAN_AIR_RACE_PACE.get(driver_code)


def get_team_performance_score(team: str) -> float:
    """Get normalized team performance score"""
    return TEAM_PERFORMANCE_SCORES.get(team, 0.0)


def get_openweather_api_key() -> Optional[str]:
    """Get OpenWeatherMap API key from environment variable"""
    return os.getenv("OPENWEATHER_API_KEY")


def validate_api_key() -> bool:
    """Validate that OpenWeatherMap API key is set"""
    key = get_openweather_api_key()
    if not key or key == "YOURAPIKEY":
        return False
    return True

