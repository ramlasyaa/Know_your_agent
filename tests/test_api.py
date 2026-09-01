import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check_endpoint(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "Know Your Agent" in data["service"]


@pytest.mark.asyncio
async def test_score_action_endpoint_clean(client: AsyncClient):
    payload = {
        "agent_id": "test_agent_01",
        "user_id": "test_user_01",
        "action_type": "payment",
        "amount": 35.50,
        "currency": "USD",
        "merchant_name": "Amazon",
        "is_new_merchant": False
    }

    response = await client.post("/score-action", json=payload)
    assert response.status_code == 201

    data = response.json()
    assert "action" in data
    assert "risk_score" in data
    assert data["recommendation"] == "ALLOW"
    assert data["risk_score"]["risk_score"] < 50.0
    assert data["risk_score"]["flagged"] is False
    assert "shap_explanation" in data["risk_score"]


@pytest.mark.asyncio
async def test_score_action_endpoint_flagged_anomaly(client: AsyncClient):
    payload = {
        "agent_id": "test_agent_rogue",
        "user_id": "test_user_victim",
        "action_type": "api_transfer",
        "amount": 4500.00,  # Exceeds hard limit
        "currency": "USD",
        "merchant_name": "CryptoExchange-Unknown",
        "is_new_merchant": True
    }

    response = await client.post("/score-action", json=payload)
    assert response.status_code == 201

    data = response.json()
    assert data["recommendation"] == "FLAG_FOR_HUMAN_REVIEW"
    assert data["risk_score"]["flagged"] is True
    assert data["risk_score"]["risk_score"] >= 50.0
    assert len(data["risk_score"]["rule_flags"]) > 0


@pytest.mark.asyncio
async def test_list_actions_endpoint(client: AsyncClient):
    # Post one action first
    payload = {
        "agent_id": "test_agent_list",
        "user_id": "test_user_list",
        "action_type": "payment",
        "amount": 20.00,
        "merchant_name": "Spotify",
        "is_new_merchant": False
    }
    await client.post("/score-action", json=payload)

    response = await client.get("/actions")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert "action" in data[0]
    assert "risk_score" in data[0]


@pytest.mark.asyncio
async def test_audit_endpoint(client: AsyncClient):
    payload = {
        "agent_id": "test_agent_audit",
        "user_id": "test_user_audit",
        "action_type": "order_checkout",
        "amount": 120.00,
        "merchant_name": "Target",
        "is_new_merchant": False
    }
    res_post = await client.post("/score-action", json=payload)
    action_id = res_post.json()["action"]["id"]

    res_audit = await client.get(f"/audit/{action_id}")
    assert res_audit.status_code == 200
    data = res_audit.json()
    assert data["action"]["id"] == action_id
    assert "risk_score" in data
    assert len(data["audit_logs"]) >= 1


@pytest.mark.asyncio
async def test_stats_endpoint(client: AsyncClient):
    response = await client.get("/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_actions" in data
    assert "flagged_actions" in data
    assert "clean_actions" in data
    assert "flag_rate_percentage" in data
