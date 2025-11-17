"""
Feature engineering module for F1 predictions
Creates features from qualifying data, historical race data, weather, and driver/team attributes
"""
import pandas as pd
import numpy as np
from typing import List, Optional
try:
    from model.utils import (
        get_driver_code,
        get_team,
        get_wet_performance_factor,
        get_clean_air_race_pace,
        get_team_performance_score,
    )
except ImportError:
    # For direct execution
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from model.utils import (
        get_driver_code,
        get_team,
        get_wet_performance_factor,
        get_clean_air_race_pace,
        get_team_performance_score,
    )


def normalize_driver_names(qualifying_df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize driver names to 3-letter codes
    
    Args:
        qualifying_df: DataFrame with 'Driver' column containing full names or codes
    
    Returns:
        DataFrame with 'DriverCode' column added
    """
    df = qualifying_df.copy()
    
    # Check if drivers are already codes (3 uppercase letters)
    if df["Driver"].str.match(r"^[A-Z]{3}$").all():
        df["DriverCode"] = df["Driver"]
    else:
        # Map full names to codes
        df["DriverCode"] = df["Driver"].map(get_driver_code)
        # If mapping failed, assume it's already a code
        df["DriverCode"] = df["DriverCode"].fillna(df["Driver"])
    
    return df


def add_team_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add team-related features"""
    df = df.copy()
    df["Team"] = df["DriverCode"].map(get_team)
    df["TeamPerformanceScore"] = df["Team"].map(get_team_performance_score).fillna(0.0)
    return df


def add_driver_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add driver-specific features"""
    df = df.copy()
    df["WetPerformanceFactor"] = df["DriverCode"].map(get_wet_performance_factor)
    df["CleanAirRacePace (s)"] = df["DriverCode"].map(get_clean_air_race_pace)
    return df


def add_weather_features(
    df: pd.DataFrame,
    rain_probability: float,
    temperature: float
) -> pd.DataFrame:
    """Add weather-related features"""
    df = df.copy()
    df["RainProbability"] = rain_probability
    df["Temperature"] = temperature
    return df


def add_sector_features(
    df: pd.DataFrame,
    sector_times_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Merge sector time features from historical data
    
    Args:
        df: Main qualifying DataFrame
        sector_times_df: DataFrame with sector times per driver
    
    Returns:
        Merged DataFrame with sector time features
    """
    merged = df.merge(
        sector_times_df,
        left_on="DriverCode",
        right_on="Driver",
        how="left"
    )
    return merged


def create_feature_matrix(
    df: pd.DataFrame,
    feature_list: List[str]
) -> pd.DataFrame:
    """
    Create feature matrix from DataFrame
    
    Args:
        df: DataFrame with all features
        feature_list: List of feature column names to include
    
    Returns:
        DataFrame with selected features, with missing values filled
    """
    available_features = [f for f in feature_list if f in df.columns]
    X = df[available_features].copy()
    
    # Fill missing values with 0 or median
    for col in X.columns:
        if X[col].isna().any():
            if X[col].dtype in [np.float64, np.int64]:
                X[col] = X[col].fillna(X[col].median() if X[col].notna().any() else 0)
            else:
                X[col] = X[col].fillna(0)
    
    return X


def adjust_qualifying_time_for_weather(
    qualifying_time: float,
    rain_probability: float,
    wet_performance_factor: float,
    threshold: float = 0.75
) -> float:
    """
    Adjust qualifying time based on weather conditions
    
    Args:
        qualifying_time: Original qualifying time
        rain_probability: Probability of rain (0-1)
        wet_performance_factor: Driver's wet performance factor
        threshold: Rain probability threshold for adjustment
    
    Returns:
        Adjusted qualifying time
    """
    if rain_probability >= threshold:
        return qualifying_time * wet_performance_factor
    return qualifying_time

