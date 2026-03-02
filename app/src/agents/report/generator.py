"""STR Report Generation Agent.

Generates FINTRAC-compliant Suspicious Transaction Report narratives
from investigation findings. Uses LLM for narrative quality with
structured output, and falls back to template-based generation
when no API key is configured.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from src.config import OPENAI_API_KEY, LLM_MODEL, LLM_TEMPERATURE
from src.data.models import (
    HumanDecision,
    RecommendedAction,
    STRReport,
    SuspicionType,
)
from src.agents.report.templates import SYSTEM_PROMPT, format_report_prompt


def _get_rag_context(investigation_state: dict) -> str:
    """Retrieve regulatory context via RAG to ground the report."""
    try:
        rag_ctx = investigation_state.get("rag_context", {})
        if rag_ctx and rag_ctx.get("context_text"):
            return rag_ctx["context_text"]

        from src.rag.retriever import get_rag_engine
        rag = get_rag_engine()

        alert_type = investigation_state.get("alert_type", "")
        context = rag.retrieve_for_alert(alert_type)
        str_guidance = rag.retrieve_str_guidance()

        parts = []
        if context.context_text:
            parts.append(context.context_text)
        if str_guidance.context_text:
            parts.append(str_guidance.context_text)
        return "\n\n".join(parts)
    except Exception:
        return ""


def _generate_with_llm(investigation_state: dict) -> str:
    """Generate report narrative using OpenAI API with RAG context."""
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import SystemMessage, HumanMessage

    llm = ChatOpenAI(
        model=LLM_MODEL,
        temperature=LLM_TEMPERATURE,
        api_key=OPENAI_API_KEY,
    )

    rag_context = _get_rag_context(investigation_state)

    prompt = format_report_prompt(investigation_state)
    if rag_context:
        prompt = (
            f"## Relevant FINTRAC Regulatory Guidance (Retrieved via RAG)\n\n"
            f"{rag_context}\n\n"
            f"---\n\n"
            f"Use the regulatory guidance above to cite specific FINTRAC indicators "
            f"and compliance requirements in your narrative. Reference the exact "
            f"indicator names and regulatory sections where applicable.\n\n"
            f"{prompt}"
        )

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=prompt),
    ]

    response = llm.invoke(messages)
    return response.content


def _generate_template_based(investigation_state: dict) -> str:
    """Generate report using templates (no LLM needed)."""
    profile = investigation_state.get("client_profile", {})
    risk_factors = investigation_state.get("risk_factors", [])
    typologies = investigation_state.get("typology_matches", [])
    watchlist = investigation_state.get("watchlist_results", {})
    velocity = investigation_state.get("velocity_analysis", {})
    crypto = investigation_state.get("crypto_analysis", {})
    network = investigation_state.get("entity_network", {})
    baseline = investigation_state.get("behavioral_baseline", {})
    alert_type = investigation_state.get("alert_type", "unknown")
    risk_score = investigation_state.get("risk_score", 0)
    risk_level = investigation_state.get("risk_level", "unknown")
    confidence = investigation_state.get("confidence", 0)
    txn_history = investigation_state.get("transaction_history", [])

    # --- Subject Information ---
    subject = (
        f"## 1. SUBJECT INFORMATION\n\n"
        f"**Name:** {profile.get('full_name', 'Unknown')}\n"
        f"**Date of Birth:** {profile.get('date_of_birth', 'N/A')}\n"
        f"**Occupation:** {profile.get('occupation', 'N/A')}\n"
        f"**Declared Income:** {profile.get('income_range', 'N/A')}\n"
        f"**Province:** {profile.get('province', 'N/A')}\n"
        f"**Account Opened:** {profile.get('account_open_date', 'N/A')}\n"
        f"**KYC Status:** {profile.get('kyc_status', 'N/A')}\n"
        f"**Risk Profile:** {profile.get('risk_profile', 'N/A')}\n"
        f"**PEP Status:** {'Yes' if profile.get('is_pep') else 'No'}\n"
        f"**Total Balance:** ${profile.get('total_balance_cad', 0):,.2f} CAD\n"
    )

    accounts = profile.get("accounts", [])
    if accounts:
        subject += "\n**Accounts:**\n"
        for a in accounts:
            subject += f"- {a.get('type', 'unknown').upper()}: ${a.get('balance_cad', 0):,.2f} CAD (opened {a.get('opened_at', 'N/A')})\n"

    # --- Suspicious Activity Description ---
    alert_descriptions = {
        "structuring": "Multiple deposits just below the FINTRAC $10,000 reporting threshold were detected within a short time window, consistent with structuring/smurfing patterns intended to avoid mandatory transaction reporting.",
        "rapid_movement": "A large deposit was received and rapidly moved out of the account through withdrawal or transfer, with minimal holding period. This flow-through pattern is consistent with layering activity.",
        "crypto_layering": "The subject deposited fiat currency and rapidly converted to cryptocurrency, then swapped to privacy-enhanced coins (Monero/Zcash) before withdrawing to an external wallet. This pattern is consistent with crypto layering to obscure the transaction trail.",
        "round_tripping": "Repeated buy-sell cycles of the same asset were observed with minimal price differences, followed by withdrawal. These transactions appear to lack economic purpose and are consistent with wash trading patterns.",
        "velocity_spike": "A significant spike in transaction frequency and volume was detected, far exceeding the subject's established behavioral baseline. This sudden change in activity pattern warrants investigation.",
        "dormant_activation": "The account was dormant for an extended period before receiving a substantial deposit. Reactivation of dormant accounts with immediate high-value activity is a recognized ML indicator.",
        "geographic_anomaly": "Transactions were initiated from IP addresses geographically inconsistent with the subject's profile, suggesting potential unauthorized access or deliberate obfuscation of transaction origin.",
        "third_party_pattern": "Multiple wire transfers to and from unrelated third parties were detected, consistent with funnel account activity where the account is used to aggregate and redistribute funds.",
        "pep_sanctions_hit": "The subject has been identified as a Politically Exposed Person (PEP). Significant financial activity by PEPs requires Enhanced Due Diligence under PCMLTFA.",
        "age_amount_mismatch": "Transaction amounts are significantly inconsistent with the subject's declared income and occupation, raising concerns about undisclosed sources of funds.",
    }

    activity = (
        f"\n## 2. SUSPICIOUS ACTIVITY DESCRIPTION\n\n"
        f"{alert_descriptions.get(alert_type, 'Suspicious transaction patterns were detected that warrant further review.')}\n\n"
    )

    if velocity and not velocity.get("error"):
        v_ratio = velocity.get("velocity_ratios", {})
        if velocity.get("anomaly_detected"):
            activity += (
                f"Transaction velocity analysis reveals that recent activity is "
                f"{v_ratio.get('transaction_count', 1):.1f}x the baseline frequency and "
                f"{v_ratio.get('transaction_volume', 1):.1f}x the baseline volume, "
                f"indicating a significant departure from established behavior.\n\n"
            )

    if crypto and crypto.get("has_crypto_activity") and crypto.get("risk_level") in ("high", "medium"):
        activity += (
            f"Crypto analysis identified {crypto.get('privacy_coin_transactions', 0)} privacy coin transaction(s) "
            f"and {crypto.get('external_wallet_withdrawals', 0)} withdrawal(s) to external wallets, "
            f"totaling ${crypto.get('total_crypto_volume_cad', 0):,.2f} CAD in crypto activity. "
        )
        for ind in crypto.get("risk_indicators", []):
            activity += f"{ind}. "
        activity += "\n\n"

    if network and network.get("network_size", 0) > 2:
        activity += (
            f"Entity network analysis reveals connections to {network.get('network_size', 0)} "
            f"other entities through shared identifiers.\n\n"
        )

    # --- Indicators Matched (enriched with RAG regulatory context) ---
    indicators = "\n## 3. FINTRAC INDICATORS MATCHED\n\n"
    for tm in typologies:
        indicators += (
            f"- **{tm.get('typology_name', 'Unknown')}** (match confidence: {tm.get('match_score', 0):.0%})\n"
            f"  Reference: {tm.get('fintrac_reference', 'N/A')}\n"
        )
    if watchlist.get("total_matches", 0) > 0:
        for m in watchlist.get("matches", []):
            indicators += f"- **{m.get('type', 'Unknown')}**: {m.get('details', '')} (Source: {m.get('source', 'N/A')})\n"
    if not typologies and watchlist.get("total_matches", 0) == 0:
        indicators += "- Risk score elevated based on combined behavioral indicators\n"

    rag_ctx = investigation_state.get("rag_context", {})
    rag_sources = rag_ctx.get("sources", [])
    if rag_sources:
        indicators += "\n**Regulatory References (RAG-Retrieved):**\n"
        for src in rag_sources:
            indicators += f"- {src.get('title', 'Unknown')} [{src.get('category', '')}] (relevance: {src.get('relevance', 0):.0%})\n"

    # --- Transaction Summary ---
    txn_summary = "\n## 4. KEY TRANSACTIONS\n\n"
    txn_summary += "| Date | Type | Amount | Currency | Method | Description |\n"
    txn_summary += "|------|------|--------|----------|--------|-------------|\n"
    for t in (txn_history or [])[-15:]:
        txn_summary += (
            f"| {t.get('timestamp', '')[:10]} | {t.get('type', '')} | "
            f"${t.get('amount_cad', 0):,.2f} | {t.get('currency', 'CAD')} | "
            f"{t.get('method', '')} | {t.get('description', '')} |\n"
        )

    # --- Risk Assessment ---
    assessment = (
        f"\n## 5. RISK ASSESSMENT\n\n"
        f"**Overall Risk Score:** {risk_score}/100 ({risk_level.upper()})\n"
        f"**Confidence Level:** {confidence:.0%}\n\n"
        f"**Key Risk Factors:**\n"
    )
    for rf in risk_factors:
        assessment += f"- {rf}\n"

    # --- Recommended Action ---
    action_map = {
        "file_str": "FILE SUSPICIOUS TRANSACTION REPORT with FINTRAC. The combination of indicators and evidence warrants mandatory reporting under the Proceeds of Crime (Money Laundering) and Terrorist Financing Act (PCMLTFA).",
        "escalate": "ESCALATE to Senior AML Analyst for enhanced review. Multiple indicators present but additional context needed before filing determination.",
        "close": "CLOSE investigation. While the alert was triggered by rule-based monitoring, the investigation did not find sufficient indicators to warrant STR filing at this time. Document findings for future reference.",
    }
    recommended = investigation_state.get("recommended_action", "close")
    recommendation = (
        f"\n## 6. RECOMMENDED ACTION\n\n"
        f"**{action_map.get(recommended, 'Review required.')}**\n\n"
        f"*This report was generated by the AI-Native AML Investigation System. "
        f"Final filing decision must be made by a qualified compliance officer "
        f"in accordance with PCMLTFA obligations.*"
    )

    return subject + activity + indicators + txn_summary + assessment + recommendation


def generate_str_report(
    investigation_state: dict,
    use_llm: bool = True,
) -> STRReport:
    """Generate a complete STR report from investigation findings.

    Args:
        investigation_state: Completed investigation state from the LangGraph agent.
        use_llm: Whether to use LLM for narrative generation. Falls back to
                 template-based if False or if no API key is configured.
    """
    if use_llm and OPENAI_API_KEY:
        try:
            narrative = _generate_with_llm(investigation_state)
        except Exception as e:
            print(f"LLM generation failed ({e}), falling back to template-based")
            narrative = _generate_template_based(investigation_state)
    else:
        narrative = _generate_template_based(investigation_state)

    profile = investigation_state.get("client_profile", {})
    risk_score = investigation_state.get("risk_score", 0)
    recommended = investigation_state.get("recommended_action", "close")
    typologies = investigation_state.get("typology_matches", [])

    risk_indicators = []
    for tm in typologies:
        if tm.get("fintrac_reference"):
            risk_indicators.append(tm["fintrac_reference"])
    for rf in investigation_state.get("risk_factors", []):
        if "FINTRAC" in rf or "indicator" in rf.lower():
            risk_indicators.append(rf)

    txn_history = investigation_state.get("transaction_history", [])
    txn_summary = [
        {
            "date": t.get("timestamp", "")[:10],
            "type": t.get("type", ""),
            "amount_cad": t.get("amount_cad", 0),
            "currency": t.get("currency", "CAD"),
            "method": t.get("method", ""),
        }
        for t in (txn_history or [])[-10:]
    ]

    report = STRReport(
        report_id=f"STR-{uuid.uuid4().hex[:10].upper()}",
        investigation_id=investigation_state.get("alert_id", ""),
        narrative=narrative,
        suspicion_type=SuspicionType.MONEY_LAUNDERING,
        subject_info={
            "name": profile.get("full_name", "Unknown"),
            "dob": profile.get("date_of_birth", ""),
            "occupation": profile.get("occupation", ""),
            "income_range": profile.get("income_range", ""),
            "province": profile.get("province", ""),
            "accounts": profile.get("accounts", []),
        },
        transaction_summary=txn_summary,
        risk_indicators=risk_indicators,
        risk_score=risk_score,
        recommended_filing=recommended == "file_str",
        human_decision=HumanDecision.PENDING,
        created_at=datetime.now(),
    )

    return report
