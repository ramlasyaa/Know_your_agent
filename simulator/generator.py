"""Synthetic AI Agent Action Generator with Anomaly Injection."""

import random
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List

KNOWN_MERCHANTS = [
    "Amazon", "DoorDash", "Uber Eats", "Instacart", "Netflix",
    "Spotify", "Target", "Walmart", "AWS Cloud Services", "OpenAI API",
    "GitHub Enterprise", "Vercel Hosting", "Stripe Checkout"
]

SUSPICIOUS_MERCHANTS = [
    "CryptoExchange-Anonymous", "Unverified-P2P-Transfer",
    "OffshorePayee-Global-Limited", "FlashDeals-Luxury-Direct",
    "Unknown-Telegram-Bot-Store", "DarkWeb-Digital-Keys"
]

ACTION_TYPES = ["payment", "order_checkout", "subscription", "api_transfer"]

AGENT_IDS = ["agent_shopping_bot_01", "agent_travel_planner_02", "agent_saas_billing_03", "agent_procurement_04"]
USER_IDS = ["usr_alex_789", "usr_sarah_456", "usr_michael_123", "usr_emily_321"]


class AgentActionGenerator:
    def __init__(self, anomaly_rate: float = 0.15):
        """
        :param anomaly_rate: Percentage of generated events that should contain injected anomalies (0.0 to 1.0)
        """
        self.anomaly_rate = min(1.0, max(0.0, anomaly_rate))

    def generate_single_action(self, is_anomaly: bool = False, force_type: str = None) -> Dict[str, Any]:
        """Generate a single realistic agent action dictionary."""
        agent_id = random.choice(AGENT_IDS)
        user_id = random.choice(USER_IDS)
        now = datetime.now(timezone.utc)

        if not is_anomaly:
            # Normal Agent Behavior Pattern
            action_type = random.choice(["payment", "order_checkout", "subscription"])
            amount = round(random.expovariate(1.0 / 30.0) + 8.0, 2)
            amount = min(amount, 350.0)
            merchant = random.choice(KNOWN_MERCHANTS)
            is_new = random.random() < 0.10  # 10% chance of standard new merchant
            timestamp = now - timedelta(seconds=random.randint(0, 300))

            return {
                "agent_id": agent_id,
                "user_id": user_id,
                "action_type": action_type,
                "amount": amount,
                "currency": "USD",
                "merchant_name": merchant,
                "is_new_merchant": is_new,
                "timestamp": timestamp.isoformat(),
                "ip_address": f"192.168.1.{random.randint(10, 250)}",
                "device_id": f"device_{agent_id}",
                "metadata": {"simulation_type": "NORMAL", "intent": "routine_user_purchase"}
            }

        # Anomalous Agent Behavior Patterns
        anomaly_kind = force_type or random.choice([
            "UNUSUAL_AMOUNT",
            "UNVERIFIED_MERCHANT",
            "ODD_TIMING",
            "HIGH_VALUE_SUBSCRIPTION"
        ])

        if anomaly_kind == "UNUSUAL_AMOUNT":
            amount = round(random.uniform(1200.00, 7500.00), 2)
            merchant = random.choice(KNOWN_MERCHANTS)
            is_new = False
            action_type = "payment"

        elif anomaly_kind == "UNVERIFIED_MERCHANT":
            amount = round(random.uniform(450.00, 2800.00), 2)
            merchant = random.choice(SUSPICIOUS_MERCHANTS)
            is_new = True
            action_type = "api_transfer"

        elif anomaly_kind == "ODD_TIMING":
            amount = round(random.uniform(150.00, 950.00), 2)
            merchant = random.choice(KNOWN_MERCHANTS + SUSPICIOUS_MERCHANTS)
            is_new = True
            # Set time between 2 AM and 4 AM UTC
            timestamp = now.replace(hour=3, minute=random.randint(10, 50))
            action_type = "order_checkout"

            return {
                "agent_id": agent_id,
                "user_id": user_id,
                "action_type": action_type,
                "amount": amount,
                "currency": "USD",
                "merchant_name": merchant,
                "is_new_merchant": is_new,
                "timestamp": timestamp.isoformat(),
                "ip_address": f"10.0.0.{random.randint(1, 100)}",
                "device_id": f"device_{agent_id}",
                "metadata": {"simulation_type": "ANOMALY", "anomaly_kind": anomaly_kind}
            }

        else:  # HIGH_VALUE_SUBSCRIPTION
            amount = round(random.uniform(999.00, 3999.00), 2)
            merchant = random.choice(SUSPICIOUS_MERCHANTS)
            is_new = True
            action_type = "subscription"

        return {
            "agent_id": agent_id,
            "user_id": user_id,
            "action_type": action_type,
            "amount": amount,
            "currency": "USD",
            "merchant_name": merchant,
            "is_new_merchant": is_new,
            "timestamp": now.isoformat(),
            "ip_address": f"192.168.1.{random.randint(10, 250)}",
            "device_id": f"device_{agent_id}",
            "metadata": {"simulation_type": "ANOMALY", "anomaly_kind": anomaly_kind}
        }

    def generate_burst_anomaly(self, burst_count: int = 6) -> List[Dict[str, Any]]:
        """Generate a rapid burst sequence of actions from a single agent within seconds (velocity spike)."""
        agent_id = "agent_rogue_burst_99"
        user_id = "usr_target_burst_88"
        now = datetime.now(timezone.utc)
        actions = []

        for i in range(burst_count):
            timestamp = now - timedelta(seconds=(burst_count - i) * 8)
            actions.append({
                "agent_id": agent_id,
                "user_id": user_id,
                "action_type": "payment",
                "amount": round(150.0 + (i * 120.0), 2),
                "currency": "USD",
                "merchant_name": "RapidVendor-" + str(i),
                "is_new_merchant": True,
                "timestamp": timestamp.isoformat(),
                "ip_address": "172.16.0.44",
                "device_id": f"device_{agent_id}",
                "metadata": {"simulation_type": "BURST_ANOMALY", "sequence_index": i}
            })
        return actions

    def generate_batch(self, count: int = 50) -> List[Dict[str, Any]]:
        """Generate a batch of actions mixing normal activity and injected anomalies."""
        batch = []
        anomaly_count = int(count * self.anomaly_rate)

        # Generate normal actions
        for _ in range(count - anomaly_count):
            batch.append(self.generate_single_action(is_anomaly=False))

        # Generate standard anomalies
        for _ in range(max(0, anomaly_count - 1)):
            batch.append(self.generate_single_action(is_anomaly=True))

        # Inject 1 burst anomaly sequence
        if anomaly_count > 0:
            batch.extend(self.generate_burst_anomaly(burst_count=5))

        # Shuffle batch
        random.shuffle(batch)
        return batch
