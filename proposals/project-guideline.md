# WS Intelligence Platform -- Project Guideline

> Single source of truth for all requirements. Every feature, pattern, and standard requested across the conversation is captured here.

---

## Functional Requirements

### Project 1: WS Sentinel (Compliance Intelligence)
- [x] Multi-agent AML investigation pipeline (triage -> investigate -> report)
- [x] XGBoost triage classifier with 80% false positive detection
- [x] LangGraph investigation state machine with 8+ tool nodes
- [x] FINTRAC-compliant STR report generation (LLM + template fallback)
- [x] Pattern discovery with K-Means/DBSCAN clustering
- [x] RAG over FINTRAC regulatory guidance (ChromaDB + TF-IDF fallback)
- [x] Case precedent retrieval for institutional memory
- [x] Synthetic data: 500 clients, 50K transactions, realistic alerts with 80% false positive rate

### Project 2: WS Pulse (Client Financial Intelligence)
- [ ] Event detection agent (paycheck arrival, earnings report, market drop)
- [ ] Portfolio analysis agent (personalized impact per user's holdings)
- [ ] Recommendation engine (tax-aware, actionable, plain-language)
- [ ] LangGraph state machine for event processing pipeline
- [ ] Synthetic data: 10 realistic Canadian portfolios, 50 market/financial events
- [ ] Real Canadian tickers (SHOP.TO, RY.TO, ENB.TO, VFV.TO, etc.)
- [ ] Realistic account types (TFSA with contribution room, RRSP with match, crypto)
- [ ] Human approval gate (approve / adjust / dismiss recommendations)

---

## Non-Functional Requirements

### PII & Data Protection
- [ ] Field-level PII classification (RESTRICTED, CONFIDENTIAL, INTERNAL, PUBLIC)
- [ ] Deterministic tokenization (same input = same token, enables joins)
- [ ] Format-preserving tokens
- [ ] Audit log for every tokenize/detokenize operation
- [ ] PII masked before entering LLM prompts, RAG, cache
- [ ] Detokenization only at dashboard render layer

### Event Architecture & Queuing
- [ ] Redis Streams for event queuing
- [ ] Priority levels (HIGH, MEDIUM, LOW)
- [ ] Consumer groups with message acknowledgment (XACK)
- [ ] Dead Letter Queue (DLQ) after 3 retries
- [ ] Backpressure management (shed low-priority when overloaded)
- [ ] Idempotency via event hash deduplication
- [ ] Queue metrics: depth, processing rate, DLQ size, consumer lag

### Latency & Performance
- [ ] P50/P90/P95/P99 latency tracking per pipeline component
- [ ] Rolling window computation (reservoir sampling)
- [ ] SLA definitions per component
- [ ] SLA violation alerting
- [ ] Latency heatmap in dashboard

### Caching
- [x] Redis backend with in-memory fallback
- [x] Multi-region TTLs (triage, investigation, regulatory)
- [x] Cache hit/miss tracking per region
- [x] Cache performance dashboard page

### Observability
- [x] Langfuse integration with local fallback
- [x] Cost tracking per investigation
- [x] Span analysis by tool
- [ ] Latency percentile dashboard integration

### Security
- [x] AI governance page (AIDA, OSFI E-23, EU AI Act)
- [x] Threat modeling documentation
- [x] Secrets management via environment variables
- [ ] PII module as security boundary

---

## Model & ML Requirements

### Model Scorecard (OSFI E-23 aligned)
- [ ] Model metadata (name, version, training date, framework, hyperparameters)
- [ ] Performance metrics by segment (accuracy, precision, recall, F1, AUC-ROC)
- [ ] Bias analysis by demographic proxy (age band, province, income bracket, account type)
- [ ] Threshold management with business justification
- [ ] Drift monitoring (feature + prediction distribution shift)
- [ ] Documented failure modes and known limitations
- [ ] OSFI E-23 regulatory compliance checkpoints

### Fairness & Bias
- [x] No exclusion of minorities -- explicit documentation
- [x] Demographic proxy analysis in model evaluation
- [ ] Formal bias grid in model scorecard

---

## Presentation & Demo Requirements

### Dashboard
- [x] Professional Wealthsimple branding (dark theme, green accent)
- [x] Executive summary with KPIs and cost savings
- [x] Alert queue with expandable investigation cards
- [x] STR report review page
- [x] Model intelligence page with evolution roadmap
- [x] Observability page with trace explorer
- [x] Cache performance page
- [x] Pattern discovery with PCA visualization
- [x] Architecture page (4 tabs)
- [x] AI governance page
- [x] Knowledge base (RAG) page
- [x] Application summary / landing page
- [ ] Pulse: Event Feed page
- [ ] Pulse: Portfolio Intelligence page
- [ ] Pulse: Recommendations page
- [ ] Production Metrics page (latency P50-P99, queue health, PII audit, SLAs)
- [ ] Model Scorecard integration in Model Intelligence page

### Deployment
- [x] Docker + docker-compose (app + Redis)
- [x] AWS CloudFormation template for one-click deployment
- [x] AWS EC2 setup script
- [ ] Both projects running from single deployment

### Documentation
- [x] README with architecture, tech stack, quick start
- [x] EXPLANATION.md (500-word summary)
- [x] Changelog tracking all development phases
- [ ] Update README for unified platform framing
- [ ] Update EXPLANATION.md for dual-project narrative
- [ ] Cost analysis table in README and dashboard

---

## Business Requirements

### Cost Savings (must be highlighted)
- AML investigation: $37.50/case manual -> $0.005/case automated (99.98% reduction)
- Annual AML team: $2M (20 FTE) -> $350K (4 FTE + platform) = $1.65M saved
- False positive auto-close: 80% analyst time freed
- Client insight: $300/hr advisor -> $0.002/event (democratized to 3M users)
- Support ticket reduction: -30% = $500K/year savings

### Value Narrative
- Back-office: Compliance efficiency and regulatory risk reduction
- Client-facing: Personalized intelligence driving engagement and Premium upsells
- Platform: Shared infrastructure demonstrates systems thinking
- Competitive: AI-native approach vs. bolt-on features at traditional banks

---

## Technical Standards

### Architecture Patterns
- [x] Multi-agent orchestration (LangGraph)
- [x] Graceful degradation (LLM fallback to template)
- [x] Human-in-the-loop at every critical decision
- [x] Immutable audit trail
- [ ] Event-driven (Redis Streams)
- [ ] Circuit breaker pattern
- [ ] Rate limiting
- [ ] Retry with exponential backoff

### Code Quality
- [x] Pydantic models for all data structures
- [x] Type hints throughout
- [x] Modular architecture (agents, data, cache, rag, observability)
- [ ] Shared infrastructure as reusable modules
