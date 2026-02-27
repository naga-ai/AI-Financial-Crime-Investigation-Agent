# Wealthsimple AI Builders -- Project Proposals V1

## Context

These are the initial project proposals generated for the Wealthsimple AI Builders application, based on analysis of the job posting and the applicant's background in AI engineering, LangGraph, LangChain, LLMs, fine-tuning, small models, data science, agentic systems, segmentation, and predictive modeling.

### Key Signals from the Job Posting

- **AI-native systems**: Rebuilt from scratch, NOT AI layered on old workflows
- **Real cognitive/operational responsibility**: Not a wrapper on ChatGPT
- **Clear human-AI boundary reasoning**: Where AI must stop
- **Systems thinking**: Across product, engineering, compliance, and operations
- **Meaningful expansion**: 10x-100x capability, not incremental improvement

---

## Proposal 1: AI-Native Financial Crime Investigation Agent

### The Problem

Wealthsimple's AML (Anti-Money Laundering) team processes thousands of transaction alerts daily. Industry stats show 80-95% are false positives. Each manual investigation takes 30-60 minutes. A team of 20-30 AML analysts at ~$80-100K/year = $2-3M/year in salary. Weeks of backlog create regulatory risk (FINTRAC expects timely reporting). As Wealthsimple scales, this cost scales linearly.

### What the AI System Does

A multi-agent investigation pipeline that autonomously conducts full AML investigations:

- **Triage Agent**: Fine-tuned small classifier that filters 80%+ obvious false positives in <100ms
- **Investigation Agent**: For alerts that pass triage, conducts full investigation autonomously -- pulls transaction history, maps entity relationships, checks watchlists, analyzes behavioral baselines, cross-references known typologies
- **Report Generation Agent**: Generates FINTRAC-compliant investigation narratives with structured output (risk score, evidence summary, recommended action, confidence level)
- **Pattern Discovery Agent**: Clusters completed investigations to discover emerging fraud typologies, feeds new patterns back to triage training data

### Human Role

Review AI-generated investigation reports on a dashboard. Approve, reject, or escalate. Make the final STR filing decision.

### Critical Human Decision

Whether to file a Suspicious Transaction Report (STR) with FINTRAC. This is a legal obligation under Canada's Proceeds of Crime (Money Laundering) and Terrorist Financing Act. Filing incorrectly harms innocent clients; failing to file enables crime. The decision requires judgment about intent -- was this transaction structuring deliberate? -- which demands human accountability.

### What Breaks First at Scale

Triage model drift. As transaction patterns evolve (new payment methods, new fraud techniques), the fine-tuned triage model's accuracy degrades. A 1% increase in false-negative rate at 3M users could mean hundreds of missed suspicious activities.

### Feasibility

HIGH -- Can use simulated transaction data, real AML typologies, and public watchlist formats.

---

## Proposal 2: AI-Native Regulatory Change Impact Analyzer

### The Problem

Compliance teams manually monitor regulatory updates, read hundreds of pages of legal text, assess relevance, and update procedures. Each regulatory change takes 2-6 weeks to process. A team of 5-10 compliance specialists dedicated to this costs $500K-1M/year. Delays create regulatory risk.

### What the AI System Does

- **Monitor Agent**: Ingests regulatory feeds (OSC, FINTRAC, CSA) automatically
- **Impact Analysis Agent**: Maps changes to affected products/processes via knowledge graph + RAG
- **Severity Classifier**: Urgency scoring for prioritization
- **Policy Draft Agent**: Generates updated compliance procedures

### Human Role

Final sign-off on compliance procedure changes and interpretation of ambiguous regulatory language.

### Critical Human Decision

Whether to approve changes to compliance procedures based on regulatory interpretation. Ambiguous regulatory language requires understanding regulatory intent beyond the text itself, carrying legal liability.

### What Breaks First at Scale

Regulatory interpretation ambiguity -- as the volume of jurisdictions and regulations grows, the AI may misinterpret cross-referencing between regulations or fail to capture implied requirements.

### Feasibility

HIGH -- Can use real public Canadian regulations from OSC, FINTRAC, CSA.

---

## Proposal 3: AI-Native Client Financial Health Monitor

### The Problem

Reactive support is expensive. Client churn from financial distress is costly. Traditional advisors can only actively manage 50-100 clients, so everyone else gets generic outreach. With 3M+ users, Wealthsimple needs proactive intervention at scale.

### What the AI System Does

- **Predictive Scoring Agent**: Continuous financial health scoring per client using ML models (XGBoost, scikit-learn)
- **Segmentation Agent**: Clusters clients into intervention cohorts using segmentation techniques (K-means, DBSCAN)
- **Intervention Orchestrator**: Multi-step personalized interventions via LangGraph -- in-app messages, emails, advisor routing
- **Learning Loop**: Tracks intervention outcomes and adapts strategies

### Human Role

Handle escalated or sensitive cases. Approve any account-altering recommendations above certain thresholds.

### Critical Human Decision

Whether to recommend taking on debt (e.g., a line of credit for consolidation). Assessing genuine financial hardship requires empathy and contextual judgment that has both ethical and business implications.

### What Breaks First at Scale

False positive distress signals. As the user base diversifies, behavioral patterns that indicate distress in one demographic may be normal in another. Requires continuous model recalibration and human oversight.

### Feasibility

MEDIUM-HIGH -- Needs simulated client data, predictive models, and orchestration layer.

---

## Proposal 4: AI-Native Investment Due Diligence Pipeline

### The Problem

Investment analysts spend days per security on research. Coverage is limited by headcount. Manual process includes reading SEC/SEDAR filings, earnings calls, news, and market data.

### What the AI System Does

Multi-agent pipeline:
- **Ingestion Agent**: Pulls SEC/SEDAR filings, earnings transcripts, news, market data
- **Analysis Agent**: Extracts key metrics, identifies trends, performs comparative analysis
- **Risk Assessment Agent**: Evaluates risk factors and generates risk profiles
- **Memo Writing Agent**: Generates institutional-quality investment memos with structured output

### Human Role

Make the actual buy/sell/hold investment decisions. Review and validate AI-generated analysis.

### Critical Human Decision

The investment decision itself -- buy/sell/hold. This requires risk tolerance assessment, portfolio theory application, and fiduciary accountability that carries legal and financial consequences.

### What Breaks First at Scale

Data quality and timeliness. As the system monitors more securities across more markets, lag in data ingestion or quality issues in source documents could lead to stale or incorrect analysis.

### Feasibility

HIGH -- Real public SEC/SEDAR data available.

---

## Proposal 5: AI-Native Client Tax Optimization Agent

### The Problem

Tax optimization is currently rule-based or manual. Most clients leave money on the table through suboptimal asset location, missed tax-loss harvesting opportunities, and poor timing of taxable events.

### What the AI System Does

- **Portfolio Monitor**: Continuous monitoring of portfolio for tax implications
- **Scenario Modeling Agent**: Models tax consequences of different strategies
- **Optimization Engine**: Recommends tax-efficient trades and asset allocation changes
- **Compliance Check Agent**: Ensures all recommendations are tax-code compliant

### Human Role

Approve tax-efficient trades, especially larger moves with significant portfolio impact.

### Critical Human Decision

Whether to execute tax strategies that involve significant portfolio restructuring. These decisions have irreversible tax consequences and require understanding the client's full financial picture beyond what's visible in portfolio data alone.

### What Breaks First at Scale

Tax code complexity across jurisdictions. As Wealthsimple expands, the combinatorial explosion of tax rules across provinces and investment types makes it increasingly difficult to guarantee optimal recommendations.

### Feasibility

MEDIUM -- Needs simulated portfolio data and Canadian tax rules modeling.

---

## Initial Ranking

1. **Proposal 1 (Financial Crime Investigation)** -- Strongest overall. Non-obvious (most applicants won't touch compliance), demonstrates systems thinking, has clear human-AI boundary story, and is highly buildable.
2. **Proposal 3 (Financial Health Monitor)** -- Best showcase of data science and predictive modeling skills. Directly aligned with Wealthsimple's mission.
3. **Proposal 2 (Regulatory Analyzer)** -- Deeply non-obvious, shows compliance understanding. Could be harder to make visually compelling in a demo.
4. **Proposal 4 (Investment Due Diligence)** -- Most visually impressive demo potential with real public data. More obvious idea though.
5. **Proposal 5 (Tax Optimization)** -- Directly relevant to Wealthsimple's products but most technically complex to prototype.

---

*V1 generated from initial analysis of the job posting and applicant background.*
*Next iteration (V2) will incorporate: cost/time savings framing, caching strategy, Langfuse observability, system design patterns, and technical depth for each proposal.*
