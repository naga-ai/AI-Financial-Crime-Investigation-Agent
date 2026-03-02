# WS Intelligence Platform

## What the human can now do that they couldn't before

**WS Clarity** (Compliance): A compliance analyst who once spent 45 minutes manually reviewing a single AML alert can now process the same alert in under 20 milliseconds and review 10 AI-generated investigation reports in the time it previously took to open one. 80% of false positives are auto-closed with a documented confidence score, so analysts focus exclusively on genuine risk. They can approve, reject, or escalate FINTRAC-ready STR reports in one click, with a full reasoning chain already written.

**WS Pilot** (Client Intelligence): A portfolio specialist who could previously advise perhaps 50 clients per day can now deliver personalized, tax-aware financial guidance to 3 million users simultaneously — in response to real-time events like earnings reports, rate decisions, and paychecks — at a cost of $0.002 per event rather than $300 per hour.

## What AI is responsible for

Both systems share a common AI-native pipeline. For Clarity: an XGBoost triage classifier (sub-2ms, 24 features) scores every alert; a LangGraph state machine runs a full investigation using 9 tools (transaction analysis, watchlist lookup, entity graph, RAG retrieval over FINTRAC guidance); a report generator produces structured STR narratives. For Pilot: an event detector identifies 6 financial moment types; a portfolio analyzer computes personalized impact and tax implications; a recommendation agent grounds advice in RAG-retrieved guidance.

Both pipelines share production infrastructure: field-level PII masking before any LLM or cache call, Redis event queues with DLQ and backpressure, multi-region semantic caching with TTL policies, and per-span tracing. A unified event telemetry bus captures every pipeline event, human decision, cache hit, and SLA violation in a 10,000-event ring buffer.

## Where AI must stop

The STR filing decision is irreversible — it triggers a regulatory submission to FINTRAC with potential criminal liability. AI provides a recommendation with confidence, reasoning, and risk indicators. A human compliance officer makes the final call. No report is filed without explicit human approval.

On the Pilot side, AI never initiates portfolio changes. It proposes. Users approve, adjust, or dismiss. No automated trading.

## What would break first at scale

The interactive Scaling Simulation (Architecture page) models this explicitly: at 100,000 alerts/day, LLM investigation cost ($0.0012/case) stays manageable, but queue saturation becomes the bottleneck — more parallel pipeline workers are needed before Redis memory. The semantic cache defers much of this: repeated alert patterns hit the cache instead of the LLM, reducing marginal cost toward zero at scale.

The other constraint is the human review queue. AI can process 10,000 cases per minute; a compliance team cannot. The system is designed to widen that funnel — only cases that genuinely need human eyes reach the review queue. At 10x current volume, the triage threshold would need tuning and the analyst team would need to grow from 4 to approximately 8 FTE, not 40.

---

## Technology Stack

### AI / Machine Learning Backend
| Component | Technology | Purpose |
|-----------|------------|---------|
| **Triage Classifier** | XGBoost | 24-feature binary classifier on AML alerts — sub-2ms inference, 100% precision |
| **Investigation Agent** | LangGraph + LangChain | 9-node state machine orchestrating parallel tool calls |
| **LLM** | GPT-4o-mini (OpenAI) or local Llama3.1/Mistral (fallback) | STR narrative generation and reasoning |
| **RAG Retrieval** | ChromaDB + sentence-transformers | Semantic search over FINTRAC regulatory guidance |
| **Pattern Discovery** | scikit-learn K-Means / DBSCAN | Unsupervised clustering of fraud typologies |
| **Observability** | Langfuse (production) / in-memory (local) | Per-span cost tracking, latency, trace explorer |

### Web Application (New Frontend — v2)
| Component | Technology | Purpose |
|-----------|------------|---------|
| **Frontend Framework** | **Next.js 14** (React, TypeScript) | Premium server-rendered web application |
| **Styling** | **Vanilla CSS** (CSS custom properties, glassmorphism) | Custom dark-mode design system with micro-animations |
| **Charts** | **Recharts** | Themed bar, pie, scatter, and histogram charts |
| **Fonts** | **Inter + Outfit** (Google Fonts) | High-end editorial typography |
| **API Client** | Native `fetch` with TypeScript types | Typed API calls to the Python backend |

### API Backend (New — v2)
| Component | Technology | Purpose |
|-----------|------------|---------|
| **API Server** | **FastAPI** (Python) | High-performance REST API wrapping the ML pipeline |
| **ASGI Server** | **Uvicorn** | Production-grade async server (replaces Streamlit) |

### Infrastructure
| Component | Technology | Purpose |
|-----------|------------|---------|
| **Cache** | Redis 7 | Multi-region semantic caching, event queues |
| **Containerization** | Docker + Docker Compose | Three-service stack: Redis + FastAPI + Next.js |
| **CI/CD** | GitHub Actions → EC2 SSH | `docker compose up --build -d` on every push to `main` |

### Previous Frontend (v1 — retained for reference)
The original Streamlit dashboard (`app/src/dashboard/app.py`) remains in the codebase and can still be run with `streamlit run src/dashboard/app.py`, but the Docker deployment now serves the Next.js frontend instead.

## Running Locally

```bash
# 1. Start the Python backend API (port 8000)
cd app
pip install fastapi uvicorn python-multipart
python -m uvicorn src.api.server:app --host 0.0.0.0 --port 8000 --reload

# 2. Start the Next.js frontend (port 3000)
cd app/frontend
npm run dev

# Open http://localhost:3000
```

## Deploying to AWS EC2

```bash
# GitHub Actions triggers on push to main — runs on EC2:
git pull
cd app
sudo docker compose down
sudo docker compose up --build -d

# Frontend: http://your-ec2-ip:3000
# API docs: http://your-ec2-ip:8000/docs
```

---
*Built for the Wealthsimple AI Builders Program.*
