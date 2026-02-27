"""Generate sample dataset for the AML Investigation Agent.

Creates clients, transactions (with injected suspicious patterns), and AML alerts.
Saves everything as JSON files in src/data/sample/.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import DATA_DIR, NUM_CLIENTS, NUM_TRANSACTIONS, SUSPICIOUS_CLIENT_RATIO
from src.data.generators.client_generator import generate_clients
from src.data.generators.transaction_generator import generate_transactions
from src.data.generators.alert_generator import generate_alerts


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Generating {NUM_CLIENTS} clients...")
    clients = generate_clients(n=NUM_CLIENTS, suspicious_ratio=SUSPICIOUS_CLIENT_RATIO)
    print(f"  Created {len(clients)} clients across {len(set(c.province for c in clients))} provinces")
    print(f"  Account types: {dict(sorted({at.value: sum(1 for c in clients for a in c.accounts if a.account_type == at) for at in set(a.account_type for c in clients for a in c.accounts)}.items()))}")

    print(f"\nGenerating ~{NUM_TRANSACTIONS} transactions...")
    transactions, suspicious_map = generate_transactions(
        clients, num_transactions=NUM_TRANSACTIONS, suspicious_ratio=SUSPICIOUS_CLIENT_RATIO,
    )
    print(f"  Created {len(transactions)} transactions")
    suspicious_txns = [t for t in transactions if t.is_suspicious]
    print(f"  Suspicious transactions: {len(suspicious_txns)} ({len(suspicious_txns)/len(transactions)*100:.1f}%)")
    print(f"  Suspicious clients: {len(suspicious_map)}")
    patterns = {}
    for pats in suspicious_map.values():
        for p in pats:
            patterns[p] = patterns.get(p, 0) + 1
    print(f"  Pattern distribution: {dict(sorted(patterns.items()))}")

    print("\nRunning alert detection rules...")
    alerts = generate_alerts(transactions, clients)
    print(f"  Generated {len(alerts)} alerts")
    tp_count = sum(1 for a in alerts if a.is_true_positive)
    print(f"  True positives: {tp_count} ({tp_count/max(len(alerts),1)*100:.1f}%)")
    print(f"  Alert types: {dict(sorted({at.value: sum(1 for a in alerts if a.alert_type == at) for at in set(a.alert_type for a in alerts)}.items()))}")

    print("\nSaving to disk...")
    clients_path = DATA_DIR / "clients.json"
    txns_path = DATA_DIR / "transactions.json"
    alerts_path = DATA_DIR / "alerts.json"
    suspicious_path = DATA_DIR / "suspicious_map.json"

    with open(clients_path, "w") as f:
        json.dump([c.model_dump(mode="json") for c in clients], f, indent=2, default=str)
    print(f"  Saved {len(clients)} clients to {clients_path.name}")

    with open(txns_path, "w") as f:
        json.dump([t.model_dump(mode="json") for t in transactions], f, indent=2, default=str)
    print(f"  Saved {len(transactions)} transactions to {txns_path.name}")

    with open(alerts_path, "w") as f:
        json.dump([a.model_dump(mode="json") for a in alerts], f, indent=2, default=str)
    print(f"  Saved {len(alerts)} alerts to {alerts_path.name}")

    with open(suspicious_path, "w") as f:
        json.dump(suspicious_map, f, indent=2)
    print(f"  Saved suspicious map to {suspicious_path.name}")

    print("\nData generation complete!")
    print(f"Files saved in: {DATA_DIR}")


if __name__ == "__main__":
    main()
