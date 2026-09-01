"""ML Anomaly Scoring Module using Isolation Forest.

Isolation Forest is an unsupervised tree-based algorithm ideal for fraud detection
because it isolates anomalies by randomly selecting a feature and splitting values.
It requires no labeled fraud data to detect novel behavioral outliers.
"""

import os
import logging
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
import joblib

logger = logging.getLogger(__name__)

CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", ".model_cache")
MODEL_PATH = os.path.join(CACHE_DIR, "isolation_forest.joblib")

FEATURE_NAMES = [
    "amount",
    "hour_of_day",
    "is_new_merchant",
    "action_type_code",
    "velocity_5m",
    "velocity_1h"
]

ACTION_TYPE_MAP = {
    "payment": 0.0,
    "order_checkout": 1.0,
    "subscription": 2.0,
    "api_transfer": 3.0
}


class AgentAnomalyModel:
    def __init__(self):
        self.model: IsolationForest = None
        self.feature_names = FEATURE_NAMES
        self._load_or_train_model()

    def _extract_features(
        self,
        amount: float,
        hour_of_day: int,
        is_new_merchant: bool,
        action_type: str,
        velocity_5m: int,
        velocity_1h: int
    ) -> pd.DataFrame:
        """Convert input parameters into a structured DataFrame with named features."""
        action_code = ACTION_TYPE_MAP.get(action_type.lower(), 0.0)
        data = {
            "amount": [float(amount)],
            "hour_of_day": [float(hour_of_day)],
            "is_new_merchant": [1.0 if is_new_merchant else 0.0],
            "action_type_code": [action_code],
            "velocity_5m": [float(velocity_5m)],
            "velocity_1h": [float(velocity_1h)]
        }
        return pd.DataFrame(data, columns=self.feature_names)

    def _generate_synthetic_normal_data(self, n_samples: int = 1200) -> pd.DataFrame:
        """Generate realistic baseline of 'normal' agent payment actions for fitting."""
        np.random.seed(42)

        amounts = np.random.exponential(scale=35.0, size=n_samples) + 5.0
        amounts = np.clip(amounts, 5.0, 250.0)

        raw_p = np.array([
            0.01, 0.01, 0.005, 0.005, 0.01, 0.02, 0.03, 0.05, 0.07, 0.08,
            0.08, 0.08, 0.08, 0.07, 0.07, 0.06, 0.06, 0.05, 0.05, 0.04,
            0.03, 0.02, 0.015, 0.01
        ])
        prob_hours = raw_p / np.sum(raw_p)

        hours = np.random.choice(range(24), size=n_samples, p=prob_hours)

        new_merchants = np.random.choice([0.0, 1.0], size=n_samples, p=[0.85, 0.15])
        action_codes = np.random.choice([0.0, 1.0, 2.0, 3.0], size=n_samples, p=[0.5, 0.3, 0.15, 0.05])
        velocity_5m = np.random.poisson(lam=0.5, size=n_samples)
        velocity_1h = np.random.poisson(lam=1.5, size=n_samples)

        df = pd.DataFrame({
            "amount": amounts,
            "hour_of_day": hours.astype(float),
            "is_new_merchant": new_merchants,
            "action_type_code": action_codes,
            "velocity_5m": velocity_5m.astype(float),
            "velocity_1h": velocity_1h.astype(float)
        })
        return df

    def train_model(self):
        """Train Isolation Forest on normal baseline data."""
        logger.info("Training new Isolation Forest anomaly detection model...")
        normal_df = self._generate_synthetic_normal_data(n_samples=1500)

        model = IsolationForest(
            n_estimators=150,
            contamination=0.05,
            random_state=42,
            bootstrap=False
        )
        model.fit(normal_df)

        os.makedirs(CACHE_DIR, exist_ok=True)
        joblib.dump(model, MODEL_PATH)
        self.model = model
        logger.info(f"Isolation Forest model trained and saved to {MODEL_PATH}")

    def _load_or_train_model(self):
        """Load cached model if exists, otherwise train a new model."""
        if os.path.exists(MODEL_PATH):
            try:
                self.model = joblib.load(MODEL_PATH)
                logger.info(f"Loaded existing Isolation Forest model from {MODEL_PATH}")
            except Exception as e:
                logger.warning(f"Failed to load cached model ({e}). Re-training...")
                self.train_model()
        else:
            self.train_model()

    def predict_anomaly_score(
        self,
        amount: float,
        hour_of_day: int,
        is_new_merchant: bool,
        action_type: str,
        velocity_5m: int,
        velocity_1h: int
    ) -> float:
        """Score action anomaly on a scale of 0.0 (very normal) to 100.0 (highly anomalous)."""
        df = self._extract_features(
            amount, hour_of_day, is_new_merchant, action_type, velocity_5m, velocity_1h
        )

        # score_samples returns opposite of anomaly score (higher = normal, lower = anomaly)
        # Typical range: +0.15 (normal) to -0.6 (anomalous)
        raw_score = self.model.score_samples(df)[0]

        # Convert to 0 - 100 scale where higher = more anomalous
        # Normal: raw_score > 0.0 -> score <= 30
        # Anomaly: raw_score < -0.15 -> score >= 65
        anomaly_score = (0.08 - raw_score) * 85.0
        normalized_score = max(0.0, min(100.0, anomaly_score))

        return round(normalized_score, 2)
