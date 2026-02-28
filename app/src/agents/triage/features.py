"""Feature engineering for the AML alert triage classifier.

Extracts features that real AML analysts use to prioritize alerts:
transaction velocity, amount patterns, client risk indicators,
counterparty diversity, and temporal anomalies.
"""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

from src.config import DATA_DIR, FINTRAC_REPORTING_THRESHOLD_CAD
from src.data.models import (
    AccountType,
    AlertType,
    AMLAlert,
    ClientProfile,
    Currency,
    Transaction,
    TransactionMethod,
    TransactionType,
)


ALERT_TYPE_ENCODING = {
    AlertType.STRUCTURING: 0,
    AlertType.RAPID_MOVEMENT: 1,
    AlertType.CRYPTO_LAYERING: 2,
    AlertType.ROUND_TRIPPING: 3,
    AlertType.VELOCITY_SPIKE: 4,
    AlertType.DORMANT_ACTIVATION: 5,
    AlertType.GEOGRAPHIC_ANOMALY: 6,
    AlertType.THIRD_PARTY_PATTERN: 7,
    AlertType.PEP_SANCTIONS_HIT: 8,
    AlertType.AGE_AMOUNT_MISMATCH: 9,
}

FEATURE_NAMES = [
    "alert_type_encoded",
    "severity_score",
    "triggered_txn_count",
    "total_amount",
    "max_single_amount",
    "mean_amount",
    "std_amount",
    "amount_near_threshold_ratio",
    "txn_time_span_hours",
    "unique_methods",
    "unique_counterparties",
    "has_wire",
    "has_crypto",
    "has_privacy_coin",
    "crypto_txn_ratio",
    "deposit_withdrawal_ratio",
    "client_risk_encoded",
    "client_account_age_days",
    "client_num_accounts",
    "client_has_crypto_account",
    "client_is_pep",
    "client_kyc_flagged",
    "velocity_ratio_7d",
    "velocity_ratio_30d",
    "amount_to_income_ratio",
    "off_hours_txn_ratio",
    "unique_ip_count",
    "anomalous_ip_ratio",
]


def _load_data() -> tuple[list[ClientProfile], list[Transaction], list[AMLAlert]]:
    with open(DATA_DIR / "clients.json") as f:
        clients = [ClientProfile(**c) for c in json.load(f)]
    with open(DATA_DIR / "transactions.json") as f:
        transactions = [Transaction(**t) for t in json.load(f)]
    with open(DATA_DIR / "alerts.json") as f:
        alerts = [AMLAlert(**a) for a in json.load(f)]
    return clients, transactions, alerts


def _build_indices(
    clients: list[ClientProfile],
    transactions: list[Transaction],
) -> tuple[dict[str, ClientProfile], dict[str, list[Transaction]], dict[str, Transaction]]:
    client_map = {c.client_id: c for c in clients}
    client_txns: dict[str, list[Transaction]] = defaultdict(list)
    txn_map: dict[str, Transaction] = {}
    for t in transactions:
        client_txns[t.client_id].append(t)
        txn_map[t.transaction_id] = t
    for txns in client_txns.values():
        txns.sort(key=lambda t: t.timestamp)
    return client_map, client_txns, txn_map


def _income_midpoint(income_range: str) -> float:
    mapping = {
        "0-25k": 12_500, "25k-50k": 37_500, "50k-75k": 62_500,
        "75k-100k": 87_500, "100k-150k": 125_000, "150k-200k": 175_000,
        "200k-300k": 250_000, "300k+": 400_000,
    }
    return mapping.get(income_range, 62_500)


ANOMALOUS_IP_PREFIXES = {"185.", "91.", "45.", "103.", "193."}


def extract_features_for_alert(
    alert: AMLAlert,
    client_map: dict[str, ClientProfile],
    client_txns: dict[str, list[Transaction]],
    txn_map: dict[str, Transaction],
) -> dict[str, float]:
    """Extract a feature vector for a single alert.

    Combines alert-level, transaction-level, and client-level signals
    that an AML analyst would consider when triaging.
    """
    triggered = [txn_map[tid] for tid in alert.triggered_transactions if tid in txn_map]
    client = client_map.get(alert.client_id)
    all_client_txns = client_txns.get(alert.client_id, [])

    # --- Alert-level features ---
    alert_type_enc = ALERT_TYPE_ENCODING.get(alert.alert_type, -1)

    # --- Transaction-level features ---
    amounts = [t.amount_cad for t in triggered] if triggered else [0]
    total_amount = sum(amounts)
    max_amount = max(amounts)
    mean_amount = np.mean(amounts)
    std_amount = float(np.std(amounts)) if len(amounts) > 1 else 0.0

    threshold = FINTRAC_REPORTING_THRESHOLD_CAD
    near_threshold = sum(1 for a in amounts if threshold * 0.80 <= a < threshold)
    near_threshold_ratio = near_threshold / max(len(amounts), 1)

    if len(triggered) >= 2:
        timestamps = sorted(t.timestamp for t in triggered)
        time_span_hours = (timestamps[-1] - timestamps[0]).total_seconds() / 3600
    else:
        time_span_hours = 0.0

    methods = set(t.method for t in triggered)
    counterparties = set(t.counterparty_type for t in triggered)
    has_wire = 1.0 if TransactionMethod.WIRE in methods else 0.0
    has_crypto = 1.0 if any(
        t.currency in (Currency.BTC, Currency.ETH, Currency.SOL, Currency.USDT, Currency.USDC)
        for t in triggered
    ) else 0.0
    has_privacy_coin = 1.0 if any(
        t.currency in (Currency.XMR, Currency.ZEC) for t in triggered
    ) else 0.0

    crypto_txn_count = sum(1 for t in triggered if t.account_type == AccountType.CRYPTO)
    crypto_ratio = crypto_txn_count / max(len(triggered), 1)

    deposits = sum(1 for t in triggered if t.transaction_type == TransactionType.DEPOSIT)
    withdrawals = sum(1 for t in triggered if t.transaction_type in (
        TransactionType.WITHDRAWAL, TransactionType.TRANSFER_OUT,
    ))
    dw_ratio = deposits / max(withdrawals, 1)

    # --- Client-level features ---
    risk_enc = {"low": 0, "medium": 1, "high": 2}.get(
        client.risk_profile.value if client else "low", 0
    )
    if client and client.account_open_date:
        account_age = (datetime(2026, 2, 25) - client.account_open_date).days
    else:
        account_age = 365
    num_accounts = len(client.accounts) if client else 1
    has_crypto_acct = 1.0 if client and any(
        a.account_type == AccountType.CRYPTO for a in client.accounts
    ) else 0.0
    is_pep = 1.0 if client and client.is_pep else 0.0
    kyc_flagged = 1.0 if client and client.kyc_status.value == "flagged" else 0.0

    # --- Velocity features (vs historical baseline) ---
    if all_client_txns and triggered:
        alert_date = alert.created_at
        txns_7d = [t for t in all_client_txns if alert_date - timedelta(days=7) <= t.timestamp <= alert_date]
        txns_30d = [t for t in all_client_txns if alert_date - timedelta(days=30) <= t.timestamp <= alert_date]
        txns_90d = [t for t in all_client_txns if alert_date - timedelta(days=90) <= t.timestamp <= alert_date]

        avg_daily_90d = len(txns_90d) / 90 if txns_90d else 0.5
        velocity_7d = (len(txns_7d) / 7) / max(avg_daily_90d, 0.1)
        velocity_30d = (len(txns_30d) / 30) / max(avg_daily_90d, 0.1)
    else:
        velocity_7d = 1.0
        velocity_30d = 1.0

    # --- Amount vs income ---
    income = _income_midpoint(client.income_range) if client else 62_500
    amount_income_ratio = max_amount / max(income, 1)

    # --- Temporal: off-hours transactions (before 7am or after 10pm) ---
    off_hours = sum(1 for t in triggered if t.timestamp.hour < 7 or t.timestamp.hour >= 22)
    off_hours_ratio = off_hours / max(len(triggered), 1)

    # --- IP diversity ---
    ips = set(t.ip_address for t in triggered if t.ip_address)
    anomalous_ips = sum(1 for ip in ips if any(ip.startswith(p) for p in ANOMALOUS_IP_PREFIXES))
    anomalous_ip_ratio = anomalous_ips / max(len(ips), 1)

    return {
        "alert_type_encoded": float(alert_type_enc),
        "severity_score": alert.severity_score,
        "triggered_txn_count": float(len(triggered)),
        "total_amount": total_amount,
        "max_single_amount": max_amount,
        "mean_amount": float(mean_amount),
        "std_amount": std_amount,
        "amount_near_threshold_ratio": near_threshold_ratio,
        "txn_time_span_hours": time_span_hours,
        "unique_methods": float(len(methods)),
        "unique_counterparties": float(len(counterparties)),
        "has_wire": has_wire,
        "has_crypto": has_crypto,
        "has_privacy_coin": has_privacy_coin,
        "crypto_txn_ratio": crypto_ratio,
        "deposit_withdrawal_ratio": dw_ratio,
        "client_risk_encoded": float(risk_enc),
        "client_account_age_days": float(account_age),
        "client_num_accounts": float(num_accounts),
        "client_has_crypto_account": has_crypto_acct,
        "client_is_pep": is_pep,
        "client_kyc_flagged": kyc_flagged,
        "velocity_ratio_7d": velocity_7d,
        "velocity_ratio_30d": velocity_30d,
        "amount_to_income_ratio": amount_income_ratio,
        "off_hours_txn_ratio": off_hours_ratio,
        "unique_ip_count": float(len(ips)),
        "anomalous_ip_ratio": anomalous_ip_ratio,
    }


def build_training_dataset() -> pd.DataFrame:
    """Load sample data and build the full feature matrix for triage training."""
    clients, transactions, alerts = _load_data()
    client_map, client_txns, txn_map = _build_indices(clients, transactions)

    rows = []
    for alert in alerts:
        features = extract_features_for_alert(alert, client_map, client_txns, txn_map)
        features["is_true_positive"] = 1.0 if alert.is_true_positive else 0.0
        features["alert_id"] = alert.alert_id
        rows.append(features)

    df = pd.DataFrame(rows)
    return df
