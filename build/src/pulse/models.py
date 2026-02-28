"""Pydantic data models for WS Pulse -- Client Financial Intelligence.

Covers portfolios, holdings, financial events, recommendations, and
user financial goals. All types used by Pulse agents and dashboard.
"""

from __future__ import annotations

import enum
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class PulseAccountType(str, enum.Enum):
    TFSA = "tfsa"
    RRSP = "rrsp"
    NON_REGISTERED = "non_registered"
    CRYPTO = "crypto"
    FHSA = "fhsa"
    RESP = "resp"


class AssetClass(str, enum.Enum):
    CANADIAN_EQUITY = "canadian_equity"
    US_EQUITY = "us_equity"
    INTERNATIONAL_EQUITY = "international_equity"
    FIXED_INCOME = "fixed_income"
    CRYPTO = "crypto"
    CASH = "cash"
    ETF_EQUITY = "etf_equity"
    ETF_BOND = "etf_bond"


class EventType(str, enum.Enum):
    PAYCHECK = "paycheck"
    EARNINGS_REPORT = "earnings_report"
    MARKET_DROP = "market_drop"
    DIVIDEND_PAYMENT = "dividend_payment"
    BOC_RATE_DECISION = "boc_rate_decision"
    SUBSCRIPTION_AUDIT = "subscription_audit"


class EventPriority(str, enum.Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RecommendationAction(str, enum.Enum):
    ALLOCATE_TFSA = "allocate_tfsa"
    ALLOCATE_RRSP = "allocate_rrsp"
    BUILD_EMERGENCY = "build_emergency_fund"
    REBALANCE = "rebalance"
    HOLD = "hold"
    BUY_DIP = "buy_dip"
    TAKE_PROFIT = "take_profit"
    REVIEW_CONCENTRATION = "review_concentration"
    TAX_LOSS_HARVEST = "tax_loss_harvest"
    INCREASE_CONTRIBUTION = "increase_contribution"


class RecommendationStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    ADJUSTED = "adjusted"
    DISMISSED = "dismissed"


class RiskProfile(str, enum.Enum):
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    GROWTH = "growth"
    AGGRESSIVE = "aggressive"


# ---------------------------------------------------------------------------
# Core Models
# ---------------------------------------------------------------------------

class Holding(BaseModel):
    ticker: str
    name: str
    asset_class: AssetClass
    quantity: float
    avg_cost: float
    current_price: float
    market_value: float = 0.0
    unrealized_gain_pct: float = 0.0
    weight_pct: float = 0.0
    sector: str = ""
    currency: str = "CAD"

    def model_post_init(self, __context: Any) -> None:
        if self.market_value == 0:
            self.market_value = round(self.quantity * self.current_price, 2)
        if self.avg_cost > 0 and self.unrealized_gain_pct == 0:
            self.unrealized_gain_pct = round(
                (self.current_price - self.avg_cost) / self.avg_cost * 100, 2
            )


class Account(BaseModel):
    account_id: str
    account_type: PulseAccountType
    holdings: list[Holding] = Field(default_factory=list)
    cash_balance: float = 0.0
    contribution_room: float | None = None
    employer_match_pct: float | None = None

    @property
    def total_value(self) -> float:
        return round(
            sum(h.market_value for h in self.holdings) + self.cash_balance, 2
        )


class UserGoals(BaseModel):
    emergency_fund_target: float = 0.0
    emergency_fund_current: float = 0.0
    retirement_age: int = 65
    monthly_savings_target: float = 0.0
    risk_profile: RiskProfile = RiskProfile.MODERATE
    tax_bracket_pct: float = 30.0
    has_premium: bool = False


class Portfolio(BaseModel):
    user_id: str
    display_name: str
    age: int
    province: str
    occupation: str
    accounts: list[Account] = Field(default_factory=list)
    goals: UserGoals = Field(default_factory=UserGoals)
    created_at: datetime | None = None

    @property
    def total_value(self) -> float:
        return round(sum(a.total_value for a in self.accounts), 2)

    @property
    def all_holdings(self) -> list[Holding]:
        return [h for a in self.accounts for h in a.holdings]

    @property
    def asset_allocation(self) -> dict[str, float]:
        total = self.total_value
        if total == 0:
            return {}
        allocation: dict[str, float] = {}
        for h in self.all_holdings:
            cls = h.asset_class.value
            allocation[cls] = allocation.get(cls, 0) + h.market_value
        return {k: round(v / total * 100, 2) for k, v in allocation.items()}

    @property
    def sector_allocation(self) -> dict[str, float]:
        total = self.total_value
        if total == 0:
            return {}
        sectors: dict[str, float] = {}
        for h in self.all_holdings:
            s = h.sector or "Other"
            sectors[s] = sectors.get(s, 0) + h.market_value
        return {k: round(v / total * 100, 2) for k, v in sectors.items()}

    @property
    def concentration_risk(self) -> list[dict[str, Any]]:
        total = self.total_value
        if total == 0:
            return []
        risks = []
        for h in self.all_holdings:
            weight = h.market_value / total * 100
            if weight > 15:
                risks.append({
                    "ticker": h.ticker,
                    "weight_pct": round(weight, 2),
                    "severity": "high" if weight > 25 else "medium",
                })
        return sorted(risks, key=lambda x: x["weight_pct"], reverse=True)


class MarketEvent(BaseModel):
    event_id: str
    event_type: EventType
    priority: EventPriority = EventPriority.MEDIUM
    title: str
    description: str
    affected_tickers: list[str] = Field(default_factory=list)
    affected_users: list[str] = Field(default_factory=list)
    data: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime | None = None
    processed: bool = False


class Recommendation(BaseModel):
    recommendation_id: str
    user_id: str
    event_id: str
    event_type: EventType
    action: RecommendationAction
    priority: EventPriority = EventPriority.MEDIUM
    title: str
    narrative: str
    reasoning: list[str] = Field(default_factory=list)
    impact_summary: str = ""
    confidence: float = Field(ge=0, le=1, default=0.8)
    status: RecommendationStatus = RecommendationStatus.PENDING
    estimated_value_cad: float = 0.0
    created_at: datetime | None = None
    reviewed_at: datetime | None = None

    @property
    def action_label(self) -> str:
        labels = {
            RecommendationAction.ALLOCATE_TFSA: "Allocate to TFSA",
            RecommendationAction.ALLOCATE_RRSP: "Allocate to RRSP",
            RecommendationAction.BUILD_EMERGENCY: "Build Emergency Fund",
            RecommendationAction.REBALANCE: "Rebalance Portfolio",
            RecommendationAction.HOLD: "Hold Position",
            RecommendationAction.BUY_DIP: "Opportunity Buy",
            RecommendationAction.TAKE_PROFIT: "Take Profit",
            RecommendationAction.REVIEW_CONCENTRATION: "Review Concentration",
            RecommendationAction.TAX_LOSS_HARVEST: "Tax Loss Harvest",
            RecommendationAction.INCREASE_CONTRIBUTION: "Increase Contribution",
        }
        return labels.get(self.action, self.action.value)


class PulseProcessingResult(BaseModel):
    event: MarketEvent
    user_id: str
    portfolio_snapshot: dict[str, Any] = Field(default_factory=dict)
    impact_analysis: dict[str, Any] = Field(default_factory=dict)
    rag_context: dict[str, Any] = Field(default_factory=dict)
    recommendation: Recommendation | None = None
    processing_time_ms: float = 0.0
    pii_tokens_masked: int = 0
    cache_hit: bool = False
