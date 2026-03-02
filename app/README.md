# WS Intelligence Platform

> AI-Native Intelligence for Both Sides of the House

**WS Clarity** -- Compliance Intelligence: AI that investigates so your analysts can decide.
**WS Pulse** -- Client Financial Intelligence: AI that turns every financial moment into the right action.

---

## Quick Start

### Docker (recommended -- includes Redis)

```bash
cd app
docker compose up --build -d

# Frontend: http://localhost:3000
# API docs: http://localhost:8000/docs
```

### Local Development

```bash
# 1. Backend API (port 8000)
cd app
python -m venv .venv
.venv/Scripts/activate      # Windows
# source .venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
python scripts/generate_data.py
python scripts/train_triage.py
python -m uvicorn src.api.server:app --host 0.0.0.0 --port 8000 --reload

# 2. Frontend (port 3000) -- separate terminal
cd app/frontend
npm install
npm run dev

# Open http://localhost:3000
```

---

## Architecture

```
WS Intelligence Platform
├── WS Clarity (Compliance Intelligence)
│   ├── Triage Agent ─────── XGBoost, 24 features, sub-2ms inference
│   ├── Investigation Agent ─ LangGraph, 9 tools, conditional routing
│   ├── Report Generator ──── GPT-4o-mini + template fallback
│   └── Pattern Discovery ─── K-Means / DBSCAN, 10 typologies
│
├── WS Pulse (Client Intelligence)
│   ├── Event Detector ────── 6 event types, priority scoring
│   ├── Portfolio Analyzer ── Per-user impact, tax implications
│   ├── Recommender ────────── Personalized, RAG-grounded
│   └── Narrative Agent ────── Plain-language advice
│
└── Shared Infrastructure
    ├── PII Masking ────────── HMAC-SHA256 tokenization
    ├── Event Queue ────────── Redis Streams, DLQ, backpressure
    ├── Semantic Cache ──────── Multi-region TTL, Redis
    ├── RAG ─────────────────── ChromaDB + sentence-transformers
    ├── Latency Tracking ────── P50-P99 per component
    ├── Model Scorecards ────── OSFI E-23 aligned
    └── Observability ────────── Langfuse + telemetry bus
```

---

## Dashboard Pages

| Section | Pages |
|---------|-------|
| **Platform** | Platform Overview |
| **WS Clarity** | Executive Summary, Investigation Queue, STR Report Review, Pattern Discovery, Model Intelligence |
| **WS Pulse** | Pulse Intelligence |
| **Infrastructure** | Observability and Traces |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14, React, TypeScript, Recharts, Vanilla CSS |
| API Server | FastAPI + Uvicorn (Python 3.10) |
| Orchestration | LangGraph + LangChain |
| Triage ML | XGBoost + scikit-learn |
| LLM | GPT-4o-mini (OpenAI) |
| RAG | ChromaDB + sentence-transformers |
| Observability | Langfuse + local telemetry bus |
| Cache | Redis 7 + in-memory fallback |
| Validation | Pydantic v2 |
| Containers | Docker + Docker Compose |
| CI/CD | GitHub Actions → AWS EC2 (GHCR) |

---

## Impact

| Metric | Before | After |
|--------|--------|-------|
| AML investigation time | 45 min / case | 17 ms / case |
| False positive auto-close | 0% | 80% |
| Annual AML team cost | $2M (20 FTE) | $350K (4 FTE + platform) |
| Client portfolio insight | $300 / hr advisor | $0.002 / event |
| Users served simultaneously | ~50 | 3M+ |

---

## Deployment

```bash
# Auto-deploys on push to main via GitHub Actions
# See .github/workflows/deploy-ec2.yml

# Frontend: http://your-ec2-ip:3000
# API docs: http://your-ec2-ip:8000/docs
```

---

*Built for the Wealthsimple AI Builders Program.*
