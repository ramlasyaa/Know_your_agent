import pytest
from simulator.generator import AgentActionGenerator


def test_generator_single_normal_action():
    gen = AgentActionGenerator(anomaly_rate=0.0)
    action = gen.generate_single_action(is_anomaly=False)

    assert "agent_id" in action
    assert "amount" in action
    assert "merchant_name" in action
    assert action["amount"] > 0
    assert action["metadata"]["simulation_type"] == "NORMAL"


def test_generator_single_anomalous_action():
    gen = AgentActionGenerator(anomaly_rate=1.0)
    action = gen.generate_single_action(is_anomaly=True)

    assert "agent_id" in action
    assert "amount" in action
    assert action["metadata"]["simulation_type"] == "ANOMALY"


def test_generator_batch_creation():
    gen = AgentActionGenerator(anomaly_rate=0.2)
    batch = gen.generate_batch(count=30)

    assert len(batch) >= 30
    normal_count = sum(1 for a in batch if a["metadata"].get("simulation_type") == "NORMAL")
    anomaly_count = sum(1 for a in batch if "ANOMALY" in a["metadata"].get("simulation_type", ""))

    assert normal_count > 0
    assert anomaly_count > 0
