"""Hybrid Risk Engine combining Rule Checks, Isolation Forest ML, and SHAP Explainability."""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, Tuple, List
from app.scoring.rules import RuleEngine
from app.scoring.ml_model import AgentAnomalyModel
from app.scoring.shap_explainer import ShapExplainer

logger = logging.getLogger(__name__)


class HybridRiskEngine:
    def __init__(self):
        self.rule_engine = RuleEngine()
        self.ml_model = AgentAnomalyModel()
        self.shap_explainer = ShapExplainer(self.ml_model)

    def evaluate_action(
        self,
        action_type: str,
        amount: float,
        is_new_merchant: bool,
        merchant_name: str,
        timestamp: datetime,
        recent_actions_count_5m: int,
        recent_actions_count_1h: int,
        avg_user_amount: float = 50.0
    ) -> Dict[str, Any]:
        """Perform complete hybrid evaluation: Rules + ML Anomaly + SHAP Explanations."""
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)

        hour_of_day = timestamp.hour

        # 1. Rule-Based Evaluation
        rule_points, triggered_rules = self.rule_engine.evaluate_rules(
            action_type=action_type,
            amount=amount,
            is_new_merchant=is_new_merchant,
            merchant_name=merchant_name,
            timestamp=timestamp,
            recent_actions_count_5m=recent_actions_count_5m,
            recent_actions_count_1h=recent_actions_count_1h,
            avg_user_amount=avg_user_amount
        )

        # 2. ML Isolation Forest Evaluation
        ml_score = self.ml_model.predict_anomaly_score(
            amount=amount,
            hour_of_day=hour_of_day,
            is_new_merchant=is_new_merchant,
            action_type=action_type,
            velocity_5m=recent_actions_count_5m,
            velocity_1h=recent_actions_count_1h
        )

        # 3. SHAP Explainability Evaluation
        shap_explanation = self.shap_explainer.explain_action(
            amount=amount,
            hour_of_day=hour_of_day,
            is_new_merchant=is_new_merchant,
            action_type=action_type,
            velocity_5m=recent_actions_count_5m,
            velocity_1h=recent_actions_count_1h,
            ml_score=ml_score
        )

        # 4. Combined Risk Score Calculation
        # Hard rules anchor the baseline, ML adds nuanced anomaly detection
        combined_score = max(rule_points, (rule_points * 0.45 + ml_score * 0.55))
        final_score = round(min(100.0, max(0.0, combined_score)), 2)

        # Determine Risk Level & Flagged Status
        has_critical_rule = any(r.severity in ["CRITICAL", "HIGH"] for r in triggered_rules)
        flagged = (final_score >= 50.0) or has_critical_rule

        if final_score < 30.0:
            risk_level = "LOW"
        elif final_score < 55.0:
            risk_level = "MEDIUM"
        elif final_score < 80.0:
            risk_level = "HIGH"
        else:
            risk_level = "CRITICAL"

        # Build combined summary reasons
        summary_reasons: List[str] = []

        # Add rule descriptions
        for rule in triggered_rules:
            summary_reasons.append(f"{rule.description} (+{rule.points:.0f} pts)")

        # Add SHAP reasons
        for shap_reason in shap_explanation.get("summary_reasons", []):
            if shap_reason not in summary_reasons and "align with standard" not in shap_reason:
                summary_reasons.append(shap_reason)

        if not summary_reasons:
            summary_reasons.append("Action is within safe parameters and standard agent activity boundaries.")

        # Convert numpy types to native Python types for JSON serializability
        final_score_native = float(final_score)
        flagged_native = bool(flagged)
        ml_score_native = float(ml_score)

        return {
            "risk_score": final_score_native,
            "flagged": flagged_native,
            "risk_level": risk_level,
            "rule_flags": [r.to_dict() for r in triggered_rules],
            "ml_anomaly_score": ml_score_native,
            "shap_explanation": {
                "base_score": float(shap_explanation["base_score"]),
                "shap_values": {k: float(v) for k, v in shap_explanation["shap_values"].items()},
                "feature_impacts": shap_explanation["feature_impacts"],
                "summary_reasons": summary_reasons
            },
            "recommendation": "FLAG_FOR_HUMAN_REVIEW" if flagged_native else "ALLOW",
            "decision_reason": f"Risk Score: {final_score_native:.1f}/100 ({risk_level}). " + "; ".join(summary_reasons[:3])
        }
