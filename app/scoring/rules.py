"""Rule-Based Fraud Detection Module.

Design Decision Note:
Rule-based checks execute alongside ML scoring to provide deterministic,
instant safeguards against known critical risk patterns (e.g. extreme amounts,
high velocity spikes, unverified merchants). Rules provide hard guarantees
that ML models (which are probabilistic) might miss on rare edge cases.
"""

from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Tuple
from app.config import settings


class RuleCheckResult:
    def __init__(self, rule_name: str, severity: str, points: float, description: str):
        self.rule_name = rule_name
        self.severity = severity  # LOW, MEDIUM, HIGH, CRITICAL
        self.points = points
        self.description = description

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_name": self.rule_name,
            "severity": self.severity,
            "points": self.points,
            "description": self.description
        }


class RuleEngine:
    def __init__(self):
        self.hard_amount_limit = settings.HARD_AMOUNT_LIMIT
        self.max_velocity = settings.MAX_ACTIONS_PER_WINDOW
        self.velocity_window_minutes = settings.VELOCITY_WINDOW_MINUTES

    def evaluate_rules(
        self,
        action_type: str,
        amount: float,
        is_new_merchant: bool,
        merchant_name: str,
        timestamp: datetime,
        recent_actions_count_5m: int,
        recent_actions_count_1h: int,
        avg_user_amount: float = 50.0
    ) -> Tuple[float, List[RuleCheckResult]]:
        """Evaluate all explicit rules and return (rule_risk_points, triggered_rules)."""
        triggered_rules: List[RuleCheckResult] = []
        total_points = 0.0

        # 1. Hard Amount Limit Rule
        if amount > self.hard_amount_limit:
            points = 45.0 if amount < self.hard_amount_limit * 3 else 70.0
            rule = RuleCheckResult(
                rule_name="HARD_AMOUNT_EXCEEDED",
                severity="HIGH" if points < 60 else "CRITICAL",
                points=points,
                description=f"Transaction amount (${amount:.2f}) exceeds configured limit (${self.hard_amount_limit:.2f})"
            )
            triggered_rules.append(rule)
            total_points += points

        # 2. Amount Anomaly relative to user baseline
        elif avg_user_amount > 0 and amount > avg_user_amount * 5.0:
            points = 30.0
            rule = RuleCheckResult(
                rule_name="AMOUNT_SPIKE_VS_BASELINE",
                severity="MEDIUM",
                points=points,
                description=f"Amount (${amount:.2f}) is >5x user average history (${avg_user_amount:.2f})"
            )
            triggered_rules.append(rule)
            total_points += points

        # 3. High Velocity / Burst Rule (Short Window)
        if recent_actions_count_5m >= self.max_velocity:
            points = 40.0
            rule = RuleCheckResult(
                rule_name="HIGH_VELOCITY_SPIKE",
                severity="HIGH",
                points=points,
                description=f"Agent performed {recent_actions_count_5m} actions in last {self.velocity_window_minutes} minutes (Max: {self.max_velocity})"
            )
            triggered_rules.append(rule)
            total_points += points

        # 4. New / Unverified Merchant Rule
        if is_new_merchant:
            points = 25.0
            rule = RuleCheckResult(
                rule_name="UNVERIFIED_NEW_MERCHANT",
                severity="MEDIUM",
                points=points,
                description=f"Action directed to previously unseen merchant '{merchant_name}'"
            )
            triggered_rules.append(rule)
            total_points += points

        # 5. Off-Hours / Odd Timing Rule (e.g. 2 AM - 5 AM UTC)
        hour = timestamp.hour if timestamp else datetime.now(timezone.utc).hour
        if 2 <= hour <= 4:
            points = 15.0
            rule = RuleCheckResult(
                rule_name="OFF_HOURS_ACTIVITY",
                severity="LOW",
                points=points,
                description=f"Action initiated during off-peak hours ({hour:02d}:00 UTC)"
            )
            triggered_rules.append(rule)
            total_points += points

        # Cap total rule points at 90.0
        return min(total_points, 90.0), triggered_rules
