"""Pydantic data models for the AML Investigation Agent.

Models Wealthsimple-specific account types, transaction patterns,
AML alerts, investigation results, and FINTRAC STR reports.
"""

from __future__ import annotations

import enum
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class AccountType(str, enum.Enum):
    TFSA = "tfsa"
    RRSP = "rrsp"
    SPOUSAL_RRSP = "spousal_rrsp"
    FHSA = "fhsa"
    RESP = "resp"
    PERSONAL = "personal"
    CRYPTO = "crypto"


class TransactionType(str, enum.Enum):
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    BUY = "buy"
    SELL = "sell"
    TRANSFER_IN = "transfer_in"
    TRANSFER_OUT = "transfer_out"
    CRYPTO_SWAP = "crypto_swap"
    STAKING_REWARD = "staking_reward"
    DIVIDEND = "dividend"
    OPTION_EXERCISE = "option_exercise"


class TransactionMethod(str, enum.Enum):
    E_TRANSFER = "e_transfer"
    WIRE = "wire"
    ACH = "ach"
    CRYPTO_TRANSFER = "crypto_transfer"
    INTERNAL = "internal"


class CounterpartyType(str, enum.Enum):
    BANK = "bank"
    EXCHANGE = "exchange"
    WS_INTERNAL = "ws_internal"
    EXTERNAL_WALLET = "external_wallet"
    BROKERAGE = "brokerage"


class Currency(str, enum.Enum):
    CAD = "CAD"
    USD = "USD"
    BTC = "BTC"
    ETH = "ETH"
    SOL = "SOL"
    XMR = "XMR"  # Monero (privacy coin)
    ZEC = "ZEC"  # Zcash (privacy coin)
    USDT = "USDT"
    USDC = "USDC"


class RiskProfile(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class KYCStatus(str, enum.Enum):
    VERIFIED = "verified"
    PENDING = "pending"
    FLAGGED = "flagged"


class AlertType(str, enum.Enum):
    STRUCTURING = "structuring"
    RAPID_MOVEMENT = "rapid_movement"
    CRYPTO_LAYERING = "crypto_layering"
    ROUND_TRIPPING = "round_tripping"
    VELOCITY_SPIKE = "velocity_spike"
    DORMANT_ACTIVATION = "dormant_activation"
    GEOGRAPHIC_ANOMALY = "geographic_anomaly"
    THIRD_PARTY_PATTERN = "third_party_pattern"
    PEP_SANCTIONS_HIT = "pep_sanctions_hit"
    AGE_AMOUNT_MISMATCH = "age_amount_mismatch"


class AlertStatus(str, enum.Enum):
    NEW = "new"
    TRIAGED = "triaged"
    INVESTIGATING = "investigating"
    REPORTED = "reported"
    CLOSED = "closed"


class RecommendedAction(str, enum.Enum):
    FILE_STR = "file_str"
    CLOSE = "close"
    ESCALATE = "escalate"


class HumanDecision(str, enum.Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"
    PENDING = "pending"


class SuspicionType(str, enum.Enum):
    MONEY_LAUNDERING = "money_laundering"
    TERRORIST_FINANCING = "terrorist_financing"
    BOTH = "both"


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

class Account(BaseModel):
    account_id: str
    account_type: AccountType
    opened_at: datetime
    balance_cad: float = 0.0


class ClientProfile(BaseModel):
    client_id: str
    first_name: str
    last_name: str
    email: str
    date_of_birth: datetime
    occupation: str
    income_range: str  # e.g. "50k-75k"
    accounts: list[Account] = Field(default_factory=list)
    risk_profile: RiskProfile = RiskProfile.LOW
    kyc_status: KYCStatus = KYCStatus.VERIFIED
    province: str = "ON"
    country: str = "CA"
    account_open_date: datetime | None = None
    is_pep: bool = False

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"


class Transaction(BaseModel):
    transaction_id: str
    client_id: str
    account_id: str
    account_type: AccountType
    transaction_type: TransactionType
    amount_cad: float
    currency: Currency = Currency.CAD
    counterparty_type: CounterpartyType = CounterpartyType.BANK
    method: TransactionMethod = TransactionMethod.E_TRANSFER
    timestamp: datetime
    ip_address: str = ""
    device_fingerprint: str = ""
    description: str = ""
    is_suspicious: bool = False
    suspicious_pattern: str = ""


class AMLAlert(BaseModel):
    alert_id: str
    client_id: str
    alert_type: AlertType
    rule_name: str
    severity_score: float = Field(ge=0, le=100)
    triggered_transactions: list[str] = Field(default_factory=list)
    status: AlertStatus = AlertStatus.NEW
    created_at: datetime
    is_true_positive: bool = False  # ground truth for training


class InvestigationStep(BaseModel):
    step_name: str
    tool_called: str
    input_params: dict[str, Any] = Field(default_factory=dict)
    output_summary: str = ""
    duration_ms: float = 0.0
    timestamp: datetime | None = None


class InvestigationResult(BaseModel):
    investigation_id: str
    alert_id: str
    client_id: str
    risk_score: float = Field(ge=0, le=100)
    confidence: float = Field(ge=0, le=1)
    findings: dict[str, Any] = Field(default_factory=dict)
    entity_relationships: list[dict[str, Any]] = Field(default_factory=list)
    watchlist_matches: list[dict[str, Any]] = Field(default_factory=list)
    behavioral_deviation_score: float = 0.0
    recommended_action: RecommendedAction = RecommendedAction.CLOSE
    steps_taken: list[InvestigationStep] = Field(default_factory=list)
    total_cost_usd: float = 0.0
    total_time_ms: float = 0.0
    created_at: datetime | None = None


class STRReport(BaseModel):
    report_id: str
    investigation_id: str
    narrative: str = ""
    suspicion_type: SuspicionType = SuspicionType.MONEY_LAUNDERING
    subject_info: dict[str, Any] = Field(default_factory=dict)
    transaction_summary: list[dict[str, Any]] = Field(default_factory=list)
    risk_indicators: list[str] = Field(default_factory=list)
    risk_score: float = Field(ge=0, le=100, default=0)
    recommended_filing: bool = False
    human_decision: HumanDecision = HumanDecision.PENDING
    created_at: datetime | None = None
    reviewed_at: datetime | None = None
    reviewed_by: str = ""
