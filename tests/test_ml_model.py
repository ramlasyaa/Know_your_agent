import pytest
from app.scoring.ml_model import AgentAnomalyModel


def test_ml_model_initialization_and_prediction():
    model = AgentAnomalyModel()
    assert model.model is not None

    # Score normal transaction
    normal_score = model.predict_anomaly_score(
        amount=25.0,
        hour_of_day=14,
        is_new_merchant=False,
        action_type="payment",
        velocity_5m=0,
        velocity_1h=1
    )

    assert 0.0 <= normal_score <= 100.0
    assert normal_score < 45.0  # Normal transactions should have low anomaly score


def test_ml_model_anomalous_prediction():
    model = AgentAnomalyModel()

    # Score extreme anomalous transaction
    anomaly_score = model.predict_anomaly_score(
        amount=5500.0,
        hour_of_day=3,
        is_new_merchant=True,
        action_type="api_transfer",
        velocity_5m=8,
        velocity_1h=15
    )

    assert 0.0 <= anomaly_score <= 100.0
    assert anomaly_score > 50.0  # Extreme anomaly should receive higher score than normal
