"""Rule engine that generates AML alerts from transaction data.

Implements 10 detection rules modeled on real FINTRAC indicators and
common AML transaction monitoring patterns used by Canadian fintechs.
"""

from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import datetime, timedelta

from src.data.models import (
    AlertStatus,
    AlertType,
    AMLAlert,
    ClientProfile,
    Currency,
    Transaction,
    TransactionMethod,
    TransactionType,
)
from src.config import (
    FINTRAC_REPORTING_THRESHOLD_CAD,
    STRUCTURING_WINDOW_HOURS,
    VELOCITY_SPIKE_MULTIPLIER,
    DORMANT_THRESHOLD_DAYS,
)


def _build_client_txn_index(
    transactions: list[Transaction],
) -> dict[str, list[Transaction]]:
    index: dict[str, list[Transaction]] = defaultdict(list)
    for txn in transactions:
        index[txn.client_id].append(txn)
    for txns in index.values():
        txns.sort(key=lambda t: t.timestamp)
    return index


def _detect_structuring(
    client_id: str, txns: list[Transaction]
) -> list[AMLAlert]:
    """Detect multiple deposits just below $10K within a rolling window."""
    alerts = []
    deposits = [
        t for t in txns
        if t.transaction_type == TransactionType.DEPOSIT
        and FINTRAC_REPORTING_THRESHOLD_CAD * 0.80 <= t.amount_cad < FINTRAC_REPORTING_THRESHOLD_CAD
    ]

    for i, txn in enumerate(deposits):
        window_end = txn.timestamp + timedelta(hours=STRUCTURING_WINDOW_HOURS)
        cluster = [t for t in deposits[i:] if t.timestamp <= window_end]
        if len(cluster) >= 3:
            total = sum(t.amount_cad for t in cluster)
            severity = min(100, 40 + len(cluster) * 10 + (total / FINTRAC_REPORTING_THRESHOLD_CAD) * 5)
            alerts.append(AMLAlert(
                alert_id=f"ALR-{uuid.uuid4().hex[:10].upper()}",
                client_id=client_id,
                alert_type=AlertType.STRUCTURING,
                rule_name="STRUCT-001: Multiple sub-$10K deposits within 48h",
                severity_score=round(severity, 1),
                triggered_transactions=[t.transaction_id for t in cluster],
                status=AlertStatus.NEW,
                created_at=cluster[-1].timestamp + timedelta(minutes=5),
                is_true_positive=any(t.is_suspicious for t in cluster),
            ))
            break  # one alert per client per pattern
    return alerts


def _detect_rapid_movement(
    client_id: str, txns: list[Transaction]
) -> list[AMLAlert]:
    """Large deposit immediately followed by withdrawal/transfer."""
    alerts = []
    large_deposits = [
        t for t in txns
        if t.transaction_type == TransactionType.DEPOSIT
        and t.amount_cad >= FINTRAC_REPORTING_THRESHOLD_CAD
    ]
    for dep in large_deposits:
        window = dep.timestamp + timedelta(hours=6)
        quick_moves = [
            t for t in txns
            if t.transaction_type in (TransactionType.WITHDRAWAL, TransactionType.TRANSFER_OUT, TransactionType.BUY)
            and dep.timestamp < t.timestamp <= window
            and t.amount_cad >= dep.amount_cad * 0.70
        ]
        if quick_moves:
            triggered = [dep.transaction_id] + [t.transaction_id for t in quick_moves]
            severity = min(100, 50 + dep.amount_cad / 10_000 * 5)
            alerts.append(AMLAlert(
                alert_id=f"ALR-{uuid.uuid4().hex[:10].upper()}",
                client_id=client_id,
                alert_type=AlertType.RAPID_MOVEMENT,
                rule_name="RAPID-001: Large deposit with immediate outflow",
                severity_score=round(severity, 1),
                triggered_transactions=triggered,
                status=AlertStatus.NEW,
                created_at=quick_moves[0].timestamp + timedelta(minutes=5),
                is_true_positive=any(t.is_suspicious for t in [dep] + quick_moves),
            ))
            break
    return alerts


def _detect_crypto_layering(
    client_id: str, txns: list[Transaction]
) -> list[AMLAlert]:
    """Fiat -> crypto -> privacy coin swap -> external withdrawal chain."""
    alerts = []
    privacy_txns = [
        t for t in txns
        if t.currency in (Currency.XMR, Currency.ZEC)
    ]
    if len(privacy_txns) >= 2:
        severity = min(100, 60 + len(privacy_txns) * 10)
        alerts.append(AMLAlert(
            alert_id=f"ALR-{uuid.uuid4().hex[:10].upper()}",
            client_id=client_id,
            alert_type=AlertType.CRYPTO_LAYERING,
            rule_name="CRYPTO-001: Privacy coin conversion detected",
            severity_score=round(severity, 1),
            triggered_transactions=[t.transaction_id for t in privacy_txns],
            status=AlertStatus.NEW,
            created_at=privacy_txns[-1].timestamp + timedelta(minutes=10),
            is_true_positive=any(t.is_suspicious for t in privacy_txns),
        ))
    return alerts


def _detect_round_tripping(
    client_id: str, txns: list[Transaction]
) -> list[AMLAlert]:
    """Rapid buy-sell cycles on the same asset."""
    alerts = []
    buys = [t for t in txns if t.transaction_type == TransactionType.BUY]
    sells = [t for t in txns if t.transaction_type == TransactionType.SELL]

    for buy in buys:
        window = buy.timestamp + timedelta(hours=4)
        matching_sells = [
            s for s in sells
            if buy.timestamp < s.timestamp <= window
            and abs(s.amount_cad - buy.amount_cad) / max(buy.amount_cad, 1) < 0.10
            and s.description == buy.description
        ]
        if len(matching_sells) >= 2:
            triggered = [buy.transaction_id] + [s.transaction_id for s in matching_sells]
            alerts.append(AMLAlert(
                alert_id=f"ALR-{uuid.uuid4().hex[:10].upper()}",
                client_id=client_id,
                alert_type=AlertType.ROUND_TRIPPING,
                rule_name="ROUND-001: Rapid buy-sell cycles on same asset",
                severity_score=55.0,
                triggered_transactions=triggered,
                status=AlertStatus.NEW,
                created_at=matching_sells[-1].timestamp + timedelta(minutes=5),
                is_true_positive=any(t.is_suspicious for t in [buy] + matching_sells),
            ))
            break
    return alerts


def _detect_velocity_spike(
    client_id: str, txns: list[Transaction]
) -> list[AMLAlert]:
    """Transaction count in a single day far exceeds 90-day average."""
    alerts = []
    if len(txns) < 30:
        return alerts

    daily_counts: dict[str, list[Transaction]] = defaultdict(list)
    for t in txns:
        daily_counts[t.timestamp.strftime("%Y-%m-%d")].append(t)

    if len(daily_counts) < 30:
        return alerts

    sorted_days = sorted(daily_counts.keys())
    avg_daily = len(txns) / len(daily_counts)

    for day in sorted_days[-30:]:
        day_txns = daily_counts[day]
        if len(day_txns) >= avg_daily * VELOCITY_SPIKE_MULTIPLIER and len(day_txns) >= 10:
            severity = min(100, 40 + (len(day_txns) / avg_daily) * 8)
            alerts.append(AMLAlert(
                alert_id=f"ALR-{uuid.uuid4().hex[:10].upper()}",
                client_id=client_id,
                alert_type=AlertType.VELOCITY_SPIKE,
                rule_name=f"VEL-001: {len(day_txns)} txns on {day} vs avg {avg_daily:.1f}/day",
                severity_score=round(severity, 1),
                triggered_transactions=[t.transaction_id for t in day_txns],
                status=AlertStatus.NEW,
                created_at=day_txns[-1].timestamp + timedelta(hours=1),
                is_true_positive=any(t.is_suspicious for t in day_txns),
            ))
            break
    return alerts


def _detect_dormant_activation(
    client_id: str, txns: list[Transaction]
) -> list[AMLAlert]:
    """Large transaction on a previously dormant account."""
    alerts = []
    if len(txns) < 2:
        return alerts

    for i in range(1, len(txns)):
        gap_days = (txns[i].timestamp - txns[i - 1].timestamp).days
        if gap_days >= DORMANT_THRESHOLD_DAYS and txns[i].amount_cad >= 10_000:
            severity = min(100, 50 + gap_days / 30 * 5 + txns[i].amount_cad / 10_000 * 3)
            alerts.append(AMLAlert(
                alert_id=f"ALR-{uuid.uuid4().hex[:10].upper()}",
                client_id=client_id,
                alert_type=AlertType.DORMANT_ACTIVATION,
                rule_name=f"DORM-001: {gap_days}-day dormant period then ${txns[i].amount_cad:,.0f} transaction",
                severity_score=round(severity, 1),
                triggered_transactions=[txns[i].transaction_id],
                status=AlertStatus.NEW,
                created_at=txns[i].timestamp + timedelta(minutes=15),
                is_true_positive=txns[i].is_suspicious,
            ))
            break
    return alerts


def _detect_geographic_anomaly(
    client_id: str, txns: list[Transaction]
) -> list[AMLAlert]:
    """Transactions from IP ranges outside the client's normal pattern."""
    alerts = []
    anomalous_prefixes = {"185.", "91.", "45.", "103.", "193."}
    anomalous_txns = [
        t for t in txns
        if any(t.ip_address.startswith(p) for p in anomalous_prefixes)
    ]
    if len(anomalous_txns) >= 2:
        severity = min(100, 45 + len(anomalous_txns) * 8)
        alerts.append(AMLAlert(
            alert_id=f"ALR-{uuid.uuid4().hex[:10].upper()}",
            client_id=client_id,
            alert_type=AlertType.GEOGRAPHIC_ANOMALY,
            rule_name="GEO-001: Transactions from anomalous IP addresses",
            severity_score=round(severity, 1),
            triggered_transactions=[t.transaction_id for t in anomalous_txns],
            status=AlertStatus.NEW,
            created_at=anomalous_txns[-1].timestamp + timedelta(minutes=10),
            is_true_positive=any(t.is_suspicious for t in anomalous_txns),
        ))
    return alerts


def _detect_third_party(
    client_id: str, txns: list[Transaction]
) -> list[AMLAlert]:
    """Funds flowing to/from unrelated third parties via wire."""
    alerts = []
    wire_transfers = [
        t for t in txns
        if t.method == TransactionMethod.WIRE
        and t.transaction_type in (TransactionType.TRANSFER_IN, TransactionType.TRANSFER_OUT)
    ]
    if len(wire_transfers) >= 3:
        total = sum(t.amount_cad for t in wire_transfers)
        severity = min(100, 40 + len(wire_transfers) * 7 + total / 50_000 * 5)
        alerts.append(AMLAlert(
            alert_id=f"ALR-{uuid.uuid4().hex[:10].upper()}",
            client_id=client_id,
            alert_type=AlertType.THIRD_PARTY_PATTERN,
            rule_name=f"3PTY-001: {len(wire_transfers)} wire transfers totaling ${total:,.0f}",
            severity_score=round(severity, 1),
            triggered_transactions=[t.transaction_id for t in wire_transfers],
            status=AlertStatus.NEW,
            created_at=wire_transfers[-1].timestamp + timedelta(minutes=10),
            is_true_positive=any(t.is_suspicious for t in wire_transfers),
        ))
    return alerts


def _detect_pep_sanctions(
    client_id: str,
    txns: list[Transaction],
    client: ClientProfile | None = None,
) -> list[AMLAlert]:
    """Flag any significant activity for PEP-flagged clients."""
    alerts = []
    if client and client.is_pep:
        large_txns = [t for t in txns if t.amount_cad >= 5_000]
        if large_txns:
            severity = 75.0
            alerts.append(AMLAlert(
                alert_id=f"ALR-{uuid.uuid4().hex[:10].upper()}",
                client_id=client_id,
                alert_type=AlertType.PEP_SANCTIONS_HIT,
                rule_name="PEP-001: Significant activity by Politically Exposed Person",
                severity_score=severity,
                triggered_transactions=[t.transaction_id for t in large_txns[:5]],
                status=AlertStatus.NEW,
                created_at=large_txns[-1].timestamp + timedelta(minutes=5),
                is_true_positive=True,
            ))
    return alerts


def _detect_age_amount_mismatch(
    client_id: str,
    txns: list[Transaction],
    client: ClientProfile | None = None,
) -> list[AMLAlert]:
    """Transactions inconsistent with declared income."""
    alerts = []
    if not client:
        return alerts

    income_ceilings = {
        "0-25k": 10_000, "25k-50k": 20_000, "50k-75k": 35_000,
        "75k-100k": 50_000, "100k-150k": 75_000, "150k-200k": 100_000,
        "200k-300k": 150_000, "300k+": 500_000,
    }
    ceiling = income_ceilings.get(client.income_range, 100_000)

    big_txns = [t for t in txns if t.amount_cad >= ceiling * 1.5]
    if big_txns:
        severity = min(100, 50 + big_txns[0].amount_cad / ceiling * 10)
        alerts.append(AMLAlert(
            alert_id=f"ALR-{uuid.uuid4().hex[:10].upper()}",
            client_id=client_id,
            alert_type=AlertType.AGE_AMOUNT_MISMATCH,
            rule_name=f"MATCH-001: ${big_txns[0].amount_cad:,.0f} deposit vs {client.income_range} income",
            severity_score=round(severity, 1),
            triggered_transactions=[t.transaction_id for t in big_txns[:3]],
            status=AlertStatus.NEW,
            created_at=big_txns[0].timestamp + timedelta(minutes=10),
            is_true_positive=any(t.is_suspicious for t in big_txns),
        ))
    return alerts


ALL_DETECTORS = [
    _detect_structuring,
    _detect_rapid_movement,
    _detect_crypto_layering,
    _detect_round_tripping,
    _detect_velocity_spike,
    _detect_dormant_activation,
    _detect_geographic_anomaly,
    _detect_third_party,
]

CLIENT_AWARE_DETECTORS = [
    _detect_pep_sanctions,
    _detect_age_amount_mismatch,
]


def _generate_false_positive_alerts(
    txn_index: dict[str, list[Transaction]],
    client_map: dict[str, ClientProfile],
    existing_alert_clients: set[str],
    target_count: int = 150,
    seed: int = 42,
) -> list[AMLAlert]:
    """Generate realistic false positive alerts from normal client activity.

    Real AML systems have 80-95% false positive rates. These alerts look
    suspicious on the surface but are actually benign.
    """
    import random as _rng
    _rng.seed(seed)

    fp_alerts: list[AMLAlert] = []
    candidates = [
        cid for cid in txn_index
        if cid not in existing_alert_clients and len(txn_index[cid]) >= 10
    ]
    _rng.shuffle(candidates)

    fp_scenarios = [
        (AlertType.STRUCTURING, "STRUCT-FP: Multiple deposits near threshold (legitimate savings pattern)"),
        (AlertType.RAPID_MOVEMENT, "RAPID-FP: Large deposit followed by investment purchase"),
        (AlertType.VELOCITY_SPIKE, "VEL-FP: Increased trading during market volatility"),
        (AlertType.DORMANT_ACTIVATION, "DORM-FP: Account reactivation after break"),
        (AlertType.GEOGRAPHIC_ANOMALY, "GEO-FP: Transaction from travel/VPN location"),
        (AlertType.AGE_AMOUNT_MISMATCH, "MATCH-FP: Inheritance/bonus deposit flagged"),
        (AlertType.THIRD_PARTY_PATTERN, "3PTY-FP: Family member transfer pattern"),
        (AlertType.ROUND_TRIPPING, "ROUND-FP: Rebalancing trades flagged as wash"),
        (AlertType.CRYPTO_LAYERING, "CRYPTO-FP: Normal crypto portfolio rebalancing"),
        (AlertType.RAPID_MOVEMENT, "RAPID-FP: Down payment withdrawal after savings"),
    ]

    for i, cid in enumerate(candidates[:target_count]):
        txns = txn_index[cid]
        scenario = _rng.choice(fp_scenarios)
        sample_txns = _rng.sample(txns, min(3, len(txns)))

        severity = _rng.uniform(25, 65)

        fp_alerts.append(AMLAlert(
            alert_id=f"ALR-{uuid.uuid4().hex[:10].upper()}",
            client_id=cid,
            alert_type=scenario[0],
            rule_name=scenario[1],
            severity_score=round(severity, 1),
            triggered_transactions=[t.transaction_id for t in sample_txns],
            status=AlertStatus.NEW,
            created_at=sample_txns[-1].timestamp + timedelta(minutes=_rng.randint(5, 30)),
            is_true_positive=False,
        ))

    return fp_alerts


def generate_alerts(
    transactions: list[Transaction],
    clients: list[ClientProfile] | None = None,
    false_positive_ratio: float = 0.80,
) -> list[AMLAlert]:
    """Run all detection rules across all client transaction histories.

    Generates both real alerts from rule detection AND synthetic false positive
    alerts to achieve realistic ~80% false positive rate for triage training.
    """
    client_map = {c.client_id: c for c in (clients or [])}
    txn_index = _build_client_txn_index(transactions)
    all_alerts: list[AMLAlert] = []

    for client_id, client_txns in txn_index.items():
        for detector in ALL_DETECTORS:
            all_alerts.extend(detector(client_id, client_txns))

        client = client_map.get(client_id)
        for detector in CLIENT_AWARE_DETECTORS:
            all_alerts.extend(detector(client_id, client_txns, client))

    seen: set[tuple[str, str]] = set()
    deduped: list[AMLAlert] = []
    for alert in all_alerts:
        key = (alert.client_id, alert.alert_type.value)
        if key not in seen:
            seen.add(key)
            deduped.append(alert)

    tp_count = len(deduped)
    target_fp = int(tp_count / (1 - false_positive_ratio) * false_positive_ratio)

    existing_clients = {a.client_id for a in deduped}
    fp_alerts = _generate_false_positive_alerts(
        txn_index, client_map, existing_clients, target_count=target_fp,
    )
    deduped.extend(fp_alerts)

    deduped.sort(key=lambda a: a.created_at)
    return deduped
