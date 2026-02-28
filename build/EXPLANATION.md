# WS Intelligence Platform

## What is this?

A unified AI platform for Wealthsimple with two production systems sharing common infrastructure:

**WS Sentinel** (Compliance Intelligence) automates AML investigation from alert triage to FINTRAC-ready STR reports. Four specialized agents -- triage classifier, investigation state machine, report generator, and pattern discovery -- process alerts in under 20 milliseconds. 80% of false positives are auto-closed, freeing analysts to focus on genuine threats.

**WS Pulse** (Client Financial Intelligence) detects financial moments -- paychecks, earnings reports, market drops, rate decisions -- and generates personalized, tax-aware recommendations for each user's portfolio. It turns generic notifications into actionable insights, democratizing advice that previously required $300/hr advisors.

## Why two systems?

The thesis is shared infrastructure. Both systems use the same PII masking module, event queue (Redis Streams), caching layer, RAG knowledge base, observability framework, and latency tracker. This demonstrates platform thinking: building once and applying across domains, not creating isolated solutions.

Sentinel solves a back-office cost problem ($1.65M/year savings). Pulse solves a client-facing growth problem (engagement, Premium upsells, support ticket reduction). Together, they show how AI can simultaneously cut costs and grow revenue.

## How does it work?

Sentinel processes AML alerts through a LangGraph state machine. An XGBoost classifier triages each alert (sub-2ms). Cases that warrant investigation flow through a multi-tool investigation agent that analyzes transactions, checks watchlists, maps entity networks, and retrieves FINTRAC regulatory guidance via RAG. The report generator produces compliant STR narratives. Pattern discovery clusters completed cases to surface emerging typologies.

Pulse processes financial events through a similar pipeline: event detection, portfolio impact analysis, RAG-retrieved financial guidance (tax rules, account optimization), and personalized recommendation generation. Events are queued via Redis Streams with priority, backpressure, and dead letter handling. All data is PII-masked before entering any AI component.

## Technical choices

- **LangGraph** for multi-agent orchestration (state machines, conditional routing)
- **XGBoost** for triage (fast, explainable, low-cost inference)
- **ChromaDB + sentence-transformers** for RAG (semantic search over regulations and financial guidance)
- **Redis** for caching (multi-region TTL) and event queuing (Streams with consumer groups)
- **Pydantic v2** for all data validation
- **PII tokenization** with deterministic hashing and audit logging
- **P50/P90/P95/P99 latency tracking** per pipeline component with SLA definitions
- **Model scorecards** aligned with OSFI E-23 for bias analysis and drift monitoring
- **Streamlit** for the interactive dashboard with 15 pages across both systems

## The human-AI boundary

AI automates investigation, analysis, and recommendation. Humans make final decisions: compliance officers approve STR filings (Sentinel), users approve or dismiss financial recommendations (Pulse). Both systems provide full reasoning chains and audit trails. Every PII operation is logged. Every model has a scorecard documenting known limitations and bias analysis.

This is not a demo. It is a production architecture that happens to run on synthetic data.

---
*Built for the Wealthsimple AI Builders Program.*
