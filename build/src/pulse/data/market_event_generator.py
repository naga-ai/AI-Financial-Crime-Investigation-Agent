"""Generates 50 realistic financial events over a 90-day window.

Events include biweekly paychecks, earnings reports, BoC rate decisions,
market drops, dividend payments, and a subscription audit trigger. Each
event references real tickers and maps to affected users.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta

from src.pulse.models import EventPriority, EventType, MarketEvent, Portfolio


def generate_events(portfolios: list[Portfolio]) -> list[MarketEvent]:
    """Generate 50 realistic financial events over 90 days."""

    base_date = datetime(2026, 1, 5)
    events: list[MarketEvent] = []

    user_holdings_map: dict[str, set[str]] = {}
    for p in portfolios:
        tickers = set()
        for a in p.accounts:
            for h in a.holdings:
                tickers.add(h.ticker)
        user_holdings_map[p.user_id] = tickers

    def _affected_users(tickers: list[str]) -> list[str]:
        return [
            uid for uid, held in user_holdings_map.items()
            if any(t in held for t in tickers)
        ]

    # --- Biweekly paychecks (20 events: 10 users x 2 pay periods) ---
    paycheck_amounts = {
        "USR-001": 1200, "USR-002": 4800, "USR-003": 3600,
        "USR-004": 7200, "USR-005": 12000, "USR-006": 3200,
        "USR-007": 15000, "USR-008": 1800, "USR-009": 9500,
        "USR-010": 5000,
    }
    for i, (uid, amount) in enumerate(paycheck_amounts.items()):
        for pay_period in range(2):
            day_offset = 14 * pay_period + (i % 3)
            events.append(MarketEvent(
                event_id=f"EVT-PAY-{uid}-{pay_period+1}",
                event_type=EventType.PAYCHECK,
                priority=EventPriority.LOW,
                title=f"Paycheck deposited — ${amount:,.0f}",
                description=(
                    f"Direct deposit of ${amount:,.0f} received. "
                    f"Optimal allocation analysis available."
                ),
                affected_tickers=[],
                affected_users=[uid],
                data={
                    "amount": amount,
                    "currency": "CAD",
                    "source": "employer_direct_deposit",
                    "frequency": "biweekly",
                },
                timestamp=base_date + timedelta(days=day_offset),
            ))

    # --- Earnings reports (5 events) ---
    earnings_events = [
        {
            "ticker": "SHOP.TO", "date_offset": 12,
            "title": "Shopify Q4 2025 Earnings Beat",
            "eps_actual": 0.44, "eps_estimate": 0.39,
            "revenue_actual": "2.36B", "revenue_estimate": "2.28B",
            "surprise_pct": 12.8,
            "guidance": "Raised FY2026 guidance; GMV growth accelerating",
        },
        {
            "ticker": "RY.TO", "date_offset": 25,
            "title": "Royal Bank Q1 2026 Earnings",
            "eps_actual": 3.18, "eps_estimate": 3.05,
            "revenue_actual": "15.2B", "revenue_estimate": "14.8B",
            "surprise_pct": 4.3,
            "guidance": "Stable credit quality; wealth management growing 11%",
        },
        {
            "ticker": "AAPL", "date_offset": 30,
            "title": "Apple Q1 FY2026 Earnings",
            "eps_actual": 2.42, "eps_estimate": 2.35,
            "revenue_actual": "128.2B", "revenue_estimate": "125.8B",
            "surprise_pct": 3.0,
            "guidance": "Services revenue at record; iPhone 17 cycle strong",
        },
        {
            "ticker": "NVDA", "date_offset": 48,
            "title": "NVIDIA Q4 FY2026 Earnings Blowout",
            "eps_actual": 0.89, "eps_estimate": 0.73,
            "revenue_actual": "42.5B", "revenue_estimate": "38.1B",
            "surprise_pct": 21.9,
            "guidance": "Blackwell Ultra demand exceeding supply; raised Q1 guidance 20%",
        },
        {
            "ticker": "ENB.TO", "date_offset": 55,
            "title": "Enbridge Q4 2025 Earnings",
            "eps_actual": 0.68, "eps_estimate": 0.71,
            "revenue_actual": "13.8B", "revenue_estimate": "14.1B",
            "surprise_pct": -4.2,
            "guidance": "Maintained dividend; energy transition investments on track",
        },
    ]
    for e in earnings_events:
        events.append(MarketEvent(
            event_id=f"EVT-EARN-{e['ticker'].replace('.', '')}",
            event_type=EventType.EARNINGS_REPORT,
            priority=EventPriority.MEDIUM if abs(e["surprise_pct"]) < 10 else EventPriority.HIGH,
            title=e["title"],
            description=(
                f"EPS: ${e['eps_actual']} vs ${e['eps_estimate']} est "
                f"({'+' if e['surprise_pct']>0 else ''}{e['surprise_pct']}% surprise). "
                f"Revenue: {e['revenue_actual']} vs {e['revenue_estimate']} est. "
                f"{e['guidance']}"
            ),
            affected_tickers=[e["ticker"]],
            affected_users=_affected_users([e["ticker"]]),
            data={
                "eps_actual": e["eps_actual"],
                "eps_estimate": e["eps_estimate"],
                "revenue_actual": e["revenue_actual"],
                "surprise_pct": e["surprise_pct"],
                "guidance": e["guidance"],
            },
            timestamp=base_date + timedelta(days=e["date_offset"]),
        ))

    # --- BoC rate decisions (2 events) ---
    events.append(MarketEvent(
        event_id="EVT-BOC-JAN",
        event_type=EventType.BOC_RATE_DECISION,
        priority=EventPriority.MEDIUM,
        title="Bank of Canada holds rate at 3.25%",
        description=(
            "BoC held overnight rate steady at 3.25%. Statement noted inflation "
            "returning to 2% target range but flagged housing market risks. "
            "Next decision: March 12, 2026."
        ),
        affected_tickers=["ZAG.TO", "XBB.TO", "RY.TO", "TD.TO", "BNS.TO"],
        affected_users=[p.user_id for p in portfolios],
        data={
            "rate": 3.25, "previous_rate": 3.25,
            "change_bps": 0, "next_decision": "2026-03-12",
        },
        timestamp=base_date + timedelta(days=22),
    ))
    events.append(MarketEvent(
        event_id="EVT-BOC-MAR",
        event_type=EventType.BOC_RATE_DECISION,
        priority=EventPriority.HIGH,
        title="Bank of Canada cuts rate to 3.00%",
        description=(
            "BoC cut overnight rate by 25bps to 3.00%, citing moderating inflation "
            "and slower employment growth. Bond prices expected to rise. "
            "Mortgage rates likely to decline."
        ),
        affected_tickers=["ZAG.TO", "XBB.TO", "RY.TO", "TD.TO", "BNS.TO"],
        affected_users=[p.user_id for p in portfolios],
        data={
            "rate": 3.00, "previous_rate": 3.25,
            "change_bps": -25, "next_decision": "2026-04-15",
        },
        timestamp=base_date + timedelta(days=66),
    ))

    # --- Market drops (3 events) ---
    market_drops = [
        {
            "date_offset": 18,
            "title": "Tech Sell-Off: NASDAQ drops 3.8%",
            "description": (
                "Broad tech sell-off driven by rising Treasury yields and rotation "
                "into value. Semiconductor stocks hit hardest (-5.2%). Canadian "
                "tech names following US peers lower."
            ),
            "tickers": ["SHOP.TO", "NVDA", "AAPL", "MSFT", "GOOGL", "META", "TSLA"],
            "drop_pct": -3.8,
            "index": "NASDAQ",
        },
        {
            "date_offset": 42,
            "title": "TSX Energy Sector Down 4.1% on Oil Price Drop",
            "description": (
                "WTI crude fell below $65/barrel on OPEC+ production increase "
                "concerns. Canadian energy names under pressure. Enbridge and "
                "Suncor leading declines."
            ),
            "tickers": ["ENB.TO", "SU.TO"],
            "drop_pct": -4.1,
            "index": "S&P/TSX Energy",
        },
        {
            "date_offset": 75,
            "title": "Global Markets Slide on US Tariff Escalation",
            "description": (
                "S&P 500 down 2.9%, TSX down 2.3% as new tariff threats rattle "
                "markets. Canadian financials exposed to cross-border trade. "
                "Safe haven assets (bonds, gold) rallying."
            ),
            "tickers": ["VFV.TO", "XIC.TO", "XEQT.TO", "VEQT.TO", "RY.TO", "TD.TO", "BNS.TO"],
            "drop_pct": -2.9,
            "index": "S&P 500",
        },
    ]
    for md in market_drops:
        events.append(MarketEvent(
            event_id=f"EVT-DROP-{md['date_offset']}",
            event_type=EventType.MARKET_DROP,
            priority=EventPriority.HIGH,
            title=md["title"],
            description=md["description"],
            affected_tickers=md["tickers"],
            affected_users=_affected_users(md["tickers"]),
            data={
                "drop_pct": md["drop_pct"],
                "index": md["index"],
                "trigger": md["description"][:80],
            },
            timestamp=base_date + timedelta(days=md["date_offset"]),
        ))

    # --- Dividend payments (2 events) ---
    events.append(MarketEvent(
        event_id="EVT-DIV-ENB",
        event_type=EventType.DIVIDEND_PAYMENT,
        priority=EventPriority.LOW,
        title="Enbridge dividend: $0.9425/share",
        description=(
            "Quarterly dividend of $0.9425 per share. Ex-dividend date passed. "
            "Current yield: 6.6%. 29th consecutive year of dividend increases."
        ),
        affected_tickers=["ENB.TO"],
        affected_users=_affected_users(["ENB.TO"]),
        data={"dividend_per_share": 0.9425, "yield_pct": 6.6, "frequency": "quarterly"},
        timestamp=base_date + timedelta(days=35),
    ))
    events.append(MarketEvent(
        event_id="EVT-DIV-RY",
        event_type=EventType.DIVIDEND_PAYMENT,
        priority=EventPriority.LOW,
        title="Royal Bank dividend: $1.48/share",
        description=(
            "Quarterly dividend of $1.48 per share. Record date Feb 25. "
            "Current yield: 3.5%. Payout ratio remains healthy at 47%."
        ),
        affected_tickers=["RY.TO"],
        affected_users=_affected_users(["RY.TO"]),
        data={"dividend_per_share": 1.48, "yield_pct": 3.5, "frequency": "quarterly"},
        timestamp=base_date + timedelta(days=50),
    ))

    # --- Subscription audit (1 event) ---
    events.append(MarketEvent(
        event_id="EVT-SUB-AUDIT",
        event_type=EventType.SUBSCRIPTION_AUDIT,
        priority=EventPriority.LOW,
        title="Premium subscription value check",
        description=(
            "Monthly review of your Wealthsimple Premium benefits. You saved "
            "$42 in FX fees this month on US stock trades. Your instant deposits "
            "were used 8 times."
        ),
        affected_tickers=[],
        affected_users=["USR-002", "USR-004", "USR-005", "USR-007", "USR-009"],
        data={
            "fx_savings": 42.00,
            "instant_deposit_uses": 8,
            "premium_cost": 10.00,
            "net_value": 32.00,
        },
        timestamp=base_date + timedelta(days=60),
    ))

    events.sort(key=lambda e: e.timestamp or base_date)
    return events
