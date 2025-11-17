"""
Data collection module for F1 predictions
Loads FastF1 race session data and processes lap/sector times
"""
import fastf1
import pandas as pd
from typing import Union, Optional
from pathlib import Path

# Enable FastF1 caching
CACHE_DIR = Path("f1_cache")
fastf1.Cache.enable_cache(str(CACHE_DIR))


def load_race_session(
    year: int,
    race_identifier: Union[int, str],
    session_type: str = "R"
) -> fastf1.core.Session:
    """
    Load a FastF1 race session
    
    Args:
        year: Race year (e.g., 2024)
        race_identifier: Race identifier (round number or name like "Australia", "China")
        session_type: Session type ("R" for race, "Q" for qualifying)
    
    Returns:
        FastF1 session object
    """
    session = fastf1.get_session(year, race_identifier, session_type)
    session.load()
    return session


def extract_lap_times(
    session: fastf1.core.Session,
    include_sectors: bool = True
) -> pd.DataFrame:
    """
    Extract lap times and optionally sector times from a session
    
    Args:
        session: FastF1 session object
        include_sectors: Whether to include sector times
    
    Returns:
        DataFrame with lap times and optionally sector times
    """
    if include_sectors:
        columns = ["Driver", "LapTime", "Sector1Time", "Sector2Time", "Sector3Time"]
    else:
        columns = ["Driver", "LapTime"]
    
    laps = session.laps[columns].copy()
    laps.dropna(inplace=True)
    
    # Convert timedelta to seconds
    for col in ["LapTime", "Sector1Time", "Sector2Time", "Sector3Time"]:
        if col in laps.columns:
            laps[f"{col} (s)"] = laps[col].dt.total_seconds()
    
    return laps


def get_average_sector_times(laps_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate average sector times per driver
    
    Args:
        laps_df: DataFrame with lap and sector times
    
    Returns:
        DataFrame with average sector times per driver
    """
    sector_cols = ["Sector1Time (s)", "Sector2Time (s)", "Sector3Time (s)"]
    available_cols = [col for col in sector_cols if col in laps_df.columns]
    
    if not available_cols:
        return pd.DataFrame(columns=["Driver"] + sector_cols)
    
    sector_times = laps_df.groupby("Driver")[available_cols].mean().reset_index()
    
    # Calculate total sector time if all sectors are available
    if len(available_cols) == 3:
        sector_times["TotalSectorTime (s)"] = (
            sector_times["Sector1Time (s)"] +
            sector_times["Sector2Time (s)"] +
            sector_times["Sector3Time (s)"]
        )
    
    return sector_times


def get_average_lap_times(laps_df: pd.DataFrame) -> pd.Series:
    """
    Calculate average lap time per driver
    
    Args:
        laps_df: DataFrame with lap times
    
    Returns:
        Series with average lap time per driver
    """
    return laps_df.groupby("Driver")["LapTime (s)"].mean()

