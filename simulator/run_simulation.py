"""CLI runner for streaming or seeding synthetic agent actions to FastAPI / Database."""

import argparse
import time
import requests
import json
import logging
from typing import List, Dict, Any
from simulator.generator import AgentActionGenerator

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("simulation_runner")


def run_simulation(api_url: str, count: int, anomaly_rate: float, interval: float):
    generator = AgentActionGenerator(anomaly_rate=anomaly_rate)
    actions = generator.generate_batch(count=count)

    endpoint = f"{api_url.rstrip('/')}/score-action"
    logger.info(f"Starting simulation of {len(actions)} actions...")
    logger.info(f"Target API Endpoint: {endpoint}")
    logger.info(f"Injected Anomaly Rate: {anomaly_rate * 100:.1f}%\n")

    scored_count = 0
    flagged_count = 0

    for i, action in enumerate(actions, 1):
        try:
            response = requests.post(endpoint, json=action, timeout=5.0)
            if response.status_code == 201:
                data = response.json()
                score = data["risk_score"]["risk_score"]
                flagged = data["risk_score"]["flagged"]
                level = data["risk_score"]["risk_level"]
                rec = data["recommendation"]

                scored_count += 1
                if flagged:
                    flagged_count += 1
                    status_str = f"❌ [FLAGGED-{level}]"
                else:
                    status_str = f"✅ [CLEAN-{level}]"

                logger.info(
                    f"Action #{i:02d} | Agent: {action['agent_id'][:12]} | "
                    f"Amount: ${action['amount']:>7.2f} | Merchant: {action['merchant_name'][:18]:<18} | "
                    f"Score: {score:>5.1f}/100 | Result: {status_str}"
                )
            else:
                logger.error(f"Action #{i:02d} failed with status {response.status_code}: {response.text}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to connect to API at {endpoint}: {e}")
            logger.info("Ensure the FastAPI backend is running on http://localhost:8000")
            break

        if interval > 0:
            time.sleep(interval)

    logger.info("\n" + "=" * 65)
    logger.info(f"Simulation Finished. Processed: {scored_count}/{len(actions)} | Flagged: {flagged_count}")
    logger.info("=" * 65)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Know Your Agent - Action Simulator CLI")
    parser.add_argument("--api-url", type=str, default="http://localhost:8000", help="FastAPI backend base URL")
    parser.add_argument("--count", type=int, default=35, help="Number of actions to generate")
    parser.add_argument("--anomaly-rate", type=float, default=0.20, help="Fraction of anomalous actions (0.0 to 1.0)")
    parser.add_argument("--interval", type=float, default=0.15, help="Delay between API posts in seconds")

    args = parser.parse_args()
    run_simulation(
        api_url=args.api_url,
        count=args.count,
        anomaly_rate=args.anomaly_rate,
        interval=args.interval
    )
