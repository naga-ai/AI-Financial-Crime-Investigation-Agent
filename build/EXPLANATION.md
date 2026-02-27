# AI-Native Financial Crime Investigation Agent

## What I Built and Why

I built an AI-native system that reimagines how Wealthsimple's compliance team investigates money laundering alerts. Today, financial crime investigators manually review hundreds of alerts per week -- pulling client profiles, analyzing transaction patterns, checking sanctions lists, and writing Suspicious Transaction Reports for FINTRAC. About 80% of these alerts are false positives. The manual work is repetitive, slow, and expensive.

Instead of bolting AI onto this existing workflow, I designed the system from scratch with AI at the core. The result is a four-agent pipeline that processes an alert from detection to FINTRAC-ready report in under 20ms, with a human compliance officer making the final filing decision.

## How It Works

**Agent 1 (Triage)** uses an XGBoost classifier trained on 24 engineered features -- transaction velocity, structuring indicators, crypto privacy coin usage, PEP status, income-to-amount ratios -- to separate true risks from noise. It auto-closes ~80% of false positives with high confidence, freeing analysts to focus on cases that matter.

**Agent 2 (Investigation)** is a LangGraph state machine that mirrors a Level 2 analyst's workflow. It gathers client context, analyzes transaction patterns, screens watchlists (PEP/sanctions), matches against known ML typologies, and conditionally routes crypto cases through deeper analysis. Nine simulated tools provide the data a real system would pull from Wealthsimple's internal APIs. Each tool call is traced with span-level observability.

**Agent 3 (Report)** generates FINTRAC-compliant STR narratives. Using structured templates aligned to real STR formatting requirements -- subject information, suspicious activity description, matched FINTRAC indicators, key transaction evidence, risk assessment, and recommended action -- it produces reports ready for human review. When an OpenAI API key is configured, LangChain + GPT-4o-mini generates natural-language narratives; otherwise, template-based generation works fully offline.

**Agent 4 (Pattern Discovery)** runs K-Means or DBSCAN clustering on completed investigations to surface emerging fraud typologies. In testing, it identified five distinct clusters including a privacy coin pattern and a watchlist-hit cluster with complex entity networks -- patterns that could feed back into the triage rules.

## Technical Choices

I chose LangGraph over raw LangChain for investigation orchestration because conditional routing (crypto vs. non-crypto paths) maps naturally to state machines, and the explicit state makes debugging and auditing straightforward. XGBoost for triage gives sub-2ms inference with explainable feature importances -- critical when regulators ask why an alert was auto-closed. Langfuse integration (with local trace store fallback) provides full cost tracking and span-level observability across every investigation.

The synthetic data pipeline generates 500 Wealthsimple-like clients, 50,000 transactions across TFSA/RRSP/Crypto accounts, and 315 alerts covering 10 FINTRAC-aligned typologies including structuring, crypto layering, rapid fund movement, and PEP/sanctions hits. An 80% false positive rate mirrors real-world AML alert volumes.

## The Human-AI Boundary

The system deliberately stops short of filing STRs. The AI investigates, reasons, and recommends. The compliance officer reviews the evidence, reads the narrative, and clicks Approve, Reject, or Escalate in the Streamlit dashboard. This is the legally correct boundary under Canada's PCMLTFA -- and it's how trustworthy AI should work in regulated industries.
