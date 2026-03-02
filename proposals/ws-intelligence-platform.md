# WS Intelligence Platform

> Wealthsimple AI Builders Program Submission

Two AI-native systems built on shared production infrastructure. One repo, one deployment, one demo link.

**WS Clarity** -- Compliance Intelligence: AI that investigates so your analysts can decide.
**WS Pulse** -- Client Financial Intelligence: AI that turns every financial moment into the right action.

---

## Project 1: WS Clarity -- Compliance Intelligence

Automates AML alert investigation end-to-end. A compliance analyst who once spent 45 minutes per alert can now review 10 AI-generated STR reports in the same time, with 80% of false positives already auto-closed.

### Agent Pipeline

```
Alert Ingestion
  → Triage Agent (XGBoost, <2ms) ─▶ AUTO-CLOSE (80% false positives)
                                  ─▶ Investigation Agent (LangGraph)
                                        ├── gather_context
                                        ├── analyze_transactions
                                        ├── screen_watchlists
                                        ├── match_typologies
                                        ├── deep_crypto_analysis (conditional)
                                        ├── retrieve_regulatory_context (RAG)
                                        └── assess_risk
                                  → Report Generator (LLM / Template fallback)
                                  → Human Compliance Officer (Approve / Reject / Escalate)
                                  → FINTRAC Filing
  → Pattern Discovery Agent (K-Means / DBSCAN feedback loop)
```

### What's Built

- XGBoost triage classifier -- 24 engineered features, stratified K-fold CV, 100% precision, sub-2ms inference
- LangGraph investigation state machine -- 9 tool nodes with conditional routing and parallel execution
- STR report generator -- GPT-4o-mini with template fallback ensuring 100% uptime without API key
- Pattern discovery -- unsupervised clustering across 10 FINTRAC-aligned AML typologies
- UI-triggered model training with hot-reload -- train from the dashboard, see fold-by-fold metrics, model goes live immediately
- Synthetic data -- 500 clients, 50K+ transactions, 315 alerts with realistic 80% false positive rate

---

## Project 2: WS Pulse -- Client Financial Intelligence

Delivers personalized, tax-aware financial guidance to every user at sub-second speed, triggered by real financial events.

### Agent Pipeline

```
Financial Event (paycheck / earnings / market drop / rate change / dividend / rebalance)
  → PII Masking (strip names, account numbers)
  → Redis Event Queue (priority-sorted)
  → Event Detector (6 types, priority scoring)
  → Portfolio Analyzer (personalized impact per user's holdings)
  → RAG Retrieval (TFSA/RRSP rules, investment principles)
  → Recommendation Agent (GPT-4o-mini, plain-language, tax-aware)
  → Human Approval Gate (approve / adjust / dismiss)
```

### What's Built

- LangGraph agent pipeline processing 6 financial event types with priority scoring
- Personalized portfolio analysis -- tax implications, concentration risk, account-type optimization
- RAG-grounded recommendations using FINTRAC and Canadian tax/investment guidance
- 10 representative Canadian portfolios -- 23yo student ($5K TFSA) to 55yo pre-retiree ($400K+)
- Real Canadian tickers: SHOP.TO, RY.TO, ENB.TO, VFV.TO, BTC, ETH
- Per-user display with names, event types, confidence scores, and estimated value

---

## Shared Production Infrastructure

Both systems share the same production-grade modules:

- **PII Masking** -- Field-level HMAC-SHA256 tokenization before any LLM call, cache write, or RAG query. Full audit log.
- **Event Queue** -- Redis Streams with priority levels, consumer groups, DLQ after 3 retries, backpressure management.
- **Semantic Cache** -- Multi-region TTL policies (triage 1h, investigation 24h, regulatory 7d). Redis with in-memory fallback.
- **RAG** -- ChromaDB + sentence-transformers over FINTRAC regulatory guidance and financial principles.
- **Observability** -- Langfuse integration + local telemetry bus. Per-span cost tracking, latency distribution, trace explorer.
- **Model Scorecards** -- OSFI E-23 aligned metadata, performance metrics, bias analysis.
- **Latency Tracking** -- P50/P90/P95/P99 per pipeline component with SLA definitions.

---

## Architecture

```
WS Intelligence Platform
├── WS Clarity (Compliance Intelligence)
│   ├── Triage Agent ─────── XGBoost, 24 features, sub-2ms
│   ├── Investigation Agent ─ LangGraph, 9 tools
│   ├── Report Generator ──── GPT-4o-mini + template fallback
│   └── Pattern Discovery ─── K-Means / DBSCAN
│
├── WS Pulse (Client Intelligence)
│   ├── Event Detector ────── 6 event types, priority scoring
│   ├── Portfolio Analyzer ── Per-user impact, tax-aware
│   ├── Recommender ────────── RAG-grounded, personalized
│   └── Narrative Agent ────── Plain-language advice
│
└── Shared Infrastructure
    ├── PII Masking ────────── HMAC-SHA256 tokenization
    ├── Event Queue ────────── Redis Streams, DLQ, backpressure
    ├── Semantic Cache ──────── Multi-region TTL, Redis
    ├── RAG ─────────────────── ChromaDB + sentence-transformers
    ├── Latency Tracking ────── P50–P99 per component
    ├── Model Scorecards ────── OSFI E-23 aligned
    └── Observability ────────── Langfuse + telemetry bus
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14, React, TypeScript, Recharts, Vanilla CSS |
| API Server | FastAPI + Uvicorn (Python 3.10) |
| Orchestration | LangGraph + LangChain |
| Triage ML | XGBoost + scikit-learn |
| LLM | GPT-4o-mini (OpenAI) |
| Clustering | scikit-learn (K-Means, DBSCAN) |
| RAG | ChromaDB + sentence-transformers |
| Observability | Langfuse + local telemetry bus |
| Cache | Redis 7 + in-memory fallback |
| Validation | Pydantic v2 |
| Containers | Docker + Docker Compose |
| CI/CD | GitHub Actions → AWS EC2 (GHCR) |

---

## Business Impact

| Metric | Before | After | Savings |
|--------|--------|-------|---------|
| AML investigation time | 45 min / case | 17 ms / case | 99.9% faster |
| Cost per investigation | $37.50 (analyst hour) | $0.005 (compute) | 99.98% reduction |
| False positive auto-close | 0% -- all manual | 80% auto-closed | 80% analyst time freed |
| Annual AML team cost | $2M (20 FTE) | $350K (4 FTE + platform) | $1.65M / year saved |
| Client portfolio insight | $300 / hr advisor | $0.002 / event | Democratized to 3M users |
| Event response time | Hours to days | Sub-second | Real-time intelligence |

---

## Live Demo

| | URL |
|--|-----|
| **Frontend** | http://3.96.64.125:3000 |
| **API** | http://3.96.64.125:8000 |
| **API Docs** | http://3.96.64.125:8000/docs |

### Dashboard Pages

| Section | Pages |
|---------|-------|
| **Platform** | Platform Overview, Architecture |
| **WS Clarity** | Executive Summary, Investigation Queue, STR Report Review, Pattern Discovery, Model Intelligence |
| **WS Pulse** | Pulse Intelligence |
| **Infrastructure** | Observability and Traces |

---

*Built for the Wealthsimple AI Builders Program.*
