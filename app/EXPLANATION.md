# WS Intelligence Platform — Written Explanation

## What the human can now do that they couldn't before

Today a compliance analyst spends roughly 45 minutes on every AML alert — pulling transaction histories, screening watchlists, matching FINTRAC typologies, and drafting a Suspicious Transaction Report. Most of those alerts are false positives. The analyst knows it within the first two minutes, but the process still demands the full 45.

WS Clarity changes that. An XGBoost triage classifier scores incoming alerts in under 2 milliseconds and auto-closes roughly 80% of low-risk false positives with documented confidence. The remaining 20% move into a LangGraph investigation pipeline: nine tool nodes handle transaction analysis, watchlist screening, entity graph construction, typology matching, and RAG retrieval over FINTRAC regulatory guidance. A report generator (GPT-4o-mini with template fallback) drafts STR narratives that analysts review, approve, or reject in a single click. Investigation time drops from 45 minutes to around 5. A team that needed 15 analysts can operate with 6 — saving an estimated $900K per year.

On the client side, WS Pulse turns every financial moment — a paycheck deposit, an earnings surprise, a rate cut — into a personalised, tax-aware recommendation delivered in seconds. An event detector classifies and prioritises incoming triggers. A portfolio analyser evaluates the impact against each user's holdings. A recommendation agent, grounded through RAG in TFSA and RRSP guidance, generates plain-language advice. What previously required a $200/hr financial advisor now costs pennies per event and scales to the full user base.

## What AI is responsible for

Both systems share a common architecture. On the Clarity side: the XGBoost classifier (24 engineered features, stratified cross-validation) triages every alert. A LangGraph state machine orchestrates the investigation — transaction pattern analysis, sanctions and PEP screening, entity-relationship mapping, FINTRAC typology matching, and semantic search over regulatory guidance. GPT-4o-mini generates STR narratives. K-Means and DBSCAN clustering surfaces emerging fraud patterns that rule-based systems miss entirely.

On the Pulse side: an event detector classifies six financial event types with priority scoring. A portfolio analyser computes personalised impact and tax implications. A recommendation agent grounds advice in RAG-retrieved Canadian regulatory context.

Both pipelines share production infrastructure: PII masking via HMAC-SHA256 tokenisation before any LLM or cache interaction, Redis Streams for event queuing with dead-letter queues and backpressure, semantic caching with tiered TTLs, full-trace observability through Langfuse, and OSFI E-23 aligned model scorecards.

## Where AI must stop

The STR filing decision carries regulatory consequences — it triggers a submission to FINTRAC. AI provides the recommendation, the reasoning chain, and the risk indicators. A compliance officer makes the final call. No report is filed without human approval.

On the Pulse side, AI never initiates portfolio changes. It proposes. Users approve, adjust, or dismiss. No automated trading, no irreversible actions.

## What would break first at scale

At 100,000 alerts per day, LLM investigation cost stays manageable (~$0.04 per case), but queue throughput becomes the constraint. More consumer workers are needed before Redis memory pressure is a factor. The semantic cache helps substantially — repeated patterns hit cache and skip the LLM entirely, pushing marginal cost down.

The harder limit is human review capacity. AI can process thousands of cases per minute; a compliance team cannot. The system addresses this by ensuring only genuinely suspicious cases reach the review queue. At ten times current volume, the triage threshold would need tuning and the team would grow from six to roughly ten, not sixty.
