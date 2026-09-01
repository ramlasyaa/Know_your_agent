import pytest
from app.scoring.ml_model import AgentAnomalyModel
from app.scoring.shap_explainer import ShapExplainer


def test_shap_explainer_output_structure():
    ml_model = AgentAnomalyModel()
    explainer = ShapExplainer(ml_model)

    explanation = explainer.explain_action(
        amount=2500.0,
        hour_of_day=3,
        is_new_merchant=True,
        action_type="payment",
        velocity_5m=6,
        velocity_1h=12,
        ml_score=85.0
    )

    assert "base_score" in explanation
    assert "shap_values" in explanation
    assert "feature_impacts" in explanation
    assert "summary_reasons" in explanation

    shap_vals = explanation["shap_values"]
    assert "amount" in shap_vals
    assert "velocity_5m" in shap_vals
    assert "is_new_merchant" in shap_vals

    impacts = explanation["feature_impacts"]
    assert len(impacts) == len(explainer.feature_names)
    assert any(i["feature"] == "amount" for i in impacts)
    assert any(i["feature"] == "velocity_5m" for i in impacts)
