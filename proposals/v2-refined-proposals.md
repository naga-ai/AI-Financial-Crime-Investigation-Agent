# Wealthsimple AI Builders -- Project Proposals V2

## What Changed From V1

- **Reframed**: Every proposal now leads with **money saved + time saved** for Wealthsimple
- **Technical depth**: Added caching strategy, Langfuse observability, system design patterns to every proposal
- **Skills showcase**: Each proposal now explicitly maps to your full stack: LangGraph, LangChain, multi-agent, fine-tuned small models, Langfuse, caching, predictive modeling, segmentation, content generation
- **Urgency**: Deadline is March 2 (5 days). Feasibility is now a top-3 filter.
- **FAQ signals**: "If the AI never actually does anything, it's probably not enough" -- every system must perform real cognitive work

---

## Your Full Technical Arsenal (must be visible in whatever you build)

- **LangGraph**: Multi-agent orchestration with state machines, conditional routing, parallel execution
- **LangChain**: Tool calling, structured output, chain composition
- **Multi-agent architecture**: Specialized agents with clear responsibilities, handoff protocols
- **Langfuse**: Full traceability -- trace every agent step, measure latency per agent, track token usage, debug failures, cost monitoring per investigation
- **Caching**: LLM response caching (semantic cache for similar queries), embedding cache, investigation result cache (avoid re-investigating known patterns), Redis/in-memory tiered caching
- **Fine-tuned small models**: Classification/triage tasks where a small specialized model beats GPT-4 at 1/100th the cost
- **Predictive modeling**: XGBoost/scikit-learn for risk scoring, anomaly detection
- **Segmentation**: Client/case clustering for pattern discovery
- **System design**: Async processing, queue-based architecture, graceful degradation, retry logic, rate limiting

---

## Proposal 1 (TOP PICK): AI-Native Financial Crime Investigation Agent

### The Problem (Wealthsimple's Pain)

With 3M+ users, Wealthsimple's AML (Anti-Money Laundering) team likely processes **thousands of transaction alerts daily**. Industry stats: 80-95% are false positives. Each manual investigation takes 30-60 minutes. This means:

- **Cost**: A team of 20-30 AML analysts at ~$80-100K/year each = $2-3M/year in salary alone
- **Time**: Weeks of backlog means regulatory risk (FINTRAC expects timely reporting)
- **Scale problem**: As Wealthsimple grows to 5M, 10M users, this cost scales linearly

### What the AI System Does (saves $1.5-2M/year, 10x faster)

A multi-agent investigation pipeline that autonomously conducts full AML investigations:

```
Alert Fired --> Triage Agent --> Investigation Agent --> Report Agent --> Human Review
                   |                    |                     |
            (fine-tuned small     (LangGraph multi-step   (structured
             model, cached)        reasoning, tools)       narrative)
```

**Agent 1 -- Triage Agent** (fine-tuned small model, NOT an LLM)

- Classifies alert severity in <100ms using a fine-tuned classifier
- Filters 80%+ obvious false positives instantly
- **Caching**: Semantic cache on transaction patterns -- if a pattern was already classified, skip the model call entirely
- **Cost savings**: Fine-tuned small model costs ~$0.001/alert vs $0.10+ for GPT-4
- **Langfuse trace**: Log every classification decision, confidence score, cache hit/miss

**Agent 2 -- Investigation Agent** (LangGraph state machine)

- For alerts that pass triage, conducts full investigation autonomously
- **Tools**: Pull transaction history, map entity relationships, check watchlists, analyze behavioral baselines, cross-reference with known typologies
- **LangGraph state machine**: Conditional routing based on investigation findings (if high-value -> deeper analysis, if matches known pattern -> fast-track)
- **Caching**: Cache entity relationship graphs, cache watchlist lookups (TTL-based), cache behavioral baselines (refresh daily)
- **Langfuse trace**: Full investigation trace -- every tool call, every reasoning step, time per step, total cost per investigation

**Agent 3 -- Report Generation Agent** (LLM with structured output)

- Generates FINTRAC-compliant investigation narratives
- Structured output: risk score, evidence summary, recommended action, confidence level
- **Caching**: Template caching for common report structures
- **Langfuse trace**: Report quality metrics, generation time, token usage

**Agent 4 -- Pattern Discovery Agent** (runs async, batch)

- Clusters completed investigations to discover emerging fraud typologies
- Uses your segmentation skills (K-means, DBSCAN on investigation features)
- Feeds new patterns back into the Triage Agent's training data
- **This is the flywheel**: System gets smarter over time

### System Design Architecture

```
                    +------------------+
                    |  Alert Queue     |  (async, Redis/SQS)
                    +--------+---------+
                             |
                    +--------v---------+
                    |  Triage Agent    |  Fine-tuned small model
                    |  (cached, <100ms)|  + semantic cache layer
                    +--------+---------+
                             |
                    +--------v---------+
                    |  Investigation   |  LangGraph state machine
                    |  Agent (tools)   |  multi-step reasoning
                    +--------+---------+
                             |
                    +--------v---------+
                    |  Report Agent    |  LLM + structured output
                    |  (templated)     |
                    +--------+---------+
                             |
                    +--------v---------+
                    |  Human Review    |  Streamlit dashboard
                    |  Dashboard       |  approve/reject/escalate
                    +--------+---------+
                             |
              +--------------v---------------+
              |  Pattern Discovery Agent     |  Batch, async
              |  (segmentation, clustering)  |  feeds back to triage
              +------------------------------+

  Cross-cutting:
  - Langfuse: traces every agent, every tool call, cost per investigation
  - Cache layer: Redis for hot data, semantic cache for LLM calls
  - Graceful degradation: if LLM is down, queue investigations, alert humans
```

### Human Role

Review AI-generated investigation reports on the dashboard. Approve, reject, or escalate. Make the final STR filing decision.

### Critical Human Decision

Whether to file a Suspicious Transaction Report (STR) with FINTRAC. This is a **legal obligation** under Canada's Proceeds of Crime (Money Laundering) and Terrorist Financing Act. Filing incorrectly harms innocent clients; failing to file enables crime. The decision requires judgment about **intent** -- was this transaction structuring deliberate? -- which demands human accountability.

### What Breaks First at Scale

**Triage model drift.** As transaction patterns evolve (new payment methods, new fraud techniques), the fine-tuned triage model's accuracy degrades. A 1% increase in false-negative rate at 3M users could mean hundreds of missed suspicious activities. Requires continuous human-in-the-loop recalibration + Langfuse monitoring of classification drift.

### Why This is THE Pick

- **Saves Wealthsimple $1.5-2M/year** in AML analyst costs (reallocation, not firing -- analysts focus on complex cases)
- **Reduces investigation time from 45 min to 3 min** per case
- **Mandatory process**: Every fintech MUST do this. It's not optional.
- **Showcases every skill**: LangGraph, multi-agent, fine-tuned small models, caching, Langfuse, predictive modeling, segmentation, content generation, system design
- **Non-obvious**: Most applicants won't touch compliance/regulatory -- they'll build client-facing tools
- **Real cognitive work**: The AI doesn't just classify -- it investigates, reasons, and writes

### Feasibility (5 days)

**HIGH.** Here's the build plan:

- Day 1: Simulate transaction data + alert data, set up project structure, LangGraph skeleton
- Day 2: Build Triage Agent (classifier) + Investigation Agent (tool-calling LangGraph)
- Day 3: Build Report Agent + Streamlit dashboard for human review
- Day 4: Add Langfuse tracing, caching layer, Pattern Discovery Agent
- Day 5: Polish, record demo video, write 500-word explanation

---

## Proposal 2: AI-Native Regulatory Change Impact Analyzer

### The Problem (saves ~$500K-1M/year + weeks of delay per regulatory change)

Compliance teams manually monitor regulatory updates, read hundreds of pages of legal text, assess relevance, update procedures. Each change takes 2-6 weeks. A team of 5-10 compliance specialists dedicated to this = $500K-1M/year. Delays mean regulatory risk.

### What the AI System Does

- **Monitor Agent**: Ingests regulatory feeds (OSC, FINTRAC, CSA) automatically
- **Impact Analysis Agent**: Maps changes to affected products/processes via knowledge graph + RAG
- **Severity Classifier**: Fine-tuned small model for urgency scoring (cached)
- **Policy Draft Agent**: Generates updated compliance procedures
- **Langfuse**: Full trace of every analysis, cost per regulatory change processed
- **Caching**: Regulatory document embeddings cached, impact mappings cached with TTL

### Why It's Strong

- Deeply non-obvious
- Shows compliance understanding
- 100x expansion of compliance officer capability
- Saves weeks per regulatory change

### Feasibility: HIGH (same 5-day timeline, using real public Canadian regulations)

---

## Proposal 3: AI-Native Client Financial Health Monitor

### The Problem (saves support costs + reduces churn, $2-5M/year impact)

Reactive support is expensive. Client churn from financial distress is costly. A proactive system that predicts and prevents churn before it happens has massive ROI.

### What the AI System Does

- **Predictive Scoring Agent**: Financial health score per client (XGBoost, your data science skills)
- **Segmentation Agent**: Clusters clients into intervention cohorts (your segmentation skills)
- **Intervention Orchestrator** (LangGraph): Multi-step personalized interventions
- **Langfuse**: Trace intervention outcomes, A/B test strategies
- **Caching**: Client health scores cached with short TTL, segment assignments cached

### Why It's Strong

- Scales a financial advisor from 100 to 3M clients
- Best showcase of data science + predictive modeling skills
- Direct alignment with Wealthsimple's mission

### Feasibility: MEDIUM-HIGH (needs simulated client data + predictive models + orchestration)

---

## Proposal 4: AI-Native Investment Due Diligence Pipeline

### The Problem (saves analyst time, ~$500K-1M/year)

Investment analysts spend days per security on research. Coverage limited by headcount.

### What the AI System Does

Multi-agent pipeline: Ingestion --> Analysis --> Risk Assessment --> Comparative --> Memo Writing. All traced via Langfuse. Embedding + analysis results cached.

### Feasibility: HIGH (real public SEC/SEDAR data available)

---

## Proposal 5: AI-Native Client Tax Optimization Agent

### The Problem (saves clients money, reduces support load, competitive advantage)

Tax optimization currently rule-based or manual. Most clients leave money on the table.

### What the AI System Does

Continuous monitoring + scenario modeling + compliant recommendations. Multi-agent with optimization engine.

### Feasibility: MEDIUM (needs simulated portfolio + tax data)

---

## Final Ranking (Updated for V2)

**Criteria weights shifted**: Cost savings to Wealthsimple is now primary, followed by technical showcase, then non-obviousness.

- **Proposal 1 (Financial Crime Investigation)** -- STRONGEST. $1.5-2M savings, showcases ALL skills, highest non-obvious factor, most buildable in 5 days, clearest human-AI boundary story
- **Proposal 3 (Financial Health Monitor)** -- RUNNER-UP. $2-5M impact but harder to quantify savings precisely, best data science showcase
- **Proposal 2 (Regulatory Analyzer)** -- SLEEPER. Deeply non-obvious, but harder to make visually compelling in a 2-3 min demo
- **Proposal 4 (Investment Due Diligence)** -- SOLID. Most visually impressive demo with real data, but more obvious
- **Proposal 5 (Tax Optimization)** -- GOOD. Directly relevant to Wealthsimple products, but most technically complex to prototype

---

## Next Steps

1. User selects which proposal to build
2. Create detailed technical architecture document
3. Build the prototype (5-day sprint)
4. Record demo video (2-3 minutes)
5. Write 500-word explanation
