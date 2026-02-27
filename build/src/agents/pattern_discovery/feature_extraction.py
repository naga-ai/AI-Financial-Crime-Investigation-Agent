"""Extract features from completed investigations for clustering.

Transforms investigation results into numerical vectors that capture
the key characteristics of each case, enabling unsupervised discovery
of emerging fraud typologies.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from src.data.models import AlertType


ALERT_TYPE_MAP = {t.value: i for i, t in enumerate(AlertType)}

CLUSTER_FEATURE_NAMES = [
    "alert_type_encoded",
    "risk_score",
    "confidence",
    "total_amount",
    "max_amount",
    "txn_count",
    "has_crypto",
    "has_privacy_coin",
    "has_watchlist_hit",
    "network_size",
    "velocity_ratio",
    "has_wire",
    "external_transfer_count",
    "account_age_days",
    "num_accounts",
    "off_hours_ratio",
]


def extract_investigation_features(
    investigation: dict[str, Any],
) -> dict[str, float]:
    """Extract clustering features from a single completed investigation."""
    profile = investigation.get("client_profile", {})
    summary = investigation.get("account_summary", {})
    velocity = investigation.get("velocity_analysis", {})
    watchlist = investigation.get("watchlist_results", {})
    network = investigation.get("entity_network", {})
    crypto = investigation.get("crypto_analysis", {})
    txn_history = investigation.get("transaction_history", [])

    alert_type = investigation.get("alert_type", "")
    amt_stats = summary.get("amount_statistics", {})

    has_crypto = 1.0 if crypto and crypto.get("has_crypto_activity") else 0.0
    has_privacy = 1.0 if crypto and crypto.get("privacy_coin_transactions", 0) > 0 else 0.0
    has_watchlist = 1.0 if watchlist and watchlist.get("total_matches", 0) > 0 else 0.0

    vel = velocity.get("velocity_ratios", {}) if velocity and not velocity.get("error") else {}
    vel_ratio = vel.get("transaction_count", 1.0)

    has_wire = 0.0
    off_hours = 0
    for t in txn_history:
        if t.get("method") == "wire":
            has_wire = 1.0
        hour = 0
        ts = t.get("timestamp", "")
        if "T" in ts:
            try:
                hour = int(ts.split("T")[1][:2])
            except (ValueError, IndexError):
                pass
        if hour < 7 or hour >= 22:
            off_hours += 1

    ext_transfers = network.get("external_transfers", {}).get("count", 0) if network else 0

    from datetime import datetime
    account_open = profile.get("account_open_date", "")
    if account_open:
        try:
            age = (datetime(2026, 2, 25) - datetime.strptime(account_open, "%Y-%m-%d")).days
        except ValueError:
            age = 365
    else:
        age = 365

    return {
        "alert_type_encoded": float(ALERT_TYPE_MAP.get(alert_type, 0)),
        "risk_score": investigation.get("risk_score", 0.0),
        "confidence": investigation.get("confidence", 0.0),
        "total_amount": amt_stats.get("total_volume_cad", 0.0),
        "max_amount": amt_stats.get("max_transaction_cad", 0.0),
        "txn_count": float(len(txn_history)),
        "has_crypto": has_crypto,
        "has_privacy_coin": has_privacy,
        "has_watchlist_hit": has_watchlist,
        "network_size": float(network.get("network_size", 0) if network else 0),
        "velocity_ratio": float(vel_ratio),
        "has_wire": has_wire,
        "external_transfer_count": float(ext_transfers),
        "account_age_days": float(age),
        "num_accounts": float(profile.get("num_accounts", 1)),
        "off_hours_ratio": off_hours / max(len(txn_history), 1),
    }


def build_clustering_dataset(
    investigations: list[dict[str, Any]],
) -> pd.DataFrame:
    """Build feature matrix from a list of completed investigations."""
    rows = []
    for inv in investigations:
        features = extract_investigation_features(inv)
        features["alert_id"] = inv.get("alert_id", "")
        features["client_id"] = inv.get("client_id", "")
        features["recommended_action"] = inv.get("recommended_action", "")
        rows.append(features)

    return pd.DataFrame(rows)
