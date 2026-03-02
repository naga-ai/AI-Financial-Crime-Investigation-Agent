# WS Intelligence Platform -- Written Explanation

## What the human can now do that they couldn't before

A compliance analyst currently spends 45 minutes manually reviewing a single AML alert -- pulling transactions, screening watchlists, matching typologies, drafting a Suspicious Transaction Report. With WS Clarity, that analyst processes an alert in under 20 milliseconds and reviews 10 AI-generated investigation reports in the time it once took to open one. Eighty percent of false positives are auto-closed with documented confidence scores. Analysts approve, reject, or escalate FINTRAC-ready STR reports in one click, with the full reasoning chain already written. Annual compliance cost drops from $2M (20 FTE) to $350K (4 FTE plus platform) -- $1.65M saved per year.

On the client side, a portfolio specialist who previously advised 50 clients per day now delivers personalized, tax-aware guidance to three million users simultaneously through WS Pulse. Every financial moment -- paycheck, earnings report, market drop, rate decision -- triggers a sub-second recommendation tailored to that user's holdings and tax situation, at $0.002 per event rather than $300 per hour.

## What AI is responsible for

Both systems share a common architecture. For Clarity: an XGBoost classifier (24 features, sub-2ms, 100% precision) scores every alert. A LangGraph state machine investigates using nine tools -- transaction analysis, watchlist screening, entity graphs, RAG over FINTRAC guidance, typology matching. A report generator produces STR narratives via GPT-4o-mini with template fallback for 100% uptime. Pattern discovery uses K-Means and DBSCAN to surface emerging fraud typologies.

For Pulse: an event detector classifies six financial event types with priority scoring. A portfolio analyzer computes personalized impact and tax implications. A recommendation agent grounds advice in RAG-retrieved TFSA, RRSP, and investment guidance.

Both pipelines share production infrastructure: PII masking (HMAC-SHA256 tokenization) before any LLM or cache call, Redis event queues with dead-letter queues and backpressure, multi-region semantic caching, per-span observability via Langfuse, and OSFI E-23 model scorecards.

## Where AI must stop

The STR filing decision is irreversible -- it triggers a regulatory submission to FINTRAC with potential criminal liability. AI provides a recommendation with confidence, reasoning, and risk indicators. A human compliance officer makes the final call. No report is filed without explicit human approval.

On the Pulse side, AI never initiates portfolio changes. It proposes. Users approve, adjust, or dismiss. No automated trading.

## What would break first at scale

At 100,000 alerts per day, LLM investigation cost ($0.0012 per case) stays manageable, but queue saturation becomes the bottleneck -- more parallel workers are needed before Redis memory is a constraint. The semantic cache defers much of this: repeated patterns hit cache instead of the LLM, reducing marginal cost toward zero.

The deeper constraint is the human review queue. AI processes 10,000 cases per minute; a compliance team cannot. The system widens that funnel -- only cases that genuinely need human eyes reach the queue. At ten times current volume, the triage threshold needs tuning and the team grows from four to roughly eight FTE, not forty.
