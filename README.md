# WS Intelligence Platform

> AI-native intelligence for compliance and client financial guidance — two production systems on shared infrastructure.

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

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        WS Intelligence Platform                                  │
├─────────────────────────────────────────────────────────────────────────────────┤
│  WS Clarity (Compliance)                    │  WS Pulse (Client AI)              │
│  ──────────────────────                    │  ──────────────────                │
│  AML Alerts → Triage (XGBoost, <2ms)        │  Financial Event → PII Masking     │
│       → Auto-close ~80% false positives     │       → Event Detector (6 types)   │
│       → Investigation (LangGraph, 9 tools) │       → Portfolio Analyzer         │
│       → Report Generator (GPT-4o-mini)     │       → RAG Retrieval              │
│       → Human Review → FINTRAC Filing       │       → Recommendation Agent       │
│  Pattern Discovery (K-Means / DBSCAN)       │       → Human Approval             │
├─────────────────────────────────────────────────────────────────────────────────┤
│  Shared: Redis · ChromaDB · Langfuse · PII Masking · Model Scorecards (OSFI E-23)│
└─────────────────────────────────────────────────────────────────────────────────┘
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
|-------|------------|
| Frontend | Next.js 14, React, TypeScript, Recharts |
| API | FastAPI, Uvicorn, Pydantic v2 |
| Orchestration | LangGraph, LangChain |
| Triage ML | XGBoost, scikit-learn |
| LLM | GPT-4o-mini (OpenAI) |
| RAG | ChromaDB, sentence-transformers |
| Cache & Queue | Redis 7 |
| Observability | Langfuse |
| Deployment | Docker, AWS EC2 |

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
│   ├── requirements.txt
│   └── docker-compose.yml
├── proposals/             # Project documentation
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

**Nagasundaram S**  
AI.Naga001@gmail.com · 647 648 5806
