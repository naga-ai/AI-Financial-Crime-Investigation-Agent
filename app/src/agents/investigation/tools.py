"""Simulated investigation tools for the AML Investigation Agent.

Each tool mirrors a real data source or analytical capability that
Wealthsimple's compliance team would access during an investigation.
In production, these would connect to internal APIs and databases.
"""

from __future__ import annotations

import json
import random
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import numpy as np

from src.cache.manager import cache
from src.config import DATA_DIR, FINTRAC_REPORTING_THRESHOLD_CAD
from src.data.models import (
    AccountType,
    ClientProfile,
    Currency,
    Transaction,
    TransactionMethod,
    TransactionType,
)


# ---------------------------------------------------------------------------
# Data loading (singleton, loaded once)
# ---------------------------------------------------------------------------

_client_map: dict[str, ClientProfile] = {}
_client_txns: dict[str, list[Transaction]] = {}
_txn_map: dict[str, Transaction] = {}
_loaded = False


def _ensure_loaded() -> None:
    global _client_map, _client_txns, _txn_map, _loaded
    if _loaded:
        return
    with open(DATA_DIR / "clients.json") as f:
        clients = [ClientProfile(**c) for c in json.load(f)]
    with open(DATA_DIR / "transactions.json") as f:
        txns = [Transaction(**t) for t in json.load(f)]
    _client_map = {c.client_id: c for c in clients}
    _txn_map = {t.transaction_id: t for t in txns}
    for t in txns:
        _client_txns.setdefault(t.client_id, []).append(t)
    for v in _client_txns.values():
        v.sort(key=lambda t: t.timestamp)
    _loaded = True


# ---------------------------------------------------------------------------
# FINTRAC watchlist (simulated)
# ---------------------------------------------------------------------------

SANCTIONS_LIST = [
    {"name": "Viktor Petrov", "type": "sanctions", "source": "OFAC SDN List", "match_score": 0.0},
    {"name": "Al-Qaeda Network", "type": "terrorist_financing", "source": "UN Security Council", "match_score": 0.0},
    {"name": "Iranian Revolutionary Guard", "type": "sanctions", "source": "Canadian Sanctions List", "match_score": 0.0},
]

PEP_DATABASE = [
    {"name": "Various", "type": "PEP", "position": "Member of Parliament", "jurisdiction": "Canada"},
    {"name": "Various", "type": "PEP", "position": "Provincial Minister", "jurisdiction": "Canada"},
    {"name": "Various", "type": "PEP", "position": "Senior Military Officer", "jurisdiction": "International"},
]

KNOWN_TYPOLOGIES = [
    {
        "id": "TYP-001",
        "name": "Structuring / Smurfing",
        "description": "Breaking large amounts into multiple transactions below FINTRAC $10K reporting threshold",
        "indicators": ["multiple_sub_threshold_deposits", "short_time_window", "same_source"],
        "fintrac_ref": "FINTRAC ML Indicator: Structuring of transactions to avoid reporting",
    },
    {
        "id": "TYP-002",
        "name": "Rapid Fund Movement",
        "description": "Large deposits immediately followed by withdrawals or transfers with minimal holding period",
        "indicators": ["large_deposit", "quick_outflow", "different_destination"],
        "fintrac_ref": "FINTRAC ML Indicator: Funds transferred in and out of an account on the same day",
    },
    {
        "id": "TYP-003",
        "name": "Crypto Layering via Privacy Coins",
        "description": "Converting fiat to crypto then swapping to privacy coins (Monero/Zcash) to obscure trail",
        "indicators": ["fiat_to_crypto", "privacy_coin_swap", "external_wallet_withdrawal"],
        "fintrac_ref": "FINTRAC VC Indicator: Exchange to privacy-enhanced cryptocurrency",
    },
    {
        "id": "TYP-004",
        "name": "Round-Trip Wash Trading",
        "description": "Repeated buy-sell cycles of the same asset to create appearance of legitimate trading",
        "indicators": ["same_asset_buy_sell", "minimal_price_difference", "rapid_cycles"],
        "fintrac_ref": "FINTRAC ML Indicator: Transactions that do not appear to have any economic purpose",
    },
    {
        "id": "TYP-005",
        "name": "Dormant Account Activation",
        "description": "Sudden large-value activity on a previously inactive account",
        "indicators": ["long_dormancy", "sudden_large_deposit", "rapid_subsequent_activity"],
        "fintrac_ref": "FINTRAC ML Indicator: Reactivation of a dormant account with significant activity",
    },
    {
        "id": "TYP-006",
        "name": "Third-Party Funnel Account",
        "description": "Account receiving funds from multiple unrelated third parties then consolidating",
        "indicators": ["multiple_incoming_sources", "consolidation_pattern", "unrelated_senders"],
        "fintrac_ref": "FINTRAC ML Indicator: Account used by other individuals or entities",
    },
    {
        "id": "TYP-007",
        "name": "Geographic Risk Pattern",
        "description": "Transactions originating from high-risk jurisdictions or IP addresses",
        "indicators": ["anomalous_ip", "vpn_usage", "cross_border_pattern"],
        "fintrac_ref": "FINTRAC ML Indicator: Transactions involving high-risk jurisdictions",
    },
]


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------

def get_client_profile(client_id: str) -> dict[str, Any]:
    """Pull full KYC data, account history, and risk profile.

    In production: queries client database + KYC verification system.
    """
    _ensure_loaded()

    cached = cache.get("entity_graph", f"profile:{client_id}")
    if cached:
        return cached

    client = _client_map.get(client_id)
    if not client:
        return {"error": f"Client {client_id} not found"}

    result = {
        "client_id": client.client_id,
        "full_name": client.full_name,
        "date_of_birth": client.date_of_birth.strftime("%Y-%m-%d"),
        "email": client.email,
        "occupation": client.occupation,
        "income_range": client.income_range,
        "province": client.province,
        "country": client.country,
        "risk_profile": client.risk_profile.value,
        "kyc_status": client.kyc_status.value,
        "is_pep": client.is_pep,
        "account_open_date": client.account_open_date.strftime("%Y-%m-%d") if client.account_open_date else None,
        "accounts": [
            {
                "account_id": a.account_id,
                "type": a.account_type.value,
                "opened_at": a.opened_at.strftime("%Y-%m-%d"),
                "balance_cad": a.balance_cad,
            }
            for a in client.accounts
        ],
        "total_balance_cad": sum(a.balance_cad for a in client.accounts),
        "num_accounts": len(client.accounts),
    }

    cache.set("entity_graph", f"profile:{client_id}", result)
    return result


def get_transaction_history(client_id: str, days: int = 90) -> list[dict[str, Any]]:
    """Pull transaction history for the specified lookback period.

    In production: queries transaction ledger with pagination.
    """
    _ensure_loaded()
    txns = _client_txns.get(client_id, [])
    cutoff = datetime.now() - timedelta(days=days * 10)  # scale for simulated dates
    recent = [t for t in txns]  # return all for prototype

    return [
        {
            "transaction_id": t.transaction_id,
            "type": t.transaction_type.value,
            "amount_cad": t.amount_cad,
            "currency": t.currency.value,
            "method": t.method.value,
            "counterparty_type": t.counterparty_type.value,
            "account_type": t.account_type.value,
            "timestamp": t.timestamp.isoformat(),
            "ip_address": t.ip_address,
            "description": t.description,
        }
        for t in recent[-200:]  # cap at 200 most recent
    ]


def get_account_summary(client_id: str) -> dict[str, Any]:
    """Summarize account activity, balances, and transaction statistics.

    In production: real-time account balance API + aggregated stats.
    """
    _ensure_loaded()
    txns = _client_txns.get(client_id, [])
    client = _client_map.get(client_id)
    if not client or not txns:
        return {"error": f"No data for client {client_id}"}

    amounts = [t.amount_cad for t in txns]
    deposits = [t for t in txns if t.transaction_type == TransactionType.DEPOSIT]
    withdrawals = [t for t in txns if t.transaction_type in (TransactionType.WITHDRAWAL, TransactionType.TRANSFER_OUT)]

    return {
        "client_id": client_id,
        "total_transactions": len(txns),
        "date_range": {
            "first": txns[0].timestamp.isoformat(),
            "last": txns[-1].timestamp.isoformat(),
        },
        "amount_statistics": {
            "total_volume_cad": round(sum(amounts), 2),
            "average_transaction_cad": round(np.mean(amounts), 2),
            "max_transaction_cad": round(max(amounts), 2),
            "median_transaction_cad": round(float(np.median(amounts)), 2),
        },
        "deposits": {
            "count": len(deposits),
            "total_cad": round(sum(t.amount_cad for t in deposits), 2),
        },
        "withdrawals": {
            "count": len(withdrawals),
            "total_cad": round(sum(t.amount_cad for t in withdrawals), 2),
        },
        "transaction_types": dict(Counter(t.transaction_type.value for t in txns)),
        "methods_used": list(set(t.method.value for t in txns)),
        "currencies_traded": list(set(t.currency.value for t in txns)),
        "accounts": [
            {"type": a.account_type.value, "balance": a.balance_cad}
            for a in client.accounts
        ],
    }


def check_watchlist(client_id: str) -> dict[str, Any]:
    """Screen client against sanctions lists, PEP databases, and adverse media.

    In production: calls Refinitiv World-Check, Dow Jones Risk & Compliance,
    or ComplyAdvantage API.
    """
    _ensure_loaded()

    cache_key = cache.make_key("watchlist", client_id)
    cached = cache.get("watchlist", cache_key)
    if cached:
        return cached

    client = _client_map.get(client_id)
    if not client:
        return {"error": f"Client {client_id} not found", "matches": []}

    matches = []

    if client.is_pep:
        matches.append({
            "type": "PEP",
            "source": "Canadian PEP Database",
            "match_confidence": 0.95,
            "details": f"{client.full_name} identified as Politically Exposed Person",
            "risk_level": "high",
            "action_required": "Enhanced Due Diligence (EDD) required under PCMLTFA",
        })

    if client.kyc_status.value == "flagged":
        matches.append({
            "type": "KYC_FLAG",
            "source": "Internal KYC System",
            "match_confidence": 1.0,
            "details": f"Client KYC verification flagged for review",
            "risk_level": "medium",
            "action_required": "Verify identity documents and source of funds",
        })

    result = {
        "client_id": client_id,
        "client_name": client.full_name,
        "screening_timestamp": datetime.now().isoformat(),
        "lists_checked": [
            "OFAC SDN List", "UN Consolidated Sanctions", "Canadian Sanctions List",
            "Canadian PEP Database", "Adverse Media Screening", "Internal Watchlist",
        ],
        "total_matches": len(matches),
        "matches": matches,
        "risk_assessment": "elevated" if matches else "clear",
    }

    cache.set("watchlist", cache_key, result)
    return result


def analyze_transaction_velocity(client_id: str) -> dict[str, Any]:
    """Compare recent transaction velocity against historical baseline.

    Detects sudden spikes in frequency or volume that deviate from
    the client's established pattern.
    """
    _ensure_loaded()
    txns = _client_txns.get(client_id, [])
    if len(txns) < 10:
        return {"error": "Insufficient transaction history for velocity analysis"}

    daily_counts: dict[str, int] = defaultdict(int)
    daily_volumes: dict[str, float] = defaultdict(float)
    for t in txns:
        day = t.timestamp.strftime("%Y-%m-%d")
        daily_counts[day] += 1
        daily_volumes[day] += t.amount_cad

    days = sorted(daily_counts.keys())
    counts = [daily_counts[d] for d in days]
    volumes = [daily_volumes[d] for d in days]

    baseline_count = np.mean(counts[:-7]) if len(counts) > 7 else np.mean(counts)
    recent_count = np.mean(counts[-7:]) if len(counts) >= 7 else np.mean(counts)
    baseline_volume = np.mean(volumes[:-7]) if len(volumes) > 7 else np.mean(volumes)
    recent_volume = np.mean(volumes[-7:]) if len(volumes) >= 7 else np.mean(volumes)

    count_ratio = recent_count / max(baseline_count, 0.1)
    volume_ratio = recent_volume / max(baseline_volume, 0.1)

    return {
        "client_id": client_id,
        "analysis_period_days": len(days),
        "baseline": {
            "avg_daily_transactions": round(float(baseline_count), 2),
            "avg_daily_volume_cad": round(float(baseline_volume), 2),
        },
        "recent_7d": {
            "avg_daily_transactions": round(float(recent_count), 2),
            "avg_daily_volume_cad": round(float(recent_volume), 2),
        },
        "velocity_ratios": {
            "transaction_count": round(float(count_ratio), 2),
            "transaction_volume": round(float(volume_ratio), 2),
        },
        "anomaly_detected": count_ratio > 3.0 or volume_ratio > 5.0,
        "anomaly_description": (
            f"Transaction velocity {count_ratio:.1f}x above baseline"
            if count_ratio > 3.0
            else f"Volume {volume_ratio:.1f}x above baseline"
            if volume_ratio > 5.0
            else "Within normal parameters"
        ),
    }


def get_entity_relationships(client_id: str) -> dict[str, Any]:
    """Map connected accounts and entities through shared counterparties.

    Identifies potential layering networks by finding accounts that
    share counterparties, IP addresses, or device fingerprints.
    """
    _ensure_loaded()

    cache_key = cache.make_key("entity", client_id)
    cached = cache.get("entity_graph", cache_key)
    if cached:
        return cached

    txns = _client_txns.get(client_id, [])
    if not txns:
        return {"error": f"No transactions for client {client_id}"}

    ips = set(t.ip_address for t in txns if t.ip_address)
    devices = set(t.device_fingerprint for t in txns if t.device_fingerprint)

    shared_ip_clients = set()
    shared_device_clients = set()
    for other_id, other_txns in _client_txns.items():
        if other_id == client_id:
            continue
        other_ips = set(t.ip_address for t in other_txns if t.ip_address)
        other_devices = set(t.device_fingerprint for t in other_txns if t.device_fingerprint)
        if ips & other_ips:
            shared_ip_clients.add(other_id)
        if devices & other_devices:
            shared_device_clients.add(other_id)

    counterparty_types = Counter(t.counterparty_type.value for t in txns)
    external_transfers = [
        t for t in txns
        if t.transaction_type in (TransactionType.TRANSFER_IN, TransactionType.TRANSFER_OUT)
    ]

    result = {
        "client_id": client_id,
        "network_size": len(shared_ip_clients | shared_device_clients),
        "shared_ip_connections": list(shared_ip_clients)[:10],
        "shared_device_connections": list(shared_device_clients)[:5],
        "counterparty_distribution": dict(counterparty_types),
        "external_transfers": {
            "count": len(external_transfers),
            "total_cad": round(sum(t.amount_cad for t in external_transfers), 2),
            "unique_counterparties": len(set(t.counterparty_type.value for t in external_transfers)),
        },
        "risk_indicators": [],
    }

    if len(shared_ip_clients) > 3:
        result["risk_indicators"].append(
            f"Shares IP addresses with {len(shared_ip_clients)} other clients"
        )
    if len(shared_device_clients) > 0:
        result["risk_indicators"].append(
            f"Shares device fingerprint with {len(shared_device_clients)} other client(s)"
        )
    if len(external_transfers) > 5:
        result["risk_indicators"].append(
            f"High volume of external transfers ({len(external_transfers)})"
        )

    cache.set("entity_graph", cache_key, result)
    return result


def match_typology(client_id: str, alert_type: str) -> list[dict[str, Any]]:
    """Compare transaction patterns against known ML/TF typologies.

    Cross-references the alert's characteristics with FINTRAC-documented
    money laundering indicators and known patterns.
    """
    _ensure_loaded()
    txns = _client_txns.get(client_id, [])
    matches = []

    typology_map = {
        "structuring": "TYP-001",
        "rapid_movement": "TYP-002",
        "crypto_layering": "TYP-003",
        "round_tripping": "TYP-004",
        "dormant_activation": "TYP-005",
        "third_party_pattern": "TYP-006",
        "geographic_anomaly": "TYP-007",
    }

    primary_typ_id = typology_map.get(alert_type)

    for typ in KNOWN_TYPOLOGIES:
        match_score = 0.0
        matched_indicators = []

        if typ["id"] == primary_typ_id:
            match_score = 0.85
            matched_indicators = typ["indicators"]
        else:
            deposits = [t for t in txns if t.transaction_type == TransactionType.DEPOSIT]
            near_threshold = [d for d in deposits if FINTRAC_REPORTING_THRESHOLD_CAD * 0.8 <= d.amount_cad < FINTRAC_REPORTING_THRESHOLD_CAD]
            if near_threshold and "multiple_sub_threshold_deposits" in typ["indicators"]:
                match_score = max(match_score, 0.4)
                matched_indicators.append("multiple_sub_threshold_deposits")

            privacy = [t for t in txns if t.currency in (Currency.XMR, Currency.ZEC)]
            if privacy and "privacy_coin_swap" in typ["indicators"]:
                match_score = max(match_score, 0.6)
                matched_indicators.append("privacy_coin_swap")

        if match_score >= 0.3:
            matches.append({
                "typology_id": typ["id"],
                "typology_name": typ["name"],
                "match_score": round(match_score, 2),
                "matched_indicators": matched_indicators,
                "description": typ["description"],
                "fintrac_reference": typ["fintrac_ref"],
            })

    matches.sort(key=lambda m: m["match_score"], reverse=True)
    return matches


def get_crypto_flow(client_id: str) -> dict[str, Any]:
    """Analyze crypto-specific transaction patterns.

    Traces fiat-to-crypto conversion paths, privacy coin usage,
    and external wallet interactions -- key FINTRAC virtual currency indicators.
    """
    _ensure_loaded()
    txns = _client_txns.get(client_id, [])
    crypto_txns = [t for t in txns if t.account_type == AccountType.CRYPTO or t.currency not in (Currency.CAD, Currency.USD)]

    if not crypto_txns:
        return {"client_id": client_id, "has_crypto_activity": False, "risk_indicators": []}

    privacy_coins = [t for t in crypto_txns if t.currency in (Currency.XMR, Currency.ZEC)]
    external_withdrawals = [t for t in crypto_txns if t.counterparty_type.value == "external_wallet"]
    swaps = [t for t in crypto_txns if t.transaction_type == TransactionType.CRYPTO_SWAP]

    fiat_deposits_before_crypto = []
    for ct in crypto_txns:
        if ct.transaction_type == TransactionType.BUY:
            deposits = [
                t for t in txns
                if t.transaction_type == TransactionType.DEPOSIT
                and t.currency in (Currency.CAD, Currency.USD)
                and ct.timestamp - timedelta(hours=24) <= t.timestamp <= ct.timestamp
            ]
            fiat_deposits_before_crypto.extend(deposits)

    risk_indicators = []
    if privacy_coins:
        risk_indicators.append(
            f"FINTRAC VC Indicator: {len(privacy_coins)} transaction(s) involving privacy coins "
            f"({', '.join(set(t.currency.value for t in privacy_coins))})"
        )
    if external_withdrawals:
        total_ext = sum(t.amount_cad for t in external_withdrawals)
        risk_indicators.append(
            f"FINTRAC VC Indicator: {len(external_withdrawals)} withdrawal(s) to external wallets "
            f"totaling ${total_ext:,.2f} CAD"
        )
    if swaps and privacy_coins:
        risk_indicators.append(
            "FINTRAC VC Indicator: Crypto swaps to privacy coins detected -- potential layering"
        )
    if fiat_deposits_before_crypto:
        total_fiat = sum(t.amount_cad for t in fiat_deposits_before_crypto)
        risk_indicators.append(
            f"Fiat-to-crypto conversion pattern: ${total_fiat:,.2f} deposited within 24h before crypto purchases"
        )

    return {
        "client_id": client_id,
        "has_crypto_activity": True,
        "total_crypto_transactions": len(crypto_txns),
        "currencies_traded": list(set(t.currency.value for t in crypto_txns)),
        "privacy_coin_transactions": len(privacy_coins),
        "external_wallet_withdrawals": len(external_withdrawals),
        "crypto_swaps": len(swaps),
        "fiat_to_crypto_deposits": len(fiat_deposits_before_crypto),
        "total_crypto_volume_cad": round(sum(t.amount_cad for t in crypto_txns), 2),
        "risk_indicators": risk_indicators,
        "risk_level": "high" if privacy_coins else "medium" if external_withdrawals else "low",
    }


def get_behavioral_baseline(client_id: str) -> dict[str, Any]:
    """Compute the client's 90-day behavioral baseline for deviation analysis.

    Establishes what 'normal' looks like for this client, so deviations
    in the triggered transactions can be quantified.
    """
    _ensure_loaded()

    cache_key = cache.make_key("behavioral", client_id)
    cached = cache.get("behavioral", cache_key)
    if cached:
        return cached

    txns = _client_txns.get(client_id, [])
    if len(txns) < 5:
        return {"error": "Insufficient history for baseline"}

    amounts = [t.amount_cad for t in txns]
    hours = [t.timestamp.hour for t in txns]

    methods = Counter(t.method.value for t in txns)
    types = Counter(t.transaction_type.value for t in txns)

    ips = [t.ip_address for t in txns if t.ip_address]
    ip_prefixes = Counter(ip.rsplit(".", 1)[0] for ip in ips)

    result = {
        "client_id": client_id,
        "baseline_period_transactions": len(txns),
        "amount_baseline": {
            "mean": round(float(np.mean(amounts)), 2),
            "median": round(float(np.median(amounts)), 2),
            "std": round(float(np.std(amounts)), 2),
            "p95": round(float(np.percentile(amounts, 95)), 2),
            "max": round(max(amounts), 2),
        },
        "temporal_baseline": {
            "most_active_hours": [h for h, _ in Counter(hours).most_common(3)],
            "weekend_ratio": round(sum(1 for t in txns if t.timestamp.weekday() >= 5) / max(len(txns), 1), 2),
        },
        "method_baseline": dict(methods.most_common()),
        "type_baseline": dict(types.most_common()),
        "ip_baseline": {
            "unique_prefixes": len(ip_prefixes),
            "primary_prefix": ip_prefixes.most_common(1)[0][0] if ip_prefixes else None,
        },
    }

    cache.set("behavioral", cache_key, result)
    return result
