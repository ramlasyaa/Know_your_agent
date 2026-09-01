import pytest
from datetime import datetime, timezone
from app.scoring.rules import RuleEngine


def test_rule_engine_clean_action():
    engine = RuleEngine()
    now = datetime(2026, 9, 1, 14, 0, 0, tzinfo=timezone.utc)  # 2 PM (normal hour)

    points, rules = engine.evaluate_rules(
        action_type="payment",
        amount=45.00,
        is_new_merchant=False,
        merchant_name="Amazon",
        timestamp=now,
        recent_actions_count_5m=1,
        recent_actions_count_1h=2,
        avg_user_amount=50.0
    )

    assert points == 0.0
    assert len(rules) == 0


def test_rule_engine_hard_amount_limit():
    engine = RuleEngine()
    now = datetime(2026, 9, 1, 14, 0, 0, tzinfo=timezone.utc)

    points, rules = engine.evaluate_rules(
        action_type="payment",
        amount=1500.00,  # Exceeds $1000 hard limit
        is_new_merchant=False,
        merchant_name="Target",
        timestamp=now,
        recent_actions_count_5m=0,
        recent_actions_count_1h=1,
        avg_user_amount=50.0
    )

    assert points >= 45.0
    assert any(r.rule_name == "HARD_AMOUNT_EXCEEDED" for r in rules)


def test_rule_engine_velocity_spike():
    engine = RuleEngine()
    now = datetime(2026, 9, 1, 14, 0, 0, tzinfo=timezone.utc)

    points, rules = engine.evaluate_rules(
        action_type="payment",
        amount=30.00,
        is_new_merchant=False,
        merchant_name="DoorDash",
        timestamp=now,
        recent_actions_count_5m=6,  # Exceeds 5 actions limit
        recent_actions_count_1h=10,
        avg_user_amount=40.0
    )

    assert points >= 40.0
    assert any(r.rule_name == "HIGH_VELOCITY_SPIKE" for r in rules)


def test_rule_engine_new_merchant_and_off_hours():
    engine = RuleEngine()
    off_hours = datetime(2026, 9, 1, 3, 0, 0, tzinfo=timezone.utc)  # 3 AM

    points, rules = engine.evaluate_rules(
        action_type="api_transfer",
        amount=120.00,
        is_new_merchant=True,
        merchant_name="UnknownPayeeXYZ",
        timestamp=off_hours,
        recent_actions_count_5m=1,
        recent_actions_count_1h=1,
        avg_user_amount=50.0
    )

    assert points >= 40.0  # 25 (new merchant) + 15 (off hours)
    rule_names = [r.rule_name for r in rules]
    assert "UNVERIFIED_NEW_MERCHANT" in rule_names
    assert "OFF_HOURS_ACTIVITY" in rule_names
