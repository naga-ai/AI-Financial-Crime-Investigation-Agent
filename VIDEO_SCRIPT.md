# WS Intelligence Platform — 3-Minute Video Script

**Total time: ~3 minutes**
Directions in [brackets] tell you what to show on screen.

---

## INTRO (0:00–0:20)

[Show: Platform Overview page]

"This is the WS Intelligence Platform — two AI systems built on shared infrastructure. One automates AML compliance investigation for the operations team. The other delivers personalised financial guidance to every client. Let me walk you through both."

---

## WS CLARITY — COMPLIANCE (0:20–1:30)

[Show: Platform Overview page, scroll to WS Clarity card]

"The first system is WS Clarity. Right now, a compliance analyst spends about 45 minutes per AML alert — pulling transaction data, screening watchlists, checking typologies, writing a report. And roughly 80% of those alerts turn out to be false positives."

[Click: Executive Summary in sidebar]

"Here's the pipeline. We have 315 synthetic AML alerts, matching real-world distributions."

[Click: Run Pipeline button, watch the animation]

"When we run the pipeline, here's what happens. An XGBoost triage classifier — 24 hand-engineered features, sub-2ms inference — scores every alert. Low-risk false positives are auto-closed with documented confidence. The remaining cases go into a LangGraph investigation agent with nine tool nodes."

[Wait for results to appear, point at KPIs]

"You can see the results — auto-close rate, investigation count, average latency. The ROI panel shows the estimated hours and cost saved per batch."

[Click: Investigation Queue in sidebar]

"This is the investigation queue. Each case has a risk score, risk factors, and the full investigation steps. You can drill into any case, see the transaction history, the FINTRAC typology matches, the tools that ran."

[Click: STR Report Review in sidebar, click on a report]

"And here are the STR reports. The AI generates a full regulatory narrative. A compliance officer reviews it here — approve, reject, or escalate. Nothing gets filed without a human decision."

[Click: Model Intelligence in sidebar]

"The model page shows the XGBoost performance — precision, recall, F1 across five folds. Feature importance. And the post-training roadmap — from the current GPT-4o-mini setup through SFT, DPO, and eventually GRPO on a self-hosted model."

---

## WS PULSE — CLIENT AI (1:30–2:10)

[Click: Pulse Intelligence in sidebar]

"The second system is WS Pulse. Every financial moment — a paycheck, an earnings report, a market dip — triggers personalised guidance."

[Click: Run Pulse button, watch animation]

"The pipeline detects the event, masks PII, runs a LangGraph agent with portfolio analysis and RAG retrieval over Canadian tax rules, then generates a plain-language recommendation via GPT-4o-mini."

[Wait for results, scroll through recommendation cards]

"Each user gets a card with the recommendation, the estimated value, a confidence score, and the action. Some hit the semantic cache — you can see the cache hit rate and latency difference."

---

## PATTERN DISCOVERY & OBSERVABILITY (2:10–2:40)

[Click: Pattern Discovery in sidebar]

"Pattern Discovery runs unsupervised clustering — K-Means or DBSCAN — on completed investigations to find emerging fraud typologies. Each data point is an individual investigation, coloured by cluster."

[Click: Run Clustering, show scatter plot and cluster cards]

"You can see the risk-score distribution, the cluster profiles, and the characteristics that define each group."

[Click: Observability & Traces in sidebar]

"Finally, observability. Every LLM call, every tool invocation — full trace with cost and latency. This is how we track real production spend per case."

---

## ARCHITECTURE & CLOSE (2:40–3:00)

[Click: Architecture in sidebar]

"Both pipelines share the same infrastructure — Redis for event queuing and caching, ChromaDB for RAG, Langfuse for observability, PII masking on every LLM call."

[Pause on the architecture diagram]

"The core principle is simple: AI investigates, AI recommends, but humans decide. Every critical action requires approval. That's the WS Intelligence Platform."

---

**Tips for recording:**
- Speak at a steady, natural pace — not rushed
- Let each page load fully before narrating its content
- Pause briefly (~1 second) between sections for clean edits
- Keep your mouse movements deliberate — hover on key numbers when you mention them
