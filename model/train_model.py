"""
Model training module for F1 predictions
Trains a unified Gradient Boosting Regressor model
"""
import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error
from sklearn.impute import SimpleImputer
from typing import Tuple, List, Optional
import joblib
from pathlib import Path


def train_gradient_boosting_model(
    X: pd.DataFrame,
    y: pd.Series,
    test_size: float = 0.2,
    random_state: int = 42,
    n_estimators: int = 200,
    learning_rate: float = 0.1,
    max_depth: Optional[int] = None,
    use_imputation: bool = True
) -> Tuple[GradientBoostingRegressor, float, List[str]]:
    """
    Train a Gradient Boosting Regressor model
    
    Args:
        X: Feature matrix
        y: Target values (average lap times)
        test_size: Proportion of data for testing
        random_state: Random seed
        n_estimators: Number of boosting stages
        learning_rate: Learning rate
        max_depth: Maximum depth of trees (None for no limit)
        use_imputation: Whether to use SimpleImputer for missing values
    
    Returns:
        Tuple of (trained_model, MAE, feature_names)
    """
    # Handle missing values
    if use_imputation:
        imputer = SimpleImputer(strategy="median")
        X_processed = imputer.fit_transform(X)
        feature_names = list(X.columns)
    else:
        X_processed = X.fillna(X.median()).values
        feature_names = list(X.columns)
    
    # Train-test split
    X_train, X_test, y_train, y_test = train_test_split(
        X_processed, y, test_size=test_size, random_state=random_state
    )
    
    # Train model
    model = GradientBoostingRegressor(
        n_estimators=n_estimators,
        learning_rate=learning_rate,
        max_depth=max_depth,
        random_state=random_state
    )
    model.fit(X_train, y_train)
    
    # Evaluate
    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    
    return model, mae, feature_names


def save_model(model: GradientBoostingRegressor, filepath: Path):
    """Save trained model to disk"""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, filepath)
    print(f"✅ Model saved to {filepath}")


def load_model(filepath: Path) -> GradientBoostingRegressor:
    """Load trained model from disk"""
    return joblib.load(filepath)


def get_feature_importance(model: GradientBoostingRegressor, feature_names: List[str]) -> dict:
    """Get feature importance scores from trained model"""
    importance_dict = dict(zip(feature_names, model.feature_importances_))
    return dict(sorted(importance_dict.items(), key=lambda x: x[1], reverse=True))

