"""Generates 10 realistic Canadian investor portfolios for WS Pulse.

Each portfolio represents a distinct Wealthsimple user persona with
real tickers, realistic account structures, and financial goals that
would be immediately recognizable to a Wealthsimple executive.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from src.pulse.models import (
    Account, AssetClass, Holding, Portfolio, PulseAccountType,
    RiskProfile, UserGoals,
)


TICKER_CATALOG = {
    "SHOP.TO": {"name": "Shopify Inc", "sector": "Technology", "asset_class": AssetClass.CANADIAN_EQUITY, "price": 107.50, "currency": "CAD"},
    "RY.TO": {"name": "Royal Bank of Canada", "sector": "Financials", "asset_class": AssetClass.CANADIAN_EQUITY, "price": 168.20, "currency": "CAD"},
    "ENB.TO": {"name": "Enbridge Inc", "sector": "Energy", "asset_class": AssetClass.CANADIAN_EQUITY, "price": 56.80, "currency": "CAD"},
    "BNS.TO": {"name": "Bank of Nova Scotia", "sector": "Financials", "asset_class": AssetClass.CANADIAN_EQUITY, "price": 73.40, "currency": "CAD"},
    "CNR.TO": {"name": "Canadian National Railway", "sector": "Industrials", "asset_class": AssetClass.CANADIAN_EQUITY, "price": 162.30, "currency": "CAD"},
    "TD.TO": {"name": "Toronto-Dominion Bank", "sector": "Financials", "asset_class": AssetClass.CANADIAN_EQUITY, "price": 82.50, "currency": "CAD"},
    "BAM.TO": {"name": "Brookfield Asset Mgmt", "sector": "Financials", "asset_class": AssetClass.CANADIAN_EQUITY, "price": 68.90, "currency": "CAD"},
    "SU.TO": {"name": "Suncor Energy", "sector": "Energy", "asset_class": AssetClass.CANADIAN_EQUITY, "price": 52.10, "currency": "CAD"},

    "VFV.TO": {"name": "Vanguard S&P 500 ETF", "sector": "Broad Market", "asset_class": AssetClass.ETF_EQUITY, "price": 122.40, "currency": "CAD"},
    "XIC.TO": {"name": "iShares Core S&P/TSX", "sector": "Broad Market", "asset_class": AssetClass.ETF_EQUITY, "price": 35.80, "currency": "CAD"},
    "XEQT.TO": {"name": "iShares All-Equity ETF", "sector": "Broad Market", "asset_class": AssetClass.ETF_EQUITY, "price": 28.90, "currency": "CAD"},
    "ZAG.TO": {"name": "BMO Aggregate Bond ETF", "sector": "Fixed Income", "asset_class": AssetClass.ETF_BOND, "price": 14.20, "currency": "CAD"},
    "XBB.TO": {"name": "iShares Core Bond ETF", "sector": "Fixed Income", "asset_class": AssetClass.ETF_BOND, "price": 26.80, "currency": "CAD"},
    "VEQT.TO": {"name": "Vanguard All-Equity ETF", "sector": "Broad Market", "asset_class": AssetClass.ETF_EQUITY, "price": 39.50, "currency": "CAD"},

    "AAPL": {"name": "Apple Inc", "sector": "Technology", "asset_class": AssetClass.US_EQUITY, "price": 227.60, "currency": "USD"},
    "MSFT": {"name": "Microsoft Corp", "sector": "Technology", "asset_class": AssetClass.US_EQUITY, "price": 415.30, "currency": "USD"},
    "AMZN": {"name": "Amazon.com Inc", "sector": "Technology", "asset_class": AssetClass.US_EQUITY, "price": 198.40, "currency": "USD"},
    "GOOGL": {"name": "Alphabet Inc", "sector": "Technology", "asset_class": AssetClass.US_EQUITY, "price": 175.20, "currency": "USD"},
    "NVDA": {"name": "NVIDIA Corp", "sector": "Technology", "asset_class": AssetClass.US_EQUITY, "price": 138.50, "currency": "USD"},
    "TSLA": {"name": "Tesla Inc", "sector": "Consumer Disc.", "asset_class": AssetClass.US_EQUITY, "price": 342.80, "currency": "USD"},
    "META": {"name": "Meta Platforms", "sector": "Technology", "asset_class": AssetClass.US_EQUITY, "price": 598.40, "currency": "USD"},
    "JPM": {"name": "JPMorgan Chase", "sector": "Financials", "asset_class": AssetClass.US_EQUITY, "price": 248.90, "currency": "USD"},

    "BTC": {"name": "Bitcoin", "sector": "Cryptocurrency", "asset_class": AssetClass.CRYPTO, "price": 96800.00, "currency": "USD"},
    "ETH": {"name": "Ethereum", "sector": "Cryptocurrency", "asset_class": AssetClass.CRYPTO, "price": 3420.00, "currency": "USD"},
    "SOL": {"name": "Solana", "sector": "Cryptocurrency", "asset_class": AssetClass.CRYPTO, "price": 185.60, "currency": "USD"},
}


def _h(ticker: str, qty: float, avg_cost_mult: float = 0.92) -> Holding:
    info = TICKER_CATALOG[ticker]
    avg_cost = round(info["price"] * avg_cost_mult, 2)
    return Holding(
        ticker=ticker,
        name=info["name"],
        asset_class=info["asset_class"],
        quantity=qty,
        avg_cost=avg_cost,
        current_price=info["price"],
        sector=info["sector"],
        currency=info["currency"],
    )


def generate_portfolios() -> list[Portfolio]:
    """Generate 10 realistic Canadian investor portfolios."""

    portfolios = [
        Portfolio(
            user_id="USR-001",
            display_name="Maya Chen",
            age=23,
            province="ON",
            occupation="University student (part-time barista)",
            accounts=[
                Account(
                    account_id="ACC-001-TFSA",
                    account_type=PulseAccountType.TFSA,
                    holdings=[
                        _h("XEQT.TO", 85, 0.95),
                        _h("VFV.TO", 20, 0.90),
                    ],
                    cash_balance=320.50,
                    contribution_room=4500.00,
                ),
                Account(
                    account_id="ACC-001-CRYPTO",
                    account_type=PulseAccountType.CRYPTO,
                    holdings=[
                        _h("BTC", 0.012, 1.15),
                        _h("ETH", 0.8, 1.05),
                    ],
                    cash_balance=0,
                ),
            ],
            goals=UserGoals(
                emergency_fund_target=3000,
                emergency_fund_current=1200,
                retirement_age=65,
                monthly_savings_target=200,
                risk_profile=RiskProfile.AGGRESSIVE,
                tax_bracket_pct=15,
                has_premium=False,
            ),
            created_at=datetime(2024, 9, 1),
        ),

        Portfolio(
            user_id="USR-002",
            display_name="James Wright",
            age=28,
            province="BC",
            occupation="Software engineer",
            accounts=[
                Account(
                    account_id="ACC-002-TFSA",
                    account_type=PulseAccountType.TFSA,
                    holdings=[
                        _h("VFV.TO", 80, 0.88),
                        _h("SHOP.TO", 40, 0.75),
                        _h("XIC.TO", 120, 0.93),
                    ],
                    cash_balance=850.00,
                    contribution_room=7000.00,
                ),
                Account(
                    account_id="ACC-002-RRSP",
                    account_type=PulseAccountType.RRSP,
                    holdings=[
                        _h("XEQT.TO", 200, 0.85),
                        _h("ZAG.TO", 150, 1.02),
                    ],
                    cash_balance=500.00,
                    contribution_room=18000.00,
                    employer_match_pct=4.0,
                ),
                Account(
                    account_id="ACC-002-CRYPTO",
                    account_type=PulseAccountType.CRYPTO,
                    holdings=[
                        _h("BTC", 0.08, 0.70),
                        _h("ETH", 3.5, 0.65),
                        _h("SOL", 25, 0.80),
                    ],
                    cash_balance=0,
                ),
            ],
            goals=UserGoals(
                emergency_fund_target=15000,
                emergency_fund_current=12000,
                retirement_age=60,
                monthly_savings_target=2500,
                risk_profile=RiskProfile.GROWTH,
                tax_bracket_pct=33,
                has_premium=True,
            ),
            created_at=datetime(2023, 1, 15),
        ),

        Portfolio(
            user_id="USR-003",
            display_name="Priya Sharma",
            age=32,
            province="ON",
            occupation="Marketing manager",
            accounts=[
                Account(
                    account_id="ACC-003-TFSA",
                    account_type=PulseAccountType.TFSA,
                    holdings=[
                        _h("VFV.TO", 150, 0.82),
                        _h("XEQT.TO", 100, 0.88),
                        _h("AAPL", 10, 0.78),
                    ],
                    cash_balance=1200.00,
                    contribution_room=3500.00,
                ),
                Account(
                    account_id="ACC-003-RRSP",
                    account_type=PulseAccountType.RRSP,
                    holdings=[
                        _h("XIC.TO", 300, 0.90),
                        _h("ZAG.TO", 400, 1.01),
                        _h("RY.TO", 20, 0.85),
                    ],
                    cash_balance=800.00,
                    contribution_room=22000.00,
                    employer_match_pct=3.0,
                ),
            ],
            goals=UserGoals(
                emergency_fund_target=12000,
                emergency_fund_current=10000,
                retirement_age=62,
                monthly_savings_target=1500,
                risk_profile=RiskProfile.MODERATE,
                tax_bracket_pct=29.3,
                has_premium=False,
            ),
            created_at=datetime(2022, 6, 1),
        ),

        Portfolio(
            user_id="USR-004",
            display_name="David & Sarah Kim",
            age=35,
            province="AB",
            occupation="Dual-income (engineer + nurse)",
            accounts=[
                Account(
                    account_id="ACC-004-TFSA-D",
                    account_type=PulseAccountType.TFSA,
                    holdings=[
                        _h("VFV.TO", 200, 0.80),
                        _h("SHOP.TO", 60, 0.70),
                        _h("NVDA", 15, 0.55),
                        _h("MSFT", 12, 0.82),
                    ],
                    cash_balance=2000.00,
                    contribution_room=5000.00,
                ),
                Account(
                    account_id="ACC-004-RRSP-D",
                    account_type=PulseAccountType.RRSP,
                    holdings=[
                        _h("XEQT.TO", 500, 0.78),
                        _h("XBB.TO", 300, 1.03),
                        _h("ENB.TO", 100, 0.88),
                    ],
                    cash_balance=3500.00,
                    contribution_room=35000.00,
                    employer_match_pct=5.0,
                ),
                Account(
                    account_id="ACC-004-NR",
                    account_type=PulseAccountType.NON_REGISTERED,
                    holdings=[
                        _h("GOOGL", 8, 0.75),
                        _h("AMZN", 10, 0.80),
                        _h("TD.TO", 50, 0.90),
                    ],
                    cash_balance=5000.00,
                ),
            ],
            goals=UserGoals(
                emergency_fund_target=25000,
                emergency_fund_current=25000,
                retirement_age=58,
                monthly_savings_target=4000,
                risk_profile=RiskProfile.GROWTH,
                tax_bracket_pct=33,
                has_premium=True,
            ),
            created_at=datetime(2021, 3, 1),
        ),

        Portfolio(
            user_id="USR-005",
            display_name="Michael Tremblay",
            age=42,
            province="QC",
            occupation="VP of Sales (tech company)",
            accounts=[
                Account(
                    account_id="ACC-005-TFSA",
                    account_type=PulseAccountType.TFSA,
                    holdings=[
                        _h("VFV.TO", 400, 0.72),
                        _h("AAPL", 30, 0.65),
                        _h("MSFT", 20, 0.70),
                        _h("NVDA", 25, 0.40),
                        _h("SHOP.TO", 80, 0.60),
                    ],
                    cash_balance=3000.00,
                    contribution_room=0.00,
                ),
                Account(
                    account_id="ACC-005-RRSP",
                    account_type=PulseAccountType.RRSP,
                    holdings=[
                        _h("XEQT.TO", 1000, 0.75),
                        _h("ZAG.TO", 800, 1.01),
                        _h("RY.TO", 60, 0.80),
                        _h("BNS.TO", 80, 0.85),
                        _h("CNR.TO", 25, 0.78),
                    ],
                    cash_balance=8000.00,
                    contribution_room=45000.00,
                    employer_match_pct=6.0,
                ),
                Account(
                    account_id="ACC-005-NR",
                    account_type=PulseAccountType.NON_REGISTERED,
                    holdings=[
                        _h("META", 12, 0.50),
                        _h("GOOGL", 15, 0.60),
                        _h("AMZN", 18, 0.68),
                        _h("BAM.TO", 100, 0.75),
                    ],
                    cash_balance=15000.00,
                ),
                Account(
                    account_id="ACC-005-CRYPTO",
                    account_type=PulseAccountType.CRYPTO,
                    holdings=[
                        _h("BTC", 0.25, 0.55),
                        _h("ETH", 8, 0.50),
                    ],
                    cash_balance=0,
                ),
            ],
            goals=UserGoals(
                emergency_fund_target=40000,
                emergency_fund_current=40000,
                retirement_age=55,
                monthly_savings_target=8000,
                risk_profile=RiskProfile.GROWTH,
                tax_bracket_pct=48.0,
                has_premium=True,
            ),
            created_at=datetime(2020, 1, 1),
        ),

        Portfolio(
            user_id="USR-006",
            display_name="Fatima Al-Hassan",
            age=29,
            province="ON",
            occupation="Product designer",
            accounts=[
                Account(
                    account_id="ACC-006-TFSA",
                    account_type=PulseAccountType.TFSA,
                    holdings=[
                        _h("VEQT.TO", 250, 0.90),
                        _h("SHOP.TO", 15, 0.85),
                    ],
                    cash_balance=600.00,
                    contribution_room=12000.00,
                ),
                Account(
                    account_id="ACC-006-FHSA",
                    account_type=PulseAccountType.FHSA,
                    holdings=[
                        _h("XIC.TO", 80, 0.95),
                        _h("ZAG.TO", 100, 1.00),
                    ],
                    cash_balance=200.00,
                    contribution_room=6000.00,
                ),
            ],
            goals=UserGoals(
                emergency_fund_target=10000,
                emergency_fund_current=6000,
                retirement_age=63,
                monthly_savings_target=1200,
                risk_profile=RiskProfile.MODERATE,
                tax_bracket_pct=26.0,
                has_premium=False,
            ),
            created_at=datetime(2023, 8, 1),
        ),

        Portfolio(
            user_id="USR-007",
            display_name="Robert Chen",
            age=55,
            province="BC",
            occupation="Senior partner (law firm)",
            accounts=[
                Account(
                    account_id="ACC-007-TFSA",
                    account_type=PulseAccountType.TFSA,
                    holdings=[
                        _h("XIC.TO", 500, 0.80),
                        _h("VFV.TO", 300, 0.75),
                        _h("RY.TO", 40, 0.70),
                        _h("ENB.TO", 80, 0.82),
                    ],
                    cash_balance=5000.00,
                    contribution_room=0.00,
                ),
                Account(
                    account_id="ACC-007-RRSP",
                    account_type=PulseAccountType.RRSP,
                    holdings=[
                        _h("ZAG.TO", 3000, 1.02),
                        _h("XBB.TO", 2000, 1.01),
                        _h("XEQT.TO", 1500, 0.72),
                        _h("BNS.TO", 200, 0.78),
                        _h("TD.TO", 150, 0.80),
                        _h("SU.TO", 100, 0.85),
                    ],
                    cash_balance=20000.00,
                    contribution_room=0.00,
                ),
                Account(
                    account_id="ACC-007-NR",
                    account_type=PulseAccountType.NON_REGISTERED,
                    holdings=[
                        _h("CNR.TO", 40, 0.65),
                        _h("BAM.TO", 200, 0.60),
                        _h("JPM", 25, 0.70),
                        _h("MSFT", 30, 0.55),
                    ],
                    cash_balance=30000.00,
                ),
            ],
            goals=UserGoals(
                emergency_fund_target=60000,
                emergency_fund_current=60000,
                retirement_age=60,
                monthly_savings_target=10000,
                risk_profile=RiskProfile.MODERATE,
                tax_bracket_pct=53.5,
                has_premium=True,
            ),
            created_at=datetime(2019, 6, 1),
        ),

        Portfolio(
            user_id="USR-008",
            display_name="Aiden O'Brien",
            age=26,
            province="NS",
            occupation="Freelance photographer",
            accounts=[
                Account(
                    account_id="ACC-008-TFSA",
                    account_type=PulseAccountType.TFSA,
                    holdings=[
                        _h("XEQT.TO", 50, 0.96),
                    ],
                    cash_balance=150.00,
                    contribution_room=18000.00,
                ),
                Account(
                    account_id="ACC-008-CRYPTO",
                    account_type=PulseAccountType.CRYPTO,
                    holdings=[
                        _h("BTC", 0.005, 1.20),
                        _h("SOL", 5, 1.10),
                    ],
                    cash_balance=0,
                ),
            ],
            goals=UserGoals(
                emergency_fund_target=5000,
                emergency_fund_current=800,
                retirement_age=65,
                monthly_savings_target=300,
                risk_profile=RiskProfile.AGGRESSIVE,
                tax_bracket_pct=20.5,
                has_premium=False,
            ),
            created_at=datetime(2024, 11, 1),
        ),

        Portfolio(
            user_id="USR-009",
            display_name="Dr. Linda Park",
            age=48,
            province="ON",
            occupation="Radiologist",
            accounts=[
                Account(
                    account_id="ACC-009-TFSA",
                    account_type=PulseAccountType.TFSA,
                    holdings=[
                        _h("VFV.TO", 250, 0.78),
                        _h("XIC.TO", 200, 0.85),
                        _h("AAPL", 20, 0.72),
                    ],
                    cash_balance=4000.00,
                    contribution_room=0.00,
                ),
                Account(
                    account_id="ACC-009-RRSP",
                    account_type=PulseAccountType.RRSP,
                    holdings=[
                        _h("XEQT.TO", 800, 0.76),
                        _h("ZAG.TO", 1500, 1.02),
                        _h("RY.TO", 50, 0.82),
                        _h("ENB.TO", 60, 0.88),
                    ],
                    cash_balance=12000.00,
                    contribution_room=15000.00,
                ),
                Account(
                    account_id="ACC-009-NR",
                    account_type=PulseAccountType.NON_REGISTERED,
                    holdings=[
                        _h("MSFT", 15, 0.68),
                        _h("GOOGL", 10, 0.72),
                        _h("TSLA", 5, 0.90),
                    ],
                    cash_balance=8000.00,
                ),
            ],
            goals=UserGoals(
                emergency_fund_target=30000,
                emergency_fund_current=30000,
                retirement_age=58,
                monthly_savings_target=6000,
                risk_profile=RiskProfile.MODERATE,
                tax_bracket_pct=53.5,
                has_premium=True,
            ),
            created_at=datetime(2020, 9, 1),
        ),

        Portfolio(
            user_id="USR-010",
            display_name="Tyler & Zoe Nguyen",
            age=31,
            province="MB",
            occupation="Dual-income (teacher + small business owner)",
            accounts=[
                Account(
                    account_id="ACC-010-TFSA-T",
                    account_type=PulseAccountType.TFSA,
                    holdings=[
                        _h("VEQT.TO", 180, 0.88),
                        _h("SHOP.TO", 10, 0.80),
                    ],
                    cash_balance=400.00,
                    contribution_room=8000.00,
                ),
                Account(
                    account_id="ACC-010-RRSP",
                    account_type=PulseAccountType.RRSP,
                    holdings=[
                        _h("XEQT.TO", 150, 0.82),
                        _h("ZAG.TO", 200, 1.01),
                    ],
                    cash_balance=600.00,
                    contribution_room=25000.00,
                    employer_match_pct=3.0,
                ),
                Account(
                    account_id="ACC-010-RESP",
                    account_type=PulseAccountType.RESP,
                    holdings=[
                        _h("XEQT.TO", 100, 0.90),
                        _h("XBB.TO", 80, 1.02),
                    ],
                    cash_balance=300.00,
                ),
                Account(
                    account_id="ACC-010-CRYPTO",
                    account_type=PulseAccountType.CRYPTO,
                    holdings=[
                        _h("BTC", 0.03, 0.85),
                        _h("ETH", 1.5, 0.78),
                    ],
                    cash_balance=0,
                ),
            ],
            goals=UserGoals(
                emergency_fund_target=15000,
                emergency_fund_current=9000,
                retirement_age=62,
                monthly_savings_target=2000,
                risk_profile=RiskProfile.MODERATE,
                tax_bracket_pct=29.3,
                has_premium=False,
            ),
            created_at=datetime(2022, 11, 1),
        ),
    ]

    for p in portfolios:
        _recalculate_weights(p)

    return portfolios


def _recalculate_weights(portfolio: Portfolio) -> None:
    total = portfolio.total_value
    if total == 0:
        return
    for account in portfolio.accounts:
        for holding in account.holdings:
            holding.market_value = round(holding.quantity * holding.current_price, 2)
            holding.weight_pct = round(holding.market_value / total * 100, 2)
            if holding.avg_cost > 0:
                holding.unrealized_gain_pct = round(
                    (holding.current_price - holding.avg_cost) / holding.avg_cost * 100, 2
                )
