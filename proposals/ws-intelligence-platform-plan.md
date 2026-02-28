# WS Intelligence Platform: Production-Grade Implementation Plan

> Dual AI systems for Wealthsimple -- compliance intelligence (Sentinel) + client financial intelligence (Pulse) -- on shared production infrastructure with PII masking, event queuing, latency tracking (P50-P99), model scorecards, and financial industry best practices.

---

## Project Naming

- **WS Sentinel** -- Compliance Intelligence (AML investigation system, already built)
  - *"AI that investigates so your analysts can decide"*
- **WS Pulse** -- Client Financial Intelligence (Money Moment Orchestrator + Portfolio Intelligence)
  - *"AI that turns every financial moment into the right action"*
- **Unified:** WS Intelligence Platform
  - *"AI-native intelligence for both sides of the house"*

---

## Repository Strategy: Same Repo, Shared Infrastructure

Same repo. The shared infrastructure is the thesis. One deployment, one demo link, one `docker-compose`. The reviewer sees both systems side by side and immediately understands the platform thinking.

```
WS Intelligence Platform (one repo)
├── WS Sentinel (Compliance)
│   ├── Triage Agent (XGBoost)
│   ├── Investigation Agent (LangGraph)
│   ├── Report Generator (LLM/template)
│   └── Pattern Discovery (K-Means/DBSCAN)
│
├── WS Pulse (Client Intelligence)
│   ├── Event Detection Agent
│   ├── Portfolio Analysis Agent
│   ├── Recommendation Engine
│   └── Narrative Agent
│
└── Shared Production Infrastructure
    ├── PII Masking & Tokenization
    ├── Event Queue (Redis Streams)
    ├── Cache (Redis, multi-region TTL)
    ├── RAG (ChromaDB + sentence-transformers)
    ├── Observability (Langfuse + latency P50-P99)
    └── Model Scorecard (OSFI E-23 aligned)
```

---

## Production Infrastructure Modules

These are the shared modules that make this a real production system, not a demo. Each lives in `build/src/shared/`.

### 1. PII Masking Module -- `src/shared/pii.py`

Financial systems must tokenize PII before it enters any AI pipeline (Capital One pattern).

- **Field-level data classification**: `RESTRICTED` (SIN, account numbers), `CONFIDENTIAL` (name, DOB, address), `INTERNAL` (transaction amounts, dates), `PUBLIC` (market data)
- **Deterministic tokenization**: Same input always produces same token (enables joins without exposing PII). Format-preserving tokens maintain data structure
- **Masking strategies**: Full mask, partial mask (`John D.`), hash-based token (`PII-a7f3bc...`)
- **Audit log**: Every tokenize/detokenize operation logged with timestamp, purpose code, requesting component
- **Integration points**: Wraps all data before it enters LangGraph agents, RAG pipelines, LLM prompts, or cache. Detokenization only at the final dashboard render layer

```python
class PIIClassification(str, Enum):
    RESTRICTED = "restricted"       # SIN, full account number
    CONFIDENTIAL = "confidential"   # name, DOB, address
    INTERNAL = "internal"           # amounts, dates, risk scores
    PUBLIC = "public"               # market data, tickers

class PIIMasker:
    def tokenize(self, value, field_type) -> str: ...
    def mask_record(self, record, schema) -> dict: ...
    def detokenize(self, token) -> str: ...  # audit-logged, role-gated
```

### 2. Event Queue Module -- `src/shared/queue.py`

Uses Redis Streams (already in our stack) for backpressure, retry, and ordering:

- **Priority queues**: HIGH (market crash, fraud alert), MEDIUM (earnings, rate change), LOW (paycheck, rebalance)
- **Consumer groups**: Parallel processing with message acknowledgment (`XACK`)
- **Dead Letter Queue (DLQ)**: Failed events after 3 retries go to DLQ for human review
- **Backpressure**: When queue depth exceeds threshold, shed low-priority events and alert
- **Idempotency**: Event deduplication by hash to prevent double-processing
- **Metrics**: Queue depth, processing rate, DLQ size, consumer lag -- all exposed in dashboard

### 3. Latency Tracker -- `src/shared/latency.py`

Real production systems track P50/P90/P95/P99 latency for every component:

- **Per-step tracking**: Each agent step, tool call, RAG retrieval, cache lookup records latency
- **Percentile computation**: Rolling window P50, P90, P95, P99 using reservoir sampling
- **SLA definitions**: Per component (e.g., triage < 5ms P99, investigation < 500ms P95, RAG < 50ms P95)
- **SLA violation alerts**: Flag when percentile exceeds threshold
- **Dashboard widget**: Latency heatmap by component with SLA lines

### 4. Model Scorecard -- `src/shared/scorecard.py`

Following Google Model Card + AWS SageMaker Model Card + OSFI E-23 model risk management:

- **Model metadata**: Name, version, training date, framework, hyperparameters
- **Performance metrics**: Accuracy, precision, recall, F1, AUC-ROC by segment
- **Bias analysis**: Performance by demographic proxy (age band, province, income bracket, account type)
- **Threshold management**: Classification thresholds with business justification
- **Drift monitoring**: Feature distribution shift and prediction distribution shift over time
- **Regulatory compliance**: OSFI E-23 alignment checkpoints

Applies to both: XGBoost triage (Sentinel) AND event classification (Pulse).

---

## WS Pulse: What to Build

### Directory Structure

```
build/src/
├── shared/                           # Production infrastructure
│   ├── __init__.py
│   ├── pii.py                        # PII masking + tokenization
│   ├── queue.py                      # Redis Streams event queue
│   ├── latency.py                    # P50-P99 latency tracking
│   └── scorecard.py                  # Model scorecard framework
├── pulse/                            # Project 2: Client Intelligence
│   ├── __init__.py
│   ├── models.py                     # Pydantic: Portfolio, Holding, MarketEvent, Recommendation
│   ├── data/
│   │   ├── portfolio_generator.py    # Realistic Canadian portfolios
│   │   ├── market_event_generator.py # Realistic financial events
│   │   └── sample/                   # Generated JSON data
│   ├── agents/
│   │   ├── event_detector.py         # Event classification + priority
│   │   ├── portfolio_analyzer.py     # Portfolio impact analysis per event
│   │   ├── recommender.py            # Personalized action recommendation
│   │   └── graph.py                  # LangGraph state machine
│   └── orchestrator.py               # Queue-integrated batch processor
```

### Three Event Types (fully working pipeline)

1. **Paycheck Arrival** -- Income deposit detection, optimal TFSA/RRSP/emergency allocation, tax-aware reasoning via RAG
2. **Earnings Report** -- Held stock earnings analysis, portfolio concentration check, peer context, rebalance suggestion
3. **Market Drop** -- Portfolio impact quantification, retirement timeline impact, opportunistic buying assessment

### Realistic Data Generation

Portfolios must feel real to a Wealthsimple executive:

- **10 users** spanning demographics: 23yo student ($5K TFSA), 28yo tech worker ($45K TFSA+RRSP+crypto), 35yo dual-income ($120K managed), 42yo high-earner ($250K+ Premium), 55yo pre-retiree ($400K RRSP+TFSA), etc.
- **Real tickers**: SHOP.TO, RY.TO, ENB.TO, BNS.TO, VFV.TO, XIC.TO, ZAG.TO, BTC, ETH, AAPL, MSFT, AMZN, GOOGL, NVDA
- **Realistic accounts**: TFSA (contribution room), RRSP (employer match), non-registered, crypto
- **50 events** over 90 days: biweekly paychecks, 5 earnings reports, 2 BoC rate decisions, 3 significant market moves, 2 dividend payments, 1 subscription audit trigger

### Agent Pipeline with Production Patterns

```
Event Ingested
    → PII Masking (strip names, account numbers)
    → Redis Streams Queue (priority-sorted)
    → Consumer Group Dequeue
    → Event Classification (type + priority)
    → Portfolio Impact Analysis (personalized to user's holdings)
    → RAG: Financial Guidance (tax rules, investment principles)
    → Generate Recommendation (plain-language, actionable)
    → Record Latency (P50-P99)
    → Cache Result (Redis)
    → Human Approval Gate (approve / adjust / dismiss)
```

Every step: PII-masked inputs, latency tracked, traced in Langfuse, cached in Redis.

---

## Dashboard Restructure

```
WS INTELLIGENCE PLATFORM
  About This Project

SENTINEL (Compliance)
  Executive Summary
  Investigation Queue
  STR Report Review

PULSE (Client Intelligence)              <-- NEW
  Event Feed                             <-- NEW
  Portfolio Intelligence                 <-- NEW
  Recommendations                        <-- NEW

SHARED INFRASTRUCTURE
  Model Intelligence + Scorecard         <-- ENHANCED
  Knowledge Base (RAG)
  Production Metrics                     <-- NEW
  Observability
  Cache Performance
  Pattern Discovery
  Architecture
  AI Governance
```

### New/Enhanced Dashboard Pages

- **Event Feed**: Live event queue, priority badges, AI reasoning chains, processing status
- **Portfolio Intelligence**: Per-user portfolio breakdown, sector pie chart, concentration risk heatmap, earnings calendar
- **Recommendations**: Recommendation cards with Approve/Adjust/Dismiss, historical approval rate, savings tracker
- **Production Metrics** (NEW): Latency percentile charts (P50/P90/P95/P99 by component), SLA status board, queue health (depth, consumer lag, DLQ), PII audit log, circuit breaker status
- **Model Intelligence** (ENHANCED): Formal model scorecard with bias analysis grid, drift monitoring chart, OSFI E-23 checklist

---

## Cost Analysis

Research-backed numbers to highlight in dashboard and README:

| Metric | Manual Process | WS Intelligence Platform | Savings |
|--------|---------------|------------------------|---------|
| AML investigation time | 45 min/case | 17ms/case | 99.9% reduction |
| AML cost per investigation | $37.50 (analyst hourly) | $0.005 (compute) | 99.98% reduction |
| False positive auto-close | 0% (all manual) | 80% | 80% analyst time freed |
| Annual AML team cost (20 FTE) | $2M | $350K (4 FTE + platform) | $1.65M/year saved |
| Client portfolio insight | $300/hr advisor | $0.002/event | Democratized to 3M users |
| Event response time | Hours-days | Sub-second | Real-time |
| Support ticket reduction | Baseline | -30% (proactive) | $500K/year savings |

---

## Presentation Strategy

Landing page positions both projects:

> "I built a unified AI intelligence platform for Wealthsimple with two systems:
>
> **WS Sentinel** automates financial crime investigation (back-office compliance).
> **WS Pulse** delivers personalized financial intelligence (client-facing growth).
>
> Both run on shared production infrastructure: event queuing, PII masking, RAG, multi-agent orchestration, caching, latency tracking, and observability."

Demo video (2-3 min):
- 30s: Platform overview (both sides + shared infra)
- 60s: Sentinel processing AML alerts
- 60s: Pulse processing financial events (paycheck → allocation, earnings → portfolio briefing)
- 30s: Production metrics (latency percentiles, model scorecard, queue health)

---

## Files to Create/Update

**New files:**
- `proposals/project-guideline.md` -- All requirements consolidated
- `build/src/shared/__init__.py`, `pii.py`, `queue.py`, `latency.py`, `scorecard.py`
- `build/src/pulse/` -- Full module (models, data generators, agents, orchestrator)

**Updated files:**
- `build/src/dashboard/app.py` -- Pulse pages + Production Metrics + nav restructure
- `build/src/rag/knowledge_base.py` -- Financial guidance documents
- `build/README.md` -- Dual-project framing with cost analysis
- `build/EXPLANATION.md` -- Rewrite as unified platform
- `build/Dockerfile` -- Add Pulse data generation
- `build/scripts/demo.py` -- Add Pulse demo section
- Retrofit Sentinel orchestrator to use shared `queue.py`, `pii.py`, `latency.py`
