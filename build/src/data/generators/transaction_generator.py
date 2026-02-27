"""Generate realistic Wealthsimple transactions with injected suspicious patterns.

Produces normal financial activity (trades, deposits, withdrawals, crypto)
plus 10 AML typologies modeled after real FINTRAC indicators.
"""

from __future__ import annotations

import random
import uuid
from datetime import datetime, timedelta
from typing import Any

from src.data.models import (
    AccountType,
    ClientProfile,
    CounterpartyType,
    Currency,
    Transaction,
    TransactionMethod,
    TransactionType,
)

CRYPTO_CURRENCIES = [Currency.BTC, Currency.ETH, Currency.SOL, Currency.USDT, Currency.USDC]
PRIVACY_COINS = [Currency.XMR, Currency.ZEC]
FIAT_CURRENCIES = [Currency.CAD, Currency.USD]

STOCK_DESCRIPTIONS = [
    "AAPL", "TSLA", "SHOP.TO", "RY.TO", "TD.TO", "ENB.TO", "CNR.TO",
    "BNS.TO", "BCE.TO", "SU.TO", "MSFT", "AMZN", "GOOGL", "NVDA",
    "XEQT.TO", "VEQT.TO", "VFV.TO", "ZAG.TO", "XIU.TO",
]

IP_POOLS = {
    "ON": ["142.204.{}.{}", "174.112.{}.{}"],
    "BC": ["70.66.{}.{}", "207.216.{}.{}"],
    "AB": ["24.77.{}.{}", "209.171.{}.{}"],
    "QC": ["96.20.{}.{}", "206.167.{}.{}"],
    "default": ["192.168.{}.{}", "10.0.{}.{}"],
}

ANOMALOUS_IPS = [
    "185.220.101.{}", "91.218.114.{}", "45.154.255.{}",
    "103.152.220.{}", "193.56.29.{}",
]


def _gen_ip(province: str, anomalous: bool = False) -> str:
    if anomalous:
        template = random.choice(ANOMALOUS_IPS)
        return template.format(random.randint(1, 254))
    pool = IP_POOLS.get(province, IP_POOLS["default"])
    template = random.choice(pool)
    return template.format(random.randint(1, 254), random.randint(1, 254))


def _gen_device() -> str:
    return f"dev-{uuid.uuid4().hex[:12]}"


def _normal_transactions(
    client: ClientProfile,
    start_date: datetime,
    end_date: datetime,
    count: int,
) -> list[Transaction]:
    """Generate normal, benign transaction activity for a client."""
    txns: list[Transaction] = []
    device = _gen_device()
    delta_days = (end_date - start_date).days

    for _ in range(count):
        account = random.choice(client.accounts)
        ts = start_date + timedelta(
            days=random.randint(0, delta_days),
            hours=random.randint(6, 23),
            minutes=random.randint(0, 59),
        )

        if account.account_type == AccountType.CRYPTO:
            txn_type = random.choices(
                [TransactionType.BUY, TransactionType.SELL, TransactionType.CRYPTO_SWAP,
                 TransactionType.DEPOSIT, TransactionType.WITHDRAWAL, TransactionType.STAKING_REWARD],
                weights=[0.3, 0.2, 0.1, 0.15, 0.1, 0.15],
                k=1,
            )[0]
            currency = random.choice(CRYPTO_CURRENCIES)
            method = TransactionMethod.CRYPTO_TRANSFER if txn_type == TransactionType.CRYPTO_SWAP else TransactionMethod.E_TRANSFER
            cpty = CounterpartyType.EXCHANGE if txn_type in (TransactionType.BUY, TransactionType.SELL) else CounterpartyType.EXTERNAL_WALLET
            amount = round(random.uniform(10, 5_000), 2)
            desc = f"{txn_type.value} {currency.value}"
        else:
            txn_type = random.choices(
                [TransactionType.BUY, TransactionType.SELL, TransactionType.DEPOSIT,
                 TransactionType.WITHDRAWAL, TransactionType.DIVIDEND, TransactionType.TRANSFER_IN],
                weights=[0.3, 0.15, 0.2, 0.1, 0.15, 0.1],
                k=1,
            )[0]
            currency = random.choice(FIAT_CURRENCIES)
            method = TransactionMethod.E_TRANSFER if txn_type in (TransactionType.DEPOSIT, TransactionType.WITHDRAWAL) else TransactionMethod.INTERNAL
            cpty = CounterpartyType.BANK if txn_type in (TransactionType.DEPOSIT, TransactionType.WITHDRAWAL) else CounterpartyType.BROKERAGE
            amount = round(random.uniform(25, 8_000), 2)
            desc = random.choice(STOCK_DESCRIPTIONS) if txn_type in (TransactionType.BUY, TransactionType.SELL) else txn_type.value

        txns.append(Transaction(
            transaction_id=f"TXN-{uuid.uuid4().hex[:10].upper()}",
            client_id=client.client_id,
            account_id=account.account_id,
            account_type=account.account_type,
            transaction_type=txn_type,
            amount_cad=amount,
            currency=currency,
            counterparty_type=cpty,
            method=method,
            timestamp=ts,
            ip_address=_gen_ip(client.province),
            device_fingerprint=device,
            description=desc,
        ))

    return txns


# ---------------------------------------------------------------------------
# Suspicious pattern injectors (one per AML typology)
# ---------------------------------------------------------------------------

def _inject_structuring(
    client: ClientProfile, base_date: datetime
) -> list[Transaction]:
    """Multiple deposits just below $10K within 48 hours."""
    txns = []
    account = client.accounts[0]
    num_deposits = random.randint(3, 7)
    for i in range(num_deposits):
        amount = round(random.uniform(8_500, 9_999), 2)
        ts = base_date + timedelta(hours=random.randint(0, 47), minutes=random.randint(0, 59))
        txns.append(Transaction(
            transaction_id=f"TXN-{uuid.uuid4().hex[:10].upper()}",
            client_id=client.client_id,
            account_id=account.account_id,
            account_type=account.account_type,
            transaction_type=TransactionType.DEPOSIT,
            amount_cad=amount,
            currency=Currency.CAD,
            counterparty_type=CounterpartyType.BANK,
            method=TransactionMethod.E_TRANSFER,
            timestamp=ts,
            ip_address=_gen_ip(client.province),
            device_fingerprint=_gen_device(),
            description="e-Transfer deposit",
            is_suspicious=True,
            suspicious_pattern="structuring",
        ))
    return txns


def _inject_rapid_movement(
    client: ClientProfile, base_date: datetime
) -> list[Transaction]:
    """Large deposit immediately followed by crypto purchase or withdrawal."""
    account = client.accounts[0]
    amount = round(random.uniform(15_000, 80_000), 2)
    deposit = Transaction(
        transaction_id=f"TXN-{uuid.uuid4().hex[:10].upper()}",
        client_id=client.client_id,
        account_id=account.account_id,
        account_type=account.account_type,
        transaction_type=TransactionType.DEPOSIT,
        amount_cad=amount,
        currency=Currency.CAD,
        counterparty_type=CounterpartyType.BANK,
        method=TransactionMethod.WIRE,
        timestamp=base_date,
        ip_address=_gen_ip(client.province),
        device_fingerprint=_gen_device(),
        description="Wire deposit",
        is_suspicious=True,
        suspicious_pattern="rapid_movement",
    )
    withdrawal = Transaction(
        transaction_id=f"TXN-{uuid.uuid4().hex[:10].upper()}",
        client_id=client.client_id,
        account_id=account.account_id,
        account_type=account.account_type,
        transaction_type=TransactionType.WITHDRAWAL,
        amount_cad=amount * random.uniform(0.90, 0.99),
        currency=Currency.CAD,
        counterparty_type=CounterpartyType.BANK,
        method=TransactionMethod.WIRE,
        timestamp=base_date + timedelta(hours=random.randint(1, 4)),
        ip_address=_gen_ip(client.province),
        device_fingerprint=_gen_device(),
        description="Wire withdrawal",
        is_suspicious=True,
        suspicious_pattern="rapid_movement",
    )
    return [deposit, withdrawal]


def _inject_crypto_layering(
    client: ClientProfile, base_date: datetime
) -> list[Transaction]:
    """Fiat deposit -> BTC -> privacy coin swap -> external wallet withdrawal."""
    crypto_accts = [a for a in client.accounts if a.account_type == AccountType.CRYPTO]
    if not crypto_accts:
        crypto_accts = client.accounts
    account = crypto_accts[0]
    device = _gen_device()
    amount = round(random.uniform(5_000, 40_000), 2)

    txns = [
        Transaction(
            transaction_id=f"TXN-{uuid.uuid4().hex[:10].upper()}",
            client_id=client.client_id,
            account_id=account.account_id,
            account_type=account.account_type,
            transaction_type=TransactionType.DEPOSIT,
            amount_cad=amount,
            currency=Currency.CAD,
            counterparty_type=CounterpartyType.BANK,
            method=TransactionMethod.E_TRANSFER,
            timestamp=base_date,
            ip_address=_gen_ip(client.province),
            device_fingerprint=device,
            description="Deposit for crypto purchase",
            is_suspicious=True,
            suspicious_pattern="crypto_layering",
        ),
        Transaction(
            transaction_id=f"TXN-{uuid.uuid4().hex[:10].upper()}",
            client_id=client.client_id,
            account_id=account.account_id,
            account_type=AccountType.CRYPTO,
            transaction_type=TransactionType.BUY,
            amount_cad=amount * 0.98,
            currency=Currency.BTC,
            counterparty_type=CounterpartyType.EXCHANGE,
            method=TransactionMethod.INTERNAL,
            timestamp=base_date + timedelta(minutes=random.randint(5, 30)),
            ip_address=_gen_ip(client.province),
            device_fingerprint=device,
            description="Buy BTC",
            is_suspicious=True,
            suspicious_pattern="crypto_layering",
        ),
        Transaction(
            transaction_id=f"TXN-{uuid.uuid4().hex[:10].upper()}",
            client_id=client.client_id,
            account_id=account.account_id,
            account_type=AccountType.CRYPTO,
            transaction_type=TransactionType.CRYPTO_SWAP,
            amount_cad=amount * 0.97,
            currency=random.choice(PRIVACY_COINS),
            counterparty_type=CounterpartyType.EXCHANGE,
            method=TransactionMethod.CRYPTO_TRANSFER,
            timestamp=base_date + timedelta(hours=random.randint(1, 3)),
            ip_address=_gen_ip(client.province),
            device_fingerprint=device,
            description="Swap BTC to privacy coin",
            is_suspicious=True,
            suspicious_pattern="crypto_layering",
        ),
        Transaction(
            transaction_id=f"TXN-{uuid.uuid4().hex[:10].upper()}",
            client_id=client.client_id,
            account_id=account.account_id,
            account_type=AccountType.CRYPTO,
            transaction_type=TransactionType.WITHDRAWAL,
            amount_cad=amount * 0.95,
            currency=random.choice(PRIVACY_COINS),
            counterparty_type=CounterpartyType.EXTERNAL_WALLET,
            method=TransactionMethod.CRYPTO_TRANSFER,
            timestamp=base_date + timedelta(hours=random.randint(4, 8)),
            ip_address=_gen_ip(client.province),
            device_fingerprint=device,
            description="Withdraw to external wallet",
            is_suspicious=True,
            suspicious_pattern="crypto_layering",
        ),
    ]
    return txns


def _inject_round_tripping(
    client: ClientProfile, base_date: datetime
) -> list[Transaction]:
    """Deposit -> buy/sell same asset repeatedly -> withdraw."""
    account = client.accounts[0]
    device = _gen_device()
    amount = round(random.uniform(10_000, 50_000), 2)
    stock = random.choice(STOCK_DESCRIPTIONS)
    txns = [
        Transaction(
            transaction_id=f"TXN-{uuid.uuid4().hex[:10].upper()}",
            client_id=client.client_id,
            account_id=account.account_id,
            account_type=account.account_type,
            transaction_type=TransactionType.DEPOSIT,
            amount_cad=amount,
            currency=Currency.CAD,
            counterparty_type=CounterpartyType.BANK,
            method=TransactionMethod.E_TRANSFER,
            timestamp=base_date,
            ip_address=_gen_ip(client.province),
            device_fingerprint=device,
            description="Deposit",
            is_suspicious=True,
            suspicious_pattern="round_tripping",
        ),
    ]
    current = base_date + timedelta(hours=1)
    for _ in range(random.randint(3, 6)):
        for ttype in [TransactionType.BUY, TransactionType.SELL]:
            txns.append(Transaction(
                transaction_id=f"TXN-{uuid.uuid4().hex[:10].upper()}",
                client_id=client.client_id,
                account_id=account.account_id,
                account_type=account.account_type,
                transaction_type=ttype,
                amount_cad=amount * random.uniform(0.95, 1.05),
                currency=Currency.CAD,
                counterparty_type=CounterpartyType.BROKERAGE,
                method=TransactionMethod.INTERNAL,
                timestamp=current,
                ip_address=_gen_ip(client.province),
                device_fingerprint=device,
                description=f"{ttype.value} {stock}",
                is_suspicious=True,
                suspicious_pattern="round_tripping",
            ))
            current += timedelta(minutes=random.randint(10, 60))

    txns.append(Transaction(
        transaction_id=f"TXN-{uuid.uuid4().hex[:10].upper()}",
        client_id=client.client_id,
        account_id=account.account_id,
        account_type=account.account_type,
        transaction_type=TransactionType.WITHDRAWAL,
        amount_cad=amount * 0.98,
        currency=Currency.CAD,
        counterparty_type=CounterpartyType.BANK,
        method=TransactionMethod.E_TRANSFER,
        timestamp=current + timedelta(hours=1),
        ip_address=_gen_ip(client.province),
        device_fingerprint=device,
        description="Withdrawal",
        is_suspicious=True,
        suspicious_pattern="round_tripping",
    ))
    return txns


def _inject_velocity_spike(
    client: ClientProfile, base_date: datetime
) -> list[Transaction]:
    """Sudden burst of transactions well above historical baseline."""
    account = client.accounts[0]
    device = _gen_device()
    txns = []
    for _ in range(random.randint(15, 30)):
        ts = base_date + timedelta(hours=random.randint(0, 23), minutes=random.randint(0, 59))
        txns.append(Transaction(
            transaction_id=f"TXN-{uuid.uuid4().hex[:10].upper()}",
            client_id=client.client_id,
            account_id=account.account_id,
            account_type=account.account_type,
            transaction_type=random.choice([TransactionType.BUY, TransactionType.SELL, TransactionType.DEPOSIT]),
            amount_cad=round(random.uniform(500, 5_000), 2),
            currency=Currency.CAD,
            counterparty_type=CounterpartyType.BROKERAGE,
            method=TransactionMethod.INTERNAL,
            timestamp=ts,
            ip_address=_gen_ip(client.province),
            device_fingerprint=device,
            description="Velocity spike activity",
            is_suspicious=True,
            suspicious_pattern="velocity_spike",
        ))
    return txns


def _inject_dormant_activation(
    client: ClientProfile, base_date: datetime
) -> list[Transaction]:
    """Large deposit on a previously dormant account."""
    account = client.accounts[0]
    amount = round(random.uniform(20_000, 100_000), 2)
    return [Transaction(
        transaction_id=f"TXN-{uuid.uuid4().hex[:10].upper()}",
        client_id=client.client_id,
        account_id=account.account_id,
        account_type=account.account_type,
        transaction_type=TransactionType.DEPOSIT,
        amount_cad=amount,
        currency=Currency.CAD,
        counterparty_type=CounterpartyType.BANK,
        method=TransactionMethod.WIRE,
        timestamp=base_date,
        ip_address=_gen_ip(client.province),
        device_fingerprint=_gen_device(),
        description="Large deposit on dormant account",
        is_suspicious=True,
        suspicious_pattern="dormant_activation",
    )]


def _inject_geographic_anomaly(
    client: ClientProfile, base_date: datetime
) -> list[Transaction]:
    """Transactions from unusual IPs far from client's province."""
    account = client.accounts[0]
    device = _gen_device()
    txns = []
    for _ in range(random.randint(3, 6)):
        ts = base_date + timedelta(hours=random.randint(0, 12))
        txns.append(Transaction(
            transaction_id=f"TXN-{uuid.uuid4().hex[:10].upper()}",
            client_id=client.client_id,
            account_id=account.account_id,
            account_type=account.account_type,
            transaction_type=random.choice([TransactionType.DEPOSIT, TransactionType.WITHDRAWAL, TransactionType.BUY]),
            amount_cad=round(random.uniform(2_000, 15_000), 2),
            currency=Currency.CAD,
            counterparty_type=CounterpartyType.BANK,
            method=TransactionMethod.E_TRANSFER,
            timestamp=ts,
            ip_address=_gen_ip(client.province, anomalous=True),
            device_fingerprint=device,
            description="Transaction from anomalous location",
            is_suspicious=True,
            suspicious_pattern="geographic_anomaly",
        ))
    return txns


def _inject_third_party(
    client: ClientProfile, base_date: datetime
) -> list[Transaction]:
    """Funds flowing to/from unrelated external accounts."""
    account = client.accounts[0]
    txns = []
    for _ in range(random.randint(3, 5)):
        ts = base_date + timedelta(days=random.randint(0, 7), hours=random.randint(8, 20))
        direction = random.choice([TransactionType.TRANSFER_IN, TransactionType.TRANSFER_OUT])
        txns.append(Transaction(
            transaction_id=f"TXN-{uuid.uuid4().hex[:10].upper()}",
            client_id=client.client_id,
            account_id=account.account_id,
            account_type=account.account_type,
            transaction_type=direction,
            amount_cad=round(random.uniform(5_000, 25_000), 2),
            currency=Currency.CAD,
            counterparty_type=CounterpartyType.BANK,
            method=TransactionMethod.WIRE,
            timestamp=ts,
            ip_address=_gen_ip(client.province),
            device_fingerprint=_gen_device(),
            description=f"Third-party {direction.value}",
            is_suspicious=True,
            suspicious_pattern="third_party_pattern",
        ))
    return txns


def _inject_pep_sanctions(
    client: ClientProfile, base_date: datetime
) -> list[Transaction]:
    """Normal-looking transactions but client is a PEP/sanctions match."""
    account = client.accounts[0]
    txns = []
    for _ in range(random.randint(2, 4)):
        ts = base_date + timedelta(days=random.randint(0, 14), hours=random.randint(9, 17))
        txns.append(Transaction(
            transaction_id=f"TXN-{uuid.uuid4().hex[:10].upper()}",
            client_id=client.client_id,
            account_id=account.account_id,
            account_type=account.account_type,
            transaction_type=random.choice([TransactionType.DEPOSIT, TransactionType.BUY]),
            amount_cad=round(random.uniform(5_000, 50_000), 2),
            currency=Currency.CAD,
            counterparty_type=CounterpartyType.BANK,
            method=TransactionMethod.WIRE,
            timestamp=ts,
            ip_address=_gen_ip(client.province),
            device_fingerprint=_gen_device(),
            description="PEP/Sanctions flagged transaction",
            is_suspicious=True,
            suspicious_pattern="pep_sanctions_hit",
        ))
    return txns


def _inject_age_amount_mismatch(
    client: ClientProfile, base_date: datetime
) -> list[Transaction]:
    """Transaction amounts wildly inconsistent with declared income."""
    account = client.accounts[0]
    txns = []
    for _ in range(random.randint(2, 4)):
        ts = base_date + timedelta(days=random.randint(0, 14), hours=random.randint(8, 22))
        txns.append(Transaction(
            transaction_id=f"TXN-{uuid.uuid4().hex[:10].upper()}",
            client_id=client.client_id,
            account_id=account.account_id,
            account_type=account.account_type,
            transaction_type=TransactionType.DEPOSIT,
            amount_cad=round(random.uniform(50_000, 200_000), 2),
            currency=Currency.CAD,
            counterparty_type=CounterpartyType.BANK,
            method=TransactionMethod.WIRE,
            timestamp=ts,
            ip_address=_gen_ip(client.province),
            device_fingerprint=_gen_device(),
            description="Deposit inconsistent with income profile",
            is_suspicious=True,
            suspicious_pattern="age_amount_mismatch",
        ))
    return txns


PATTERN_INJECTORS = [
    _inject_structuring,
    _inject_rapid_movement,
    _inject_crypto_layering,
    _inject_round_tripping,
    _inject_velocity_spike,
    _inject_dormant_activation,
    _inject_geographic_anomaly,
    _inject_third_party,
    _inject_pep_sanctions,
    _inject_age_amount_mismatch,
]


def generate_transactions(
    clients: list[ClientProfile],
    num_transactions: int = 50_000,
    suspicious_ratio: float = 0.08,
    seed: int = 42,
) -> tuple[list[Transaction], dict[str, list[str]]]:
    """Generate transactions for all clients, injecting suspicious patterns.

    Returns:
        Tuple of (all_transactions, suspicious_client_patterns) where
        suspicious_client_patterns maps client_id -> list of pattern names.
    """
    random.seed(seed)
    all_txns: list[Transaction] = []
    suspicious_map: dict[str, list[str]] = {}

    start_date = datetime(2025, 6, 1)
    end_date = datetime(2026, 2, 20)

    suspicious_clients = [c for c in clients if c.risk_profile in (
        "medium", "high",
    ) or c.kyc_status == "flagged"][:int(len(clients) * suspicious_ratio)]

    normal_clients = [c for c in clients if c not in suspicious_clients]

    txn_per_normal = num_transactions // len(clients)
    for client in normal_clients:
        count = txn_per_normal + random.randint(-10, 10)
        all_txns.extend(_normal_transactions(client, start_date, end_date, max(count, 5)))

    for client in suspicious_clients:
        normal_count = txn_per_normal + random.randint(-5, 5)
        all_txns.extend(_normal_transactions(client, start_date, end_date, max(normal_count, 5)))

        num_patterns = random.randint(1, 3)
        injectors = random.sample(PATTERN_INJECTORS, min(num_patterns, len(PATTERN_INJECTORS)))
        patterns_for_client: list[str] = []
        for injector in injectors:
            inject_date = start_date + timedelta(days=random.randint(30, 250))
            suspicious_txns = injector(client, inject_date)
            all_txns.extend(suspicious_txns)
            if suspicious_txns:
                patterns_for_client.append(suspicious_txns[0].suspicious_pattern)

        if patterns_for_client:
            suspicious_map[client.client_id] = patterns_for_client

    all_txns.sort(key=lambda t: t.timestamp)
    return all_txns, suspicious_map
