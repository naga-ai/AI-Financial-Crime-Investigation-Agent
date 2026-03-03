# WS Intelligence Platform

> Wealthsimple AI Builders Program — Two AI-native systems on shared production infrastructure. One repo, one deployment, one demo.

**WS Clarity** — Compliance Intelligence: AI that investigates so your analysts can decide.  
**WS Pulse** — Client Financial Intelligence: AI that turns every financial moment into the right action.

---

## Live Demo

| | URL |
|--|-----|
| **Dashboard** | [http://3.96.64.125:3000](http://3.96.64.125:3000) |
| **API** | [http://3.96.64.125:8000](http://3.96.64.125:8000) |
| **API Docs** | [http://3.96.64.125:8000/docs](http://3.96.64.125:8000/docs) |

---

## Quick Start

### Docker (recommended)

```bash
cd app
docker compose up --build -d

# Dashboard: http://localhost:3000
# API: http://localhost:8000/docs
```

### Local Development

**1. Backend API**
```bash
cd app
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux
pip install -r requirements.txt
python scripts/generate_data.py
python -m uvicorn src.api.server:app --host 0.0.0.0 --port 8000 --reload
```

**2. Train the triage model** (required before running the pipeline)
```bash
# In a separate terminal, hit the train endpoint after the API is up:
curl -X POST http://localhost:8000/api/model/train
```

**3. Frontend**
```bash
cd app/frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

---

## WS Clarity — Compliance Intelligence

Automates AML alert investigation end-to-end. A compliance analyst who once spent 45 minutes per alert can now review 10 AI-generated STR reports in the same time, with ~80% of false positives already auto-closed.

**Agent Pipeline:**
```
Alert Ingestion
  → Triage Agent (XGBoost, <2ms) ─▶ AUTO-CLOSE (~80% false positives)
                                  ─▶ Investigation Agent (LangGraph)
                                        ├── gather_context, analyze_transactions
                                        ├── screen_watchlists, match_typologies
                                        ├── deep_crypto_analysis, retrieve_regulatory_context (RAG)
                                        └── assess_risk
                                  → Report Generator (LLM / template fallback)
                                  → Human Compliance Officer → FINTRAC Filing
  → Pattern Discovery (K-Means / DBSCAN)
```

**What's built:** XGBoost triage (24 features, sub-2ms); LangGraph investigation (9 tool nodes); STR report generator (GPT-4o-mini + template fallback); Pattern discovery across FINTRAC typologies; UI-triggered model training with hot-reload; 500 clients, 50K+ transactions, 315 synthetic alerts.

---

## WS Pulse — Client Financial Intelligence

Delivers personalized, tax-aware financial guidance at sub-second speed, triggered by real financial events.

**Agent Pipeline:**
```
Financial Event (paycheck / earnings / market drop / rate change / dividend / rebalance)
  → PII Masking → Redis Event Queue (priority-sorted)
  → Event Detector (6 types) → Portfolio Analyzer (per-user impact, tax-aware)
  → RAG Retrieval (TFSA/RRSP rules) → Recommendation Agent (GPT-4o-mini)
  → Human Approval Gate
```

**What's built:** LangGraph pipeline for 6 event types; personalized portfolio analysis; RAG-grounded recommendations; 10 Canadian portfolios from $5K TFSA to $400K+; real tickers (SHOP.TO, RY.TO, VFV.TO, etc.).

---

## Shared Production Infrastructure

Both systems share:

| Component | Description |
|-----------|-------------|
| **PII Masking** | Field-level HMAC-SHA256 tokenization before any LLM call, cache write, or RAG query. Full audit log. |
| **Event Queue** | Redis Streams, priority levels, consumer groups, DLQ after 3 retries, backpressure. |
| **Semantic Cache** | Multi-region TTL (triage 1h, investigation 24h, regulatory 7d). Redis + in-memory fallback. |
| **RAG** | ChromaDB + sentence-transformers over FINTRAC and financial principles. |
| **Observability** | Langfuse — per-span cost, latency distribution, trace explorer. |
| **Model Scorecards** | OSFI E-23 aligned metadata, performance metrics, bias analysis. |
| **Latency Tracking** | P50/P90/P95/P99 per component. |

---

## Architecture

```
WS Intelligence Platform
├── WS Clarity (Compliance)
│   ├── Triage Agent ─────── XGBoost, 24 features, sub-2ms
│   ├── Investigation Agent ─ LangGraph, 9 tools
│   ├── Report Generator ──── GPT-4o-mini + template fallback
│   └── Pattern Discovery ─── K-Means / DBSCAN
├── WS Pulse (Client Intelligence)
│   ├── Event Detector ────── 6 event types, priority scoring
│   ├── Portfolio Analyzer ── Per-user impact, tax-aware
│   └── Recommendation Agent ─ RAG-grounded, personalized
└── Shared: PII Masking · Event Queue · Semantic Cache · RAG · Observability · Model Scorecards
```

---

## Dashboard Pages

| Section | Pages |
|---------|-------|
| **Platform** | Platform Overview, Architecture |
| **WS Clarity** | Executive Summary, Investigation Queue, STR Report Review, Pattern Discovery, Model Intelligence |
| **WS Pulse** | Pulse Intelligence |
| **Infrastructure** | Observability & Traces |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14, React, TypeScript, Recharts |
| API | FastAPI, Uvicorn, Pydantic v2 |
| Orchestration | LangGraph, LangChain |
| Triage ML | XGBoost, scikit-learn |
| Clustering | scikit-learn (K-Means, DBSCAN) |
| LLM | GPT-4o-mini (OpenAI) |
| RAG | ChromaDB, sentence-transformers |
| Cache & Queue | Redis 7 |
| Observability | Langfuse |
| Deployment | Docker, GitHub Actions → GHCR, AWS EC2 |

---

## Project Structure

```
wealthsimple/
├── app/
│   ├── frontend/          # Next.js dashboard
│   ├── src/
│   │   ├── api/           # FastAPI server
│   │   ├── agents/        # Triage, Investigation, Report, Pattern Discovery
│   │   ├── pulse/         # WS Pulse orchestrator
│   │   ├── data/          # Generators, sample data
│   │   ├── shared/        # PII, config
│   │   └── ...
│   ├── scripts/           # generate_data, train
│   ├── deploy/            # Docker Compose build, CloudFormation
│   ├── requirements.txt
│   └── docker-compose.yml
├── EXPLANATION.md         # 500-word written explanation
├── VIDEO_SCRIPT.md        # 3-min recording script
└── README.md
```

---

## Impact (Estimated)

| Metric | Before | After |
|--------|--------|-------|
| AML investigation time | 45 min / case | ~5 min (AI + review) |
| Cost per investigation | $37.50 (analyst hour) | ~$4 (compute + review) |
| False positive auto-close | 0% | ~80% |
| Annual AML savings | — | ~$900K (15 → 6 FTE) |
| Client portfolio insight | $200/hr advisor | ~$0.05 / event |
| Event response | Hours to days | Seconds |

---

## Key Features

- **Human-in-the-loop** — AI recommends; humans approve every critical action. No STR filing without compliance officer sign-off.
- **Production-ready** — PII masking, semantic cache, event queues, observability, OSFI E-23 aligned scorecards.
- **Synthetic data** — 500 clients, 50K+ transactions, 315 alerts. Run `scripts/generate_data.py` to regenerate.
- **Train from UI** — Retrain the triage model from the dashboard; hot-reload into the pipeline.

---

## Deployment

- **Docker Compose**: `cd app && docker compose up -d`
- **AWS EC2**: Deploy via `app/deploy/`. Ensure Redis, API, and frontend are running. Generate data and train the model on first deploy.
- **CI/CD**: GitHub Actions → GHCR. See `.github/workflows/`.

---

## Contact

AI.Naga001@gmail.com
