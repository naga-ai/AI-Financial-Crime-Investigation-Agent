# AI-Native Financial Crime Investigation Agent

> A production-grade multi-agent AML investigation system for Wealthsimple, built with LangGraph, XGBoost, LangChain, Langfuse, and Streamlit.

---

## Live Demo

**Dashboard:** [http://YOUR_AWS_IP:8501](http://YOUR_AWS_IP:8501)

Click **"About This Project"** for the full submission summary, then **"Executive Summary" > "Run Pipeline"** to see the AI process 315 alerts in real time.

---

## Quick Start

### Option A: AWS (production -- one command)

```bash
# 1. Launch EC2: Ubuntu 22.04, t3.small, 20GB, security group open on TCP 8501
# 2. SSH in and run:
curl -sSL https://raw.githubusercontent.com/YOUR_USER/YOUR_REPO/main/deploy/aws-setup.sh -o setup.sh
bash setup.sh https://github.com/YOUR_USER/YOUR_REPO.git

# 3. Dashboard is live at http://<PUBLIC_IP>:8501
```

Or use the CloudFormation template: `deploy/cloudformation.yaml` (one-click from AWS Console).

### Option B: Docker (local)

```bash
git clone <this-repo> && cd build
cp .env.example .env
docker-compose up --build   # Starts app + Redis
```

Open **http://localhost:8501**.

### Option C: Python (no Docker)

```bash
cd build && pip install -r requirements.txt
python scripts/generate_data.py
python scripts/train_triage.py
streamlit run src/dashboard/app.py
```

### Option D: Terminal demo

```bash
python scripts/demo.py
```

---

## What This Is

A four-agent AI pipeline that processes AML alerts from detection to FINTRAC-ready STR report, with a human compliance officer making the final filing decision.

```
Alert ──▶ [Agent 1: Triage] ──▶ Auto-close 80% false positives
                │
                ▼ high/medium risk
          [Agent 2: Investigation] ──▶ 9 tools, conditional routing
                │
                ▼ file_str / escalate
          [Agent 3: Report] ──▶ FINTRAC-compliant STR narrative
                │
                ▼
          Human Compliance Officer ──▶ Approve / Reject / Escalate
                
          [Agent 4: Pattern Discovery] ──▶ Emerging typologies → rule feedback
```

### Key Results

| Metric | Value |
|--------|-------|
| Alerts processed | 315 |
| Auto-close rate (false positives) | 80% |
| Triage precision / recall | 100% / 93.7% |
| Avg pipeline latency | 17ms/alert |
| STR reports generated | 53 |
| Investigation cost estimate | ~$0.005/case |
| Pattern clusters discovered | 5 |
| Projected annual savings | ~$650K (vs. 6 FTE analysts) |

---

## Dashboard (8 Pages)

| Page | Description |
|------|-------------|
| **Executive Summary** | KPIs, cost savings projection, disposition breakdown, risk distribution |
| **Investigation Queue** | Risk-ranked cases with expandable profiles, steps, transactions |
| **STR Report Review** | Full FINTRAC narratives + Approve/Reject/Escalate workflow |
| **Model Intelligence** | XGBoost metrics, feature importance, SFT roadmap, classification thresholds |
| **Observability** | Per-investigation traces, span analysis, cost waterfall, production projection |
| **Cache Performance** | Redis/in-memory hit rates, region breakdown, efficiency analysis |
| **Pattern Discovery** | K-Means/DBSCAN clustering, PCA scatter, feature heatmap |
| **Architecture** | System design, tech stack, data model, deployment guide |

---

## Architecture

### Agent 1: XGBoost Triage Classifier
- 24 engineered features (velocity, structuring, crypto, PEP, income ratios)
- Sub-2ms inference with explainable feature importances
- 100% precision, 93.7% recall (stratified 5-fold CV)
- Semantic caching for repeated alert patterns

### Agent 2: LangGraph Investigation State Machine
- 7 graph nodes with conditional crypto routing + RAG retrieval
- 9 investigation tools + RAG regulatory context retrieval
- Per-tool span tracing
- Full audit trail for regulatory compliance

### RAG: Regulatory Knowledge Retrieval
- 12 FINTRAC guidance documents embedded with all-MiniLM-L6-v2 (sentence-transformers)
- ChromaDB vector store with HNSW indexing (cosine similarity)
- TF-IDF keyword fallback for lightweight environments
- Alert-type-aware query construction for targeted retrieval
- Case precedent store: completed investigations indexed for institutional memory

### Agent 3: FINTRAC STR Report Generator
- Template-based (offline) + LLM-powered (GPT-4o-mini) generation
- RAG-enriched: cites actual FINTRAC indicator references and regulatory language
- 6-section reports matching real STR format
- Pydantic-validated structured output

### Agent 4: Pattern Discovery
- K-Means / DBSCAN clustering on 16 investigation features
- Human-readable cluster descriptions
- Surfaces emerging typologies not in original rules
- Feedback loop for rule/model updates

### Observability (Langfuse + Local)
- Per-investigation traces with tool-level spans
- Cost estimation (LLM tokens, tool calls, ML inference)
- Local trace store fallback when Langfuse isn't configured
- Production cost projections

### Caching (Redis + In-Memory)
- 5 cache regions with independent TTLs
- Redis backend for production (auto-fallback to in-memory)
- Hit/miss tracking per region
- Cache efficiency analysis

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| Agent orchestration | LangGraph |
| LLM integration | LangChain + OpenAI (GPT-4o-mini) |
| RAG / Vector store | ChromaDB + sentence-transformers (all-MiniLM-L6-v2) |
| Triage ML | XGBoost + scikit-learn |
| Clustering | K-Means / DBSCAN (scikit-learn) |
| Observability | Langfuse + local trace store |
| Caching | Redis 7 + in-memory fallback |
| Data validation | Pydantic v2 |
| Dashboard | Streamlit + Plotly |
| Deployment | Docker + docker-compose |

---

## Project Structure

```
build/
├── Dockerfile                    # Production container
├── docker-compose.yml            # App + Redis
├── requirements.txt              # Python dependencies
├── .env.example                  # Configuration template
├── README.md
├── EXPLANATION.md                # 500-word summary
├── scripts/
│   ├── generate_data.py          # Synthetic dataset generator
│   ├── train_triage.py           # XGBoost model training
│   ├── run_pipeline.py           # Pipeline test script
│   ├── test_patterns.py          # Pattern discovery test
│   └── demo.py                   # End-to-end demo
├── src/
│   ├── config.py                 # Configuration + constants
│   ├── data/
│   │   ├── models.py             # Pydantic models (15 enums, 8 models)
│   │   ├── generators/
│   │   │   ├── client_generator.py
│   │   │   ├── transaction_generator.py
│   │   │   └── alert_generator.py
│   │   └── sample/               # Generated JSON datasets
│   ├── agents/
│   │   ├── orchestrator.py       # Pipeline coordinator
│   │   ├── triage/
│   │   │   ├── features.py       # 24-feature engineering
│   │   │   └── classifier.py     # XGBoost + caching
│   │   ├── investigation/
│   │   │   ├── state.py          # LangGraph TypedDict state
│   │   │   ├── tools.py          # 9 investigation tools
│   │   │   └── graph.py          # State machine
│   │   ├── report/
│   │   │   ├── templates.py      # FINTRAC STR templates
│   │   │   └── generator.py      # LLM + template generation
│   │   └── pattern_discovery/
│   │       ├── feature_extraction.py
│   │       └── clustering.py     # K-Means / DBSCAN
│   ├── rag/
│   │   ├── knowledge_base.py     # FINTRAC regulatory documents (12 docs)
│   │   └── retriever.py          # ChromaDB + TF-IDF dual-backend RAG engine
│   ├── cache/
│   │   └── manager.py            # Redis + in-memory dual backend
│   ├── observability/
│   │   └── langfuse_setup.py     # Tracing + cost tracking
│   └── dashboard/
│       └── app.py                # 11-page Streamlit command center
└── models/                       # Saved XGBoost model + metrics
```

---

## Data Model

Wealthsimple-specific entities:
- **Account Types:** TFSA, RRSP, Spousal RRSP, FHSA, RESP, Personal, Crypto
- **Transaction Types:** Deposit, Withdrawal, Buy, Sell, Transfer, Crypto Swap, Staking Reward, Dividend
- **10 AML Typologies:** Structuring, Rapid Movement, Crypto Layering, Round-Tripping, Velocity Spike, Dormant Activation, Geographic Anomaly, Third-Party Patterns, PEP/Sanctions, Age-Amount Mismatch
- **FINTRAC Alignment:** $10K reporting threshold, 48h structuring window, Canadian provinces, STR format

---

## Model Evolution Roadmap

| Phase | Approach | Status |
|-------|----------|--------|
| **Phase 1** | XGBoost on tabular features | Deployed |
| **Phase 2** | SFT small LLM (Llama 3.1 8B) on investigation transcripts | Planned |
| **Phase 3** | Graph neural networks + temporal transformers | Research |

---

## Configuration

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | LLM-powered report narratives | No (template fallback) |
| `LANGFUSE_PUBLIC_KEY` | Cloud observability | No (local trace store) |
| `LANGFUSE_SECRET_KEY` | Cloud observability | No (local trace store) |
| `REDIS_URL` | Redis caching backend | No (in-memory fallback) |

The system is fully functional without any API keys or external services.

---

## Human-AI Boundary

> The AI investigates, reasons, and recommends. The compliance officer makes the final STR filing decision.

This is the legally and ethically correct boundary under Canada's PCMLTFA. Every decision is audit-logged. Every investigation step is traced. The system augments human judgment in the highest-stakes regulatory context.

---

## Dashboard Pages (11)

| # | Page | Description |
|---|------|-------------|
| 0 | **About This Project** | Executive summary, impact, human-AI boundary, requirements checklist |
| 1 | **Executive Summary** | KPIs, cost savings projection, disposition breakdown, risk distribution |
| 2 | **Investigation Queue** | Risk-ranked cases, client profiles, risk factors, transactions, inline reports |
| 3 | **STR Report Review** | FINTRAC narratives + Approve/Reject/Escalate workflow |
| 4 | **Model Intelligence** | XGBoost model card, CV metrics, feature importance, SFT roadmap |
| 5 | **Knowledge Base (RAG)** | Semantic search over FINTRAC guidance, document browser, pipeline RAG usage |
| 6 | **Observability** | Per-investigation traces, span analysis, cost projections, trace explorer |
| 7 | **Cache Performance** | Redis/memory backend, hit/miss rates by region, efficiency analysis |
| 8 | **Pattern Discovery** | K-Means/DBSCAN clustering, PCA scatter, feature heatmap |
| 9 | **Architecture** | Cloud (AWS/GCP) + on-prem deployment, system design patterns, data model |
| 10 | **AI Governance** | FINTRAC/OSFI/AIDA/EU AI Act compliance, bias mitigation, security architecture |

---

## Changelog

| Date | Change | Rationale |
|------|--------|-----------|
| Day 1 | Project structure, Pydantic models, synthetic data generators | Foundation: 500 clients, 50K txns, 315 alerts (80/20 FP/TP) |
| Day 2 | XGBoost triage + LangGraph investigation agent | Core AI: auto-close 80% FP, 9-tool investigation state machine |
| Day 3 | STR report generator + Streamlit dashboard (4 pages) | Human interface: FINTRAC-compliant narratives, review workflow |
| Day 4 | Langfuse tracing + pattern discovery agent + 2 new pages | Observability: per-span traces, K-Means clustering |
| Day 5 | Demo script, README, 500-word explanation | Documentation and demo |
| Day 5+ | Redis cache, Docker deployment, dashboard rewrite (9 pages) | Production-grade: Redis backend, Docker compose, executive KPIs |
| Day 5+ | Architecture page (cloud/on-prem), AI Governance page | Enterprise: AWS/GCP deployment diagrams, AIDA/OSFI/bias/security |
| Day 5+ | Bias mitigation framework, fairness metrics, security architecture | Responsible AI: demographic parity, threat model, LLM security |
| Day 6 | RAG module: ChromaDB + sentence-transformers, 12 FINTRAC docs, Knowledge Base dashboard page | Grounds reports in regulatory language, adds semantic search, case precedent store |
