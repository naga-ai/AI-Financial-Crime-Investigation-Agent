"""FINTRAC-compliant report templates and prompts.

Structures follow the actual FINTRAC STR form sections:
Subject Information, Transaction Details, Suspicious Activity Description,
and Indicators Matched. These templates ensure every AI-generated report
meets the regulatory standard for filing.
"""

from __future__ import annotations

SYSTEM_PROMPT = """You are a senior AML compliance analyst at Wealthsimple, Canada's largest fintech.
You are writing a Suspicious Transaction Report (STR) narrative for submission to FINTRAC
(Financial Transactions and Reports Analysis Centre of Canada).

Your narrative must be:
- Factual and evidence-based (cite specific transactions, dates, amounts)
- Written in professional compliance language
- Structured per FINTRAC guidelines
- Clear about what makes this activity suspicious
- Objective -- describe patterns, not intent (intent is for human reviewers to assess)

Do NOT speculate about the client's motives. Present the facts and indicators only."""

REPORT_GENERATION_PROMPT = """Generate a FINTRAC Suspicious Transaction Report narrative based on the following investigation findings.

## Investigation Summary

**Alert ID:** {alert_id}
**Alert Type:** {alert_type}
**Client:** {client_name} (ID: {client_id})

## Subject Information
- **Date of Birth:** {dob}
- **Occupation:** {occupation}
- **Income Range:** {income_range}
- **Province:** {province}
- **Account Open Date:** {account_open_date}
- **KYC Status:** {kyc_status}
- **Risk Profile:** {risk_profile}
- **PEP Status:** {pep_status}
- **Accounts:** {accounts}

## Investigation Findings

**Risk Score:** {risk_score}/100 ({risk_level})
**Confidence:** {confidence}%

### Risk Factors Identified:
{risk_factors}

### Typology Matches:
{typology_matches}

### Transaction Velocity Analysis:
{velocity_analysis}

### Watchlist Screening Results:
{watchlist_results}

### Entity Network Analysis:
{entity_network}

{crypto_section}

### Behavioral Baseline Deviation:
{behavioral_baseline}

## Key Transactions:
{key_transactions}

---

Write the STR narrative in the following structure:

1. **SUBJECT INFORMATION** - Brief summary of the account holder
2. **SUSPICIOUS ACTIVITY DESCRIPTION** - Detailed narrative of what was observed (2-3 paragraphs)
3. **INDICATORS MATCHED** - List specific FINTRAC ML/TF indicators with references
4. **TRANSACTION SUMMARY** - Key transactions cited as evidence (table format)
5. **RISK ASSESSMENT** - Overall risk evaluation and recommendation
6. **RECOMMENDED ACTION** - File STR / Escalate / Close with justification"""

CRYPTO_SECTION_TEMPLATE = """### Crypto Activity Analysis:
- Privacy coin transactions: {privacy_coin_count}
- External wallet withdrawals: {external_wallet_count}
- Crypto swaps: {swap_count}
- Total crypto volume: ${crypto_volume:,.2f} CAD
- Risk indicators: {crypto_indicators}"""


def format_report_prompt(investigation_state: dict) -> str:
    """Format the report generation prompt with investigation findings."""
    profile = investigation_state.get("client_profile", {})
    summary = investigation_state.get("account_summary", {})
    velocity = investigation_state.get("velocity_analysis", {})
    watchlist = investigation_state.get("watchlist_results", {})
    network = investigation_state.get("entity_network", {})
    crypto = investigation_state.get("crypto_analysis", {})
    baseline = investigation_state.get("behavioral_baseline", {})
    typologies = investigation_state.get("typology_matches", [])
    risk_factors = investigation_state.get("risk_factors", [])
    txn_history = investigation_state.get("transaction_history", [])

    risk_factors_text = "\n".join(f"- {rf}" for rf in risk_factors) or "- None identified"

    typology_text = ""
    for tm in typologies:
        typology_text += (
            f"- **{tm.get('typology_name', 'Unknown')}** "
            f"(match: {tm.get('match_score', 0):.0%}) -- "
            f"{tm.get('description', '')}\n"
            f"  FINTRAC ref: {tm.get('fintrac_reference', 'N/A')}\n"
        )
    typology_text = typology_text or "- No known typology matches"

    velocity_text = "Not available"
    if velocity and not velocity.get("error"):
        v = velocity
        velocity_text = (
            f"Baseline: {v.get('baseline', {}).get('avg_daily_transactions', 'N/A')} txns/day, "
            f"${v.get('baseline', {}).get('avg_daily_volume_cad', 'N/A'):,.0f}/day\n"
            f"Recent 7d: {v.get('recent_7d', {}).get('avg_daily_transactions', 'N/A')} txns/day, "
            f"${v.get('recent_7d', {}).get('avg_daily_volume_cad', 'N/A'):,.0f}/day\n"
            f"Velocity ratio: {v.get('velocity_ratios', {}).get('transaction_count', 'N/A')}x count, "
            f"{v.get('velocity_ratios', {}).get('transaction_volume', 'N/A')}x volume\n"
            f"Anomaly: {v.get('anomaly_description', 'N/A')}"
        )

    watchlist_text = "No matches found"
    if watchlist.get("total_matches", 0) > 0:
        matches = watchlist.get("matches", [])
        watchlist_text = "\n".join(
            f"- **{m.get('type', 'Unknown')}**: {m.get('details', '')} (Source: {m.get('source', 'N/A')})"
            for m in matches
        )

    network_text = (
        f"Network size: {network.get('network_size', 0)} connected entities\n"
        f"External transfers: {network.get('external_transfers', {}).get('count', 0)} "
        f"totaling ${network.get('external_transfers', {}).get('total_cad', 0):,.0f}\n"
    )
    for ri in network.get("risk_indicators", []):
        network_text += f"- {ri}\n"

    crypto_section = ""
    if crypto and crypto.get("has_crypto_activity"):
        crypto_section = CRYPTO_SECTION_TEMPLATE.format(
            privacy_coin_count=crypto.get("privacy_coin_transactions", 0),
            external_wallet_count=crypto.get("external_wallet_withdrawals", 0),
            swap_count=crypto.get("crypto_swaps", 0),
            crypto_volume=crypto.get("total_crypto_volume_cad", 0),
            crypto_indicators="\n  - ".join(crypto.get("risk_indicators", ["None"])),
        )

    baseline_text = "Insufficient history"
    if baseline and not baseline.get("error"):
        b = baseline.get("amount_baseline", {})
        baseline_text = (
            f"Mean transaction: ${b.get('mean', 0):,.2f} | "
            f"Median: ${b.get('median', 0):,.2f} | "
            f"95th percentile: ${b.get('p95', 0):,.2f} | "
            f"Max: ${b.get('max', 0):,.2f}"
        )

    key_txns = txn_history[-10:] if txn_history else []
    txn_lines = []
    for t in key_txns:
        txn_lines.append(
            f"| {t.get('timestamp', '')[:10]} | {t.get('type', '')} | "
            f"${t.get('amount_cad', 0):,.2f} {t.get('currency', 'CAD')} | "
            f"{t.get('method', '')} | {t.get('description', '')} |"
        )
    key_txn_text = (
        "| Date | Type | Amount | Method | Description |\n"
        "|------|------|--------|--------|-------------|\n"
        + "\n".join(txn_lines)
    ) if txn_lines else "No transactions available"

    accounts_text = ", ".join(
        f"{a.get('type', 'unknown').upper()} (${a.get('balance_cad', 0):,.0f})"
        for a in profile.get("accounts", [])
    )

    return REPORT_GENERATION_PROMPT.format(
        alert_id=investigation_state.get("alert_id", "N/A"),
        alert_type=investigation_state.get("alert_type", "N/A"),
        client_name=profile.get("full_name", "Unknown"),
        client_id=investigation_state.get("client_id", "N/A"),
        dob=profile.get("date_of_birth", "N/A"),
        occupation=profile.get("occupation", "N/A"),
        income_range=profile.get("income_range", "N/A"),
        province=profile.get("province", "N/A"),
        account_open_date=profile.get("account_open_date", "N/A"),
        kyc_status=profile.get("kyc_status", "N/A"),
        risk_profile=profile.get("risk_profile", "N/A"),
        pep_status="Yes -- Enhanced Due Diligence required" if profile.get("is_pep") else "No",
        accounts=accounts_text,
        risk_score=investigation_state.get("risk_score", 0),
        risk_level=investigation_state.get("risk_level", "unknown"),
        confidence=round(investigation_state.get("confidence", 0) * 100),
        risk_factors=risk_factors_text,
        typology_matches=typology_text,
        velocity_analysis=velocity_text,
        watchlist_results=watchlist_text,
        entity_network=network_text,
        crypto_section=crypto_section,
        behavioral_baseline=baseline_text,
        key_transactions=key_txn_text,
    )
