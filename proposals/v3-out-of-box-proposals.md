# Wealthsimple AI Builders -- Project Proposals V3: Out-of-Box

## What Changed From V1/V2

### The Blind Spot

All 5 proposals in V1/V2 were **internal efficiency plays**: AML investigation, regulatory monitoring, client health scoring, investment due diligence, tax optimization. They answer the question "How does Wealthsimple operate better?" -- but they don't answer the harder question:

> **"Why would a new user choose Wealthsimple over Questrade, their bank, or doing nothing?"**

The job posting says "meaningfully expands what a human can do." V1/V2 expanded what a **compliance officer** can do. V3 asks: what can AI do for the **regular Canadian trying to build wealth**?

### What Wealthsimple's AI Actually Looks Like Today

Research into Wealthsimple's engineering blog, product announcements, and AI disclosures reveals:

- **Willow** (their AI voice assistant) answers 60-70% of customer questions but **explicitly cannot access personal account data**. It's trained on help documentation only.
- Their **engineering AI strategy** is almost entirely focused on developer productivity: 85% Copilot adoption, Cursor rollout, LLM Gateway for internal use, AI-assisted code migrations.
- **Client-facing AI is essentially zero.** No personalized intelligence. No proactive recommendations. No cross-product optimization.
- They're expanding aggressively into **credit cards and loans** (competing with Big Six banks) and need differentiation beyond fees.

**The gap is enormous.** Wealthsimple has 3M+ users and $100B+ in assets, but their client-facing AI is a FAQ bot that can't read your balance. Every proposal below exploits this gap.

### V3 Design Principles

1. **User-facing, not back-office** -- every system directly touches the client experience
2. **Growth-driving** -- creates reasons to join, reasons to stay, reasons to tell friends
3. **AI-native** -- couldn't exist before modern AI (LLMs + agents + embeddings + tool-calling)
4. **Defensible** -- leverages Wealthsimple's unique position (3M Canadian users, multi-product platform, regulatory trust)

---

## Proposal 6: AI-Native "What If" Financial Scenario Engine

### The Problem

Every Canadian has questions that currently require assembling 3-4 professionals:

- "Can I afford a house in Toronto in 2027?"
- "Should I max my TFSA or pay down my student loans?"
- "What happens to my retirement if I take a year off to travel?"
- "My partner and I want to merge finances -- what's the optimal structure?"

Today's answer: book a meeting with a financial advisor ($300/hr), a mortgage broker, maybe an accountant. Or Google it and get generic advice that ignores your tax bracket, RRSP room, existing portfolio, and province.

A human financial advisor can serve 50-100 clients. AI can serve 3 million.

### What the AI System Does

A multi-agent scenario engine that takes a natural-language life question and returns a complete, personalized financial impact analysis across every relevant domain simultaneously.

```
User: "What if I buy a $600K condo in Toronto next year?"

System output:
├── Down payment analysis: FHSA ($40K) + TFSA ($22K) = $62K (10.3%)
├── CMHC insurance: $15,480 (required below 20%)
├── Mortgage: $538K @ 4.2% variable = $2,890/month
│   └── Stress test: passes at 6.2% qualifying rate
├── Tax impact: First-Time Home Buyer Credit ($1,500) + FHSA deduction ($8,000)
├── Portfolio impact: liquidating TFSA costs $0 tax, but loses ~$2,200/yr growth
├── Cash flow: monthly surplus drops from $1,400 to $310
│   └── Emergency fund: 1.1 months (below 3-month minimum)
├── Retirement impact: delays target retirement age by 2.1 years
└── Recommendation: "Possible but tight. Consider waiting 8 months to build
    emergency fund to 3 months, or target $550K to keep monthly surplus above $600."
```

**Agent Architecture:**

| Agent | Role | Tech |
|-------|------|------|
| **Data Fusion** | Assembles complete financial picture from accounts, tax, transactions | LangGraph state machine, tool-calling |
| **Tax Modeling** | Canadian tax brackets, RRSP/TFSA/FHSA rules, provincial differences | Rules engine + LLM for edge cases |
| **Scenario Simulation** | Monte Carlo simulation of outcomes under uncertainty | XGBoost + probabilistic modeling |
| **Narrative Explanation** | Translates numbers into plain-language advice | LLM with RAG over financial guidance |
| **Comparison** | Side-by-side: "buy now vs wait 1 year vs invest the down payment" | Structured output + visualization |

### Human Role

The AI presents analysis and scenarios. The human makes the decision. The AI never says "you should buy" -- it says "here's what happens if you do."

### Critical Human Decision

Whether to execute a major financial life change. The AI can model outcomes but cannot assess emotional readiness, relationship dynamics, career confidence, or risk tolerance beyond what's quantifiable. A $600K mortgage is a 25-year commitment that requires human judgment about life circumstances the AI cannot observe.

### What Breaks First at Scale

**Tax rule complexity.** Canada has federal + provincial tax, with different rules for TFSA/RRSP/FHSA/RESP, plus interaction effects (RRSP withdrawal affects GIS eligibility, TFSA withdrawals don't). As scenarios get more complex (marriage + house + baby + job change), the combinatorial explosion of tax interactions becomes the bottleneck. Needs a formal tax rules engine, not just LLM reasoning.

### Why It Drives User Growth

- **Word of mouth.** "I asked Wealthsimple what happens if I buy a house and it gave me a complete financial plan in 30 seconds." People share this.
- **Sticky.** The more data Wealthsimple has about you, the better the scenarios get. Switching costs increase.
- **Upsell.** Every scenario naturally surfaces product opportunities ("You have $15K in RRSP room -- open an RRSP?").

### Self-Critique

- Requires financial data beyond Wealthsimple (other bank accounts, CRA data, employer pension). Prototype would use self-reported inputs.
- Regulatory gray area: is this "financial advice" (regulated) or "financial information" (not regulated)? Wealthsimple would need legal review. Mitigation: never use the word "should" -- always frame as "here's what happens if."
- Generic scenario engines exist (every bank has a mortgage calculator). The AI-native differentiator is: multi-domain reasoning (tax + investment + mortgage + cash flow simultaneously), natural language input, and personalized-to-YOUR-situation output. Without this, it's just another calculator.

### Feasibility: HIGH

Prototype with self-reported financial profile + simulated Wealthsimple account data. Canadian tax rules are public. Mortgage rules are standard. Monte Carlo simulation is well-understood. 5-day build is realistic.

---

## Proposal 7: AI-Native "Money Moment" Orchestrator

### The Problem

Finance is **event-driven**, not app-driven. Nobody wakes up and thinks "I should open my investment app today." People react to financial events:

- Paycheck arrives
- Market drops 5%
- Tax refund hits
- Rent increases
- Subscription renews for something you forgot about
- You get a raise
- Interest rates change

Currently, these moments pass without action. The paycheck sits in a chequing account earning 0%. The tax refund gets spent on something forgettable. The raise doesn't change the savings rate. This is the **intention gap** -- people know they should invest, save, optimize, but the moment passes before they act.

Mint tried to solve this with dashboards and notifications. It failed because it could show you data but couldn't **reason about your situation** or **take action**.

### What the AI System Does

An autonomous financial orchestration layer that detects events, reasons about their impact on YOUR goals, and executes optimal actions (with human approval thresholds).

```
EVENT: Paycheck deposited ($4,200 after tax)

AI reasoning chain:
├── Fixed obligations: rent ($1,800) + utilities ($180) + insurance ($120) = $2,100
├── Emergency fund: currently 2.8 months → target 3 months → allocate $340
├── TFSA room: $6,500 remaining this year → monthly target $541
├── RRSP: employer match up to 4% → you're at 3% → recommend increase
├── Remaining discretionary: $1,219
└── Action: Auto-transfer $340 to savings, $541 to TFSA (invest in your portfolio)

Notification: "Your paycheck is here. I've set aside $881 toward your goals
(emergency fund + TFSA). You have $1,219 for the month. Sound good?"

User: [Approve] / [Adjust] / [Skip this time]
```

```
EVENT: S&P 500 drops 4.2% in one day

AI reasoning chain:
├── Your equity portfolio: down ~$3,100 today
├── Impact on retirement goal: delays target by 0.3 months (negligible)
├── Historical context: similar drops recover within 60 days 78% of the time
├── Your risk profile: moderate-aggressive, 15+ year horizon
├── Cash available for opportunistic buying: $2,400
└── Action: Hold. No rebalancing needed. Optional: invest $500 from cash at discount.

Notification: "Markets are down today. Your portfolio dropped $3,100 but your
retirement timeline barely moved (0.3 months). This is noise, not signal.
Want to invest $500 from your cash at a 4% discount?"
```

**Agent Architecture:**

| Agent | Role | Tech |
|-------|------|------|
| **Event Detection** | Monitors transactions, market data, calendar, rate changes | Stream processing + anomaly detection |
| **Impact Assessment** | Maps event to user's goals, timelines, and risk profile | LangGraph multi-step reasoning |
| **Action Planning** | Determines optimal response with cost/benefit analysis | Optimization engine + LLM explanation |
| **Execution** | Executes approved actions (transfers, investments, rebalancing) | Tool-calling with human approval gates |
| **Learning** | Tracks which recommendations user accepts/rejects, adapts over time | Feedback loop + preference modeling |

### Human Role

Approve, adjust, or reject every recommended action. Set thresholds for auto-execution ("auto-invest up to $500/paycheck, but ask me for anything larger"). The AI proposes; the human disposes.

### Critical Human Decision

Setting the approval thresholds themselves. Deciding "the AI can auto-invest up to $500 per event without asking me" is a delegation-of-authority decision that requires understanding your own financial stability, risk tolerance, and trust in the system. Getting this wrong (too permissive) could lead to cash flow problems; getting this wrong (too restrictive) defeats the purpose.

### What Breaks First at Scale

**Event correlation.** Individual events are easy. But when paycheck + market drop + rent increase + subscription renewal all happen in the same week, the system needs to reason about priority and cash flow holistically, not event-by-event. A naive system optimizes each event independently and overdrafts the account. Requires a "financial physics engine" that maintains a real-time cash flow model.

### Why It Drives User Growth

- **Paradigm shift.** Transforms Wealthsimple from "app you open" to "financial brain that's always working for you." This is the pitch that gets people to switch from their bank.
- **Retention.** Every auto-invested dollar is a dollar that's harder to move to a competitor. The AI creates stickiness through action, not just information.
- **Viral moments.** "Wealthsimple automatically invested my tax refund into my TFSA. I didn't have to do anything." People talk about this.

### Self-Critique

- "Proactive financial management" has been attempted before (Mint, Digit, Qapital). They all failed or were acquired. The difference here is: those apps could only move money around, not REASON about why. LLMs + tool-calling agents make the reasoning layer possible for the first time. But the ghost of Mint is real -- people may not trust autonomous financial actions.
- Privacy concerns with transaction monitoring. Must be explicitly opt-in with granular controls.
- Approval fatigue: if the AI sends too many notifications, users will disable it. Needs intelligent batching and prioritization.

### Enhancement: Personalized Portfolio Intelligence (Trading Platform Focus)

Wealthsimple's #1 user complaint (per reviews) is **basic research and charting tools** compared to Questrade and Interactive Brokers. Their #1 revenue driver is the **1.5% FX fee on US stock trades**. This means: better research tools → more informed US stock trades → more FX revenue. AI-native research that understands YOUR portfolio is the highest-leverage feature Wealthsimple could build.

The Money Moment Orchestrator should extend beyond life events to include **portfolio-aware market intelligence**:

```
EVENT: Shopify (SHOP) reports Q4 earnings after market close

AI reasoning chain (personalized to YOUR portfolio):
├── You hold: 25 shares of SHOP ($2,150, 8% of portfolio)
├── Earnings result: Revenue $2.8B (+31% YoY), beat estimates by 6%
├── Guidance: Strong, raised FY outlook
├── Key risk: Rising CAC in European markets (you should know this)
├── Your position impact: +$180 pre-market (based on after-hours movement)
├── Peer context: 42% of Wealthsimple SHOP holders added to position after
│   last earnings beat
├── Portfolio consideration: SHOP is now 9.2% of your portfolio (above your
│   5-10% single-stock target)
└── Options: (1) Hold, (2) Trim 5 shares to rebalance, (3) Set trailing stop

Notification: "Shopify beat earnings -- your position is up $180. But it's
now 9.2% of your portfolio, above your 10% target. Want to trim 5 shares
to lock in gains and rebalance?"
```

```
EVENT: Bank of Canada rate decision -- holds at 3.25%

AI reasoning chain:
├── Your variable-rate mortgage estimate: no change
├── Your bond ETF (ZAG): neutral (already priced in)
├── Your GIC maturing next month: current 1-year rate 3.8% (down from 4.2%)
├── High-interest savings: Wealthsimple Cash rate stays at 4.0%
├── Macro view: market expects 2 more cuts this year
└── Action: "Your GIC matures in 28 days. Rates are falling. Consider
    locking in a new 2-year GIC at 3.9% before the next cut."
```

**Additional Agent for Trading Intelligence:**

| Agent | Role | Tech |
|-------|------|------|
| **Earnings Analyzer** | Reads earnings releases and 10-K/10-Q filings for holdings | RAG over financial filings + LLM extraction |
| **Portfolio Health Monitor** | Tracks concentration, sector drift, correlation risk | Real-time portfolio analytics + threshold alerts |
| **News Relevance Filter** | From 1,000 daily financial stories, surfaces only what matters for YOUR 12 holdings | Embedding similarity between news + portfolio |
| **Macro Impact Mapper** | Translates macro events (rate decisions, CPI, employment) into portfolio-specific impact | Economic model + LLM reasoning |

**Why this enhancement matters for Wealthsimple's business:**

1. **Solves the #1 user complaint.** "Basic research tools" is the top pain point. AI that reads earnings reports for you and explains what they mean FOR YOUR POSITION is better than any charting tool.
2. **Drives FX revenue.** Better US stock intelligence → more confident US stock trades → more 1.5% FX conversion fees. A user who understands their AAPL position better trades more.
3. **Premium upsell.** Portfolio health monitoring and earnings intelligence are natural premium features. Drive users toward $100K threshold for Premium.
4. **Retention moat.** An AI that has learned your portfolio preferences, risk tolerance, and trading style over 2 years is very hard to replace by switching to Questrade.

**Self-Critique of Trading Enhancement:**

- **Regulatory risk is real.** Personalized stock analysis that says "consider trimming SHOP" could be interpreted as investment advice (regulated by CSA/IIROC). Must be framed as information, not recommendation. "Here's what the data shows" not "you should do this."
- **Earnings analysis quality.** LLMs can hallucinate financial data. Getting an earnings number wrong ($2.8B vs $28B) in a notification to a user holding the stock is catastrophic. Needs structured data feeds (not scraping), Pydantic validation, and human-in-the-loop for edge cases.
- **Information overload.** A user with 15 holdings doesn't want 15 earnings notifications in one week. Needs intelligent prioritization: only notify on material events (>5% price move, position >3% of portfolio, analyst rating change).
- **Free vs paid.** Wealthsimple needs revenue. Making all this intelligence free cannibalizes Premium. But gating it entirely loses the engagement benefit. Needs a free/premium tiering strategy: basic alerts free, deep analysis and portfolio health premium.

### How This Connects to the AML System (Strategic, Not Forced)

The AML investigation system and the Money Moment Orchestrator are NOT one product. They serve different users (compliance officers vs retail investors). Forcing them into one dashboard would be contrived.

But they share a **strategic thesis** and a **common engineering platform** that together demonstrate something more valuable than either alone: the ability to think across Wealthsimple's entire business.

**The strategic thesis:**

> Wealthsimple needs AI on both sides of the house. On the compliance side, AI reduces the cost and risk of mandatory regulatory processes (AML). On the client side, AI creates differentiated experiences that drive growth. An AI Builder who can think across both sides -- and sees the shared infrastructure between them -- is more valuable than one who can only do one.

**Shared infrastructure (genuine, not forced):**

| Component | AML System | Money Moment Orchestrator |
|-----------|-----------|--------------------------|
| **Event detection** | Transaction triggers AML alert | Transaction triggers financial moment |
| **Behavioral baseline** | "Is this activity normal for this client?" | "Is this spending normal for this user?" |
| **Client profiling** | Risk profile for compliance | Financial profile for personalization |
| **Transaction analysis** | Pattern matching for typologies | Pattern matching for spending/income |
| **RAG** | FINTRAC regulations + STR guidance | Financial guidance + tax rules + market data |
| **Multi-agent orchestration** | LangGraph investigation pipeline | LangGraph event reasoning pipeline |
| **Observability** | Langfuse traces per investigation | Langfuse traces per recommendation |
| **Caching** | Redis for triage + entity lookups | Redis for portfolio state + market data |

**What this means for the application:**

Building BOTH systems (even if only one is fully prototyped and the other is a detailed architecture) shows:

1. **Systems thinking across the company** (the job posting literally asks for this)
2. **Comfort with compliance AND product** (rare -- most engineers avoid compliance)
3. **Infrastructure-level thinking** (shared platform, not just features)
4. **Business acumen** (understands both cost reduction AND revenue growth)

### Feasibility: HIGH

Prototype with simulated events (paycheck, market data, rate changes, earnings) + synthetic user profiles and portfolio holdings. LangGraph handles multi-step reasoning. Earnings data from public APIs (Yahoo Finance, SEC EDGAR). The approval UI is a Streamlit interface. 5-day build is realistic for core event orchestration + 2-3 event types.

---

## Proposal 8: AI-Native Peer Intelligence Network

### The Problem

Canadians are financially isolated. Nobody talks about money. The result: people have no idea if they're doing well, doing poorly, or doing average. They can't benchmark themselves because there's no benchmark.

- "Is $50K in savings at 28 good or bad?"
- "How much should I be investing per month?"
- "Am I the only one who hasn't bought a house yet?"
- "What do people with my income actually invest in?"

The only answers available are generic articles ("Canadians should save 20% of income") that ignore age, city, income, career, and life stage.

### What the AI System Does

Wealthsimple has something no competitor has: **the financial behavior of 3 million Canadians.** This proposal turns that data into a defensible competitive moat.

```
User opens app. Sees:

"People like you" (28, Toronto, tech, $85K income):
├── Median monthly savings: $1,100/month (you: $800 → below median)
├── TFSA utilization: 73% have one, avg balance $22,400 (you: $12,000)
├── Investment mix: 65% equities, 20% bonds, 15% crypto (you: 90% equities)
├── Top action this month: 34% increased RRSP contribution (tax season)
└── Insight: "You save less than peers, but your equity allocation is more
    aggressive -- which historically outperforms over 10+ year horizons.
    Consider increasing savings rate by $200/month to match median."
```

**Agent Architecture:**

| Agent | Role | Tech |
|-------|------|------|
| **Cohort Engine** | Segments 3M users into meaningful peer groups | K-Means, DBSCAN on financial behavior features |
| **Privacy Layer** | Differential privacy + k-anonymity (minimum cohort size: 500) | Noise injection, aggregation thresholds |
| **Insight Generator** | Identifies statistically significant patterns within cohorts | Statistical testing + anomaly detection |
| **Narrative Agent** | Translates statistics into personalized, actionable insights | LLM with guardrails against negative framing |
| **Behavioral Nudge** | Identifies the single highest-impact action for this user | Predictive modeling (what did similar users do that worked?) |

### Human Role

Users choose how much peer data they want to see. They decide whether to act on any insight. They can opt out of contributing their anonymized data to cohorts.

### Critical Human Decision

Whether to change financial behavior based on peer comparison. Social proof is powerful but can be misleading -- "most people your age have a mortgage" doesn't mean YOU should have a mortgage if your career is unstable or you plan to move cities. The AI presents the data; the human must filter it through their own life context.

### What Breaks First at Scale

**Survivorship bias and selection bias.** Wealthsimple's user base skews young, tech-savvy, and urban. "People like you" may not actually be representative of all Canadians in that demographic -- just the ones who use Wealthsimple. As the user base grows and diversifies, cohort definitions need continuous recalibration. Also: successful users are more likely to stay on the platform, creating survivorship bias in "what works" recommendations.

### Why It Drives User Growth

- **Moat.** Only Wealthsimple has this data at scale in Canada. Questrade can't replicate it. Banks won't share theirs. This is a genuine competitive advantage that gets stronger with every new user (network effect).
- **Engagement.** People are endlessly curious about how they compare to peers. This drives daily app opens (not just when making trades).
- **Acquisition.** "See how you compare to 3 million Canadians" is a compelling ad hook. The insights themselves are shareable content.
- **Behavior change.** Social proof is the most effective nudge in behavioral economics. Showing someone that 73% of their peers have a TFSA is more persuasive than any article about TFSAs.

### Self-Critique

- **Privacy is the elephant in the room.** Even with differential privacy and aggregation, the perception of "Wealthsimple is analyzing my finances and comparing me to others" could feel invasive. Must be opt-in, transparent, and framed positively (never shaming). Needs rigorous privacy engineering, not just promises.
- **Selection bias.** Wealthsimple's user base is not representative of all Canadians. Cohort insights that say "people like you invest in crypto" may reflect platform-specific behavior, not general wisdom.
- **Negative emotional impact.** Showing someone they're below the median savings rate could be demotivating rather than motivating. Framing must be carefully designed with behavioral psychologists, not just engineers.
- **Regulatory risk.** Depending on how insights are framed, this could cross into "financial advice" territory. "People like you invest 65% in equities" could be interpreted as a recommendation.

### Feasibility: MEDIUM-HIGH

Prototype with synthetic cohort data (simulated 3M users with realistic demographics). K-Means/DBSCAN segmentation is straightforward. Differential privacy adds complexity but is well-documented. The narrative generation with positive framing is an interesting LLM guardrails challenge. 5-day build is achievable with simulated data.

---

## Proposal 9: AI-Native Financial Document Intelligence Hub

### The Problem

Every Canadian interacts with dozens of financial documents per year:

- **Tax:** T4 (employment income), T3 (investment income), T5 (interest), NOA (Notice of Assessment)
- **Banking:** Mortgage statements, LOC statements, credit card statements from other institutions
- **Insurance:** Home, auto, life insurance policies and renewals
- **Government:** CPP statements, OAS projections, RESP grant confirmations
- **Legal:** Separation agreements, wills, power of attorney

Currently, these documents arrive, get filed (or lost), and are never analyzed holistically. Nobody has a complete picture of their financial life across all institutions. The financial advisor who could synthesize all this costs $300/hr and serves 50 clients.

### What the AI System Does

Upload any financial document. The AI extracts structured data, explains what it means for YOUR situation, identifies optimization opportunities, and offers to take action.

```
User uploads: TD Mortgage Statement (PDF)

AI output:
├── Extracted: $412,000 remaining @ 4.89% fixed, 3 years remaining in term
├── Monthly payment: $2,340 | Prepayment privileges: 15% lump sum annually
├── Analysis:
│   ├── "Your rate (4.89%) is 0.6% above current best rates (4.29%)"
│   ├── "You have $61,800 in unused prepayment room this year"
│   ├── "Prepaying $10,000 saves $8,200 in interest over remaining amortization"
│   └── "At renewal in 3 years, switching could save ~$180/month"
├── Action: "You have $14,200 in your Wealthsimple savings earning 4.0%.
│   Prepaying $10,000 toward your mortgage effectively earns 4.89% risk-free.
│   Want to set a reminder for your renewal date?"
└── Cross-product: "Also, your NOA shows $22,000 RRSP room. An RRSP
    contribution would reduce your marginal tax rate and free up cash flow."
```

**Agent Architecture:**

| Agent | Role | Tech |
|-------|------|------|
| **Document Extraction** | OCR + LLM to parse any financial document into structured data | Multi-modal LLM (GPT-4V or open-source) + Pydantic validation |
| **Cross-Reference** | Maps extracted data against user's Wealthsimple accounts | Tool-calling + data fusion |
| **Optimization** | Identifies opportunities: rate comparison, prepayment, contribution room | Rules engine + LLM reasoning |
| **Action** | Proposes specific, executable next steps within Wealthsimple | Structured output + approval workflow |
| **Knowledge Base** | RAG over Canadian financial product rules, tax guidance, rate data | ChromaDB + regulatory document embeddings |

### Human Role

Upload documents voluntarily. Review AI analysis. Decide whether to act on any recommendation. Delete uploaded documents at any time.

### Critical Human Decision

Whether to act on cross-institutional optimization recommendations. Moving money from a mortgage prepayment to an RRSP depends on assumptions about future income, career stability, and risk tolerance that the AI cannot fully assess. The AI can model the math; the human must decide if the math matches their life.

### What Breaks First at Scale

**Document format diversity.** Financial documents have hundreds of formats across institutions. A TD mortgage statement looks different from an RBC one. Insurance policies vary wildly. The extraction agent needs to handle this variety without hallucinating data. One wrong number (extracting $41,200 instead of $412,000) could lead to catastrophically wrong advice.

### Why It Drives User Growth

- **Acquisition funnel.** People come for the free document analysis. They stay because now Wealthsimple understands their complete financial picture. It's a trojan horse for platform adoption.
- **Data moat.** Every uploaded document gives Wealthsimple data about the user's financial life OUTSIDE Wealthsimple. This powers better recommendations across all products.
- **Switching trigger.** "Your TD savings account earns 0.5%. Your Wealthsimple cash account earns 4.0%. That's $1,400/year you're leaving on the table." The AI actively identifies reasons to switch.

### Self-Critique

- **OCR + LLM document reading is becoming commoditized.** Every bank will have this eventually. The value isn't in extraction (everyone can do that) -- it's in the cross-product action layer (only Wealthsimple can offer to move your money right now). The prototype must demonstrate the ACTION, not just the extraction.
- **Competitor sensitivity.** Ingesting and analyzing documents from TD, RBC, etc. and then recommending people move their money is aggressive. Not illegal, but could generate competitive backlash.
- **Data security.** Handling other institutions' documents raises the security bar significantly. Must be encrypted at rest, processed in-memory only, deletable on demand.

### Feasibility: HIGH

Prototype with synthetic financial documents (generated PDFs). Multi-modal LLM (GPT-4V) handles extraction. Rules engine for Canadian financial products is bounded. Action recommendations are straightforward. 5-day build is realistic if document variety is limited to 3-4 types.

---

## Proposal 10: AI-Native Retirement Time Machine

### The Problem

"Retirement" is abstract. $500,000 in a retirement account is just a number. People can't feel it. They can't visualize it. As a result, they don't act on it.

Traditional retirement calculators ask for 15 inputs and return a single number. Nobody uses them twice. They don't account for Canadian-specific complexity (CPP, OAS, GIS, TFSA/RRSP interaction, provincial tax). They don't update when your life changes.

### What the AI System Does

A living, breathing model of your financial future that updates continuously and responds to natural-language questions.

```
Dashboard:
┌─────────────────────────────────────────────────────────────┐
│  YOUR RETIREMENT TRAJECTORY                                 │
│                                                             │
│  Current path: retire at age 64.2 with $1.2M              │
│  ████████████████████████████░░░░░░░  (73% funded)         │
│                                                             │
│  Highest-impact lever: Increase RRSP by $300/month         │
│  → Retire 1.8 years earlier | Save $42K in lifetime tax    │
│                                                             │
│  What changed this month:                                   │
│  ├── Market returns: +1.2% → retirement moved 0.2yr closer │
│  ├── Spending increase: +$200/month → moved 0.4yr further  │
│  └── Net change: retirement delayed by 0.2 years           │
│                                                             │
│  Ask me anything: [What if I take a year off in 2028?    ] │
└─────────────────────────────────────────────────────────────┘
```

```
User: "What if I take a year off to travel in 2028?"

AI response:
├── Income gap: $85,000 (1 year salary)
├── Spending during travel: estimated $40,000 (based on your current spending patterns)
├── Portfolio impact: miss $7,200 in contributions + $3,100 in employer RRSP match
├── CPP impact: reduced by ~$1,200/year in retirement (lower pensionable earnings)
├── Tax benefit: lower income year = lower tax bracket = good year for RRSP withdrawal
├── Retirement impact: delayed by 1.4 years (from 64.2 to 65.6)
├── Mitigation: "If you save an extra $400/month for the 24 months before departure,
│   the net delay drops to 0.6 years"
└── Bottom line: "The math says it costs 1.4 years of retirement. But 24 months
    of pre-saving cuts that to 0.6 years. That's a very reasonable price for a
    year of travel at 32."
```

**Agent Architecture:**

| Agent | Role | Tech |
|-------|------|------|
| **Financial Model** | Maintains real-time model of income, spending, assets, liabilities | Continuously updated state machine |
| **Monte Carlo** | Simulates 10,000 retirement scenarios with market uncertainty | NumPy + custom simulation engine |
| **Canadian Tax Engine** | Models RRSP, TFSA, CPP, OAS, GIS interactions by province | Rules engine with LLM edge-case handler |
| **Scenario Agent** | Answers natural-language "what if" questions | LangGraph + tool-calling |
| **Narrative Agent** | Explains results in emotionally resonant language | LLM with positive framing guardrails |

### Human Role

Set goals, answer lifestyle questions, make decisions. The AI models futures; the human chooses which future to pursue.

### Critical Human Decision

Choosing between competing life priorities. "Travel now vs retire earlier" is not a financial question -- it's a values question. The AI can quantify the tradeoff, but choosing between experiences at 32 and security at 65 requires human judgment about what makes a life worth living.

### What Breaks First at Scale

**Assumption sensitivity.** Long-horizon projections are extremely sensitive to assumptions about market returns, inflation, and government policy. A 1% difference in assumed returns changes the retirement date by 5+ years. The system must communicate uncertainty honestly (show the range, not just the point estimate) and update assumptions as economic conditions change. Users who see their retirement date jump around wildly will lose trust.

### Why It Drives User Growth

- **Emotional hook.** "I can see exactly when I can retire" is deeply motivating. People who feel in control of their retirement are more engaged and more likely to increase savings.
- **Shareability.** "Wealthsimple showed me I can retire 3 years earlier if I just increase my TFSA by $200/month." This is the kind of insight people text to friends.
- **Retention.** The model gets more accurate with more data. Leaving Wealthsimple means losing your retirement model. This is stickiness through value, not lock-in.
- **Daily engagement.** Monthly "here's what changed" updates give people a reason to open the app even when they're not trading.

### Self-Critique

- **Every bank has a retirement calculator.** The AI-native difference must be visceral: continuous updates, natural-language questions, emotional narrative, and integration with ACTUAL account data (not self-reported). Without this integration, it's just a nicer calculator.
- **Projection anxiety.** Showing someone their retirement date moves when markets drop could cause panic selling -- the opposite of what a good advisor would do. Needs calm, contextualized framing.
- **Canadian tax complexity.** CPP, OAS, and GIS have complex clawback rules that interact with each other. The RRSP/RRIF conversion at 71, TFSA contribution room tracking, pension income splitting -- getting this right is a serious rules-engine challenge.

### Feasibility: MEDIUM-HIGH

Monte Carlo simulation is well-understood. Canadian tax rules are public. The challenge is integrating it all into a coherent model with good natural-language interaction. 5-day prototype would simulate 3-4 scenarios with a simplified tax model. Full tax complexity is a 2-3 month effort.

---

## Proposal 11: AI-Native Financial Guardian ("Anti-Bank")

### The Problem

Banks profit when you're financially disorganized. Overdraft fees, dormant account charges, high-interest debt, expensive insurance -- these are revenue centers for incumbents. Nobody is on the consumer's side.

Wealthsimple's brand is already "the anti-bank." But right now, that means lower fees and a nicer app. What if AI made it literal -- an agent that actively hunts for money you're losing and fights to get it back?

### What the AI System Does

A financial guardian agent that continuously monitors your financial life for waste, inefficiency, and missed opportunities -- then takes action.

```
WEEKLY FINANCIAL HEALTH CHECK:

Savings found this week: $127.50
├── Subscription audit: Spotify ($11.99) + Apple Music ($10.99) = overlap detected
│   └── "You used Spotify 47 times and Apple Music 0 times this month. Cancel Apple Music?"
├── Fee detection: BMO chequing account charged $4.95 monthly fee
│   └── "Your Wealthsimple Cash account has no fees. You've paid $59.40 in fees this year."
├── Rate optimization: Emergency fund ($8,000) in RBC savings @ 0.5%
│   └── "Move to Wealthsimple Cash @ 4.0%. That's $280/year more in interest."
├── Insurance check: Auto insurance renewal next month
│   └── "Based on 3M users, people with your profile pay 15% less on average.
│        Consider shopping around."
└── Tax opportunity: $3,200 in unused TFSA room + capital gains from non-registered
    └── "Selling $3,200 from your non-registered account and re-buying in TFSA
         shelters future gains. Net tax cost now: $0 (loss positions available to offset)."

Lifetime savings from guardian: $4,847/year
```

**Agent Architecture:**

| Agent | Role | Tech |
|-------|------|------|
| **Subscription Auditor** | Detects recurring charges, identifies duplicates and unused services | Transaction pattern analysis + categorization LLM |
| **Fee Hunter** | Identifies bank fees, penalties, unnecessary charges across institutions | Rule-based detection + cross-product comparison |
| **Rate Optimizer** | Compares user's rates (savings, mortgage, insurance) against benchmarks | Regression model on cohort data + rate feeds |
| **Tax Optimizer** | Identifies TFSA/RRSP room, tax-loss harvesting, income splitting opportunities | Canadian tax rules engine + LLM reasoning |
| **Action Agent** | Executes approved optimizations (cancel, transfer, rebalance) | Tool-calling with approval gates |

### Human Role

Review weekly digest. Approve or dismiss each finding. Set preferences ("never cancel streaming subscriptions automatically," "always optimize tax positions"). Override any action.

### Critical Human Decision

Whether to act on rate/provider switching recommendations. Changing banks, insurance providers, or canceling services has consequences beyond the numbers -- relationship value, convenience, bundled discounts, and personal preference. The AI optimizes for dollars; the human optimizes for life.

### What Breaks First at Scale

**False positives in subscription auditing.** Detecting "duplicate" subscriptions is harder than it looks -- Spotify for music + Apple Music for podcasts might both be used. Annual subscriptions look dormant for 11 months. Shared family plans complicate per-user analysis. False positives (recommending cancellation of something the user values) destroy trust fast.

### Why It Drives User Growth

- **Quantifiable value.** "Wealthsimple saved me $4,847 this year" is the most powerful retention metric possible. It's also an ad campaign that writes itself.
- **Anti-bank positioning.** Every dollar the guardian saves reinforces Wealthsimple's brand as the anti-bank. Banks charge fees; Wealthsimple finds them and fights them.
- **Viral mechanics.** "Your bank charged you $59 in fees last year. Wealthsimple charges $0." This is the kind of insight that gets screenshotted and shared.
- **Product cross-sell.** Every optimization surfaces a Wealthsimple product: Cash (vs fee-charging bank), TFSA (vs non-registered), direct indexing (vs mutual funds).

### Self-Critique

- **Most aggressive proposal.** "Spending surveillance" could feel invasive even when opt-in. Privacy perception matters as much as privacy reality.
- **Conflict of interest.** Wealthsimple recommending you move money FROM other institutions TO Wealthsimple is obviously self-interested. Needs transparent disclosure: "We benefit when you move money here. Here are the numbers -- you decide."
- **Legal questions.** Insurance comparison and "shop around" recommendations could be interpreted as insurance brokering (regulated). Fee comparison across institutions needs careful framing.
- **Overreach risk.** Telling someone to cancel a subscription they like (even if they haven't used it recently) feels paternalistic. Must be suggestions, never commands. Tone matters enormously.

### Feasibility: MEDIUM

Transaction categorization and subscription detection are well-studied. The challenge is the breadth -- fee detection, rate comparison, tax optimization, and insurance analysis each require domain-specific logic. A 5-day prototype would focus on 2-3 of these (subscription audit + fee detection + TFSA optimization) and leave the rest for a roadmap.

---

## Cross-Comparison Matrix

| Dimension | Proposal 6: What If Engine | Proposal 7: Money Moment + Portfolio Intelligence | Proposal 8: Peer Intelligence | Proposal 9: Document Hub | Proposal 10: Retirement Machine | Proposal 11: Financial Guardian |
|-----------|---------------------------|--------------------------------------------------|-------------------------------|--------------------------|-------------------------------|-------------------------------|
| **User Growth Impact** | High (word of mouth) | Very High (paradigm shift + trading engagement) | High (network effect / moat) | High (acquisition funnel) | Medium-High (engagement) | Very High (quantifiable value) |
| **AI-Nativeness** | High (multi-domain reasoning) | Very High (proactive autonomy + portfolio reasoning) | High (real-time cohort + narrative) | Medium-High (doc understanding + action) | Medium (simulation + NL explanation) | High (continuous monitoring + action) |
| **Technical Depth** | High (Monte Carlo + tax engine + LLM) | Very High (event stream + earnings RAG + portfolio analytics + execution) | High (clustering + differential privacy + LLM) | High (multi-modal + cross-product) | Medium-High (simulation + tax rules) | Medium-High (pattern detection + rules) |
| **Revenue Alignment** | Medium (product upsell) | Very High (drives US trades → FX revenue, Premium upsell) | Medium (engagement → stickiness) | Medium (cross-sell on analysis) | Low (indirect) | Medium (product cross-sell) |
| **Novelty / Non-Obvious** | Medium (scenario tools exist) | Very High (no Canadian fintech does personalized portfolio AI) | Very High (nobody does this yet) | Medium (doc OCR is trending) | Medium (calculators exist) | High (anti-bank-as-AI-agent is new) |
| **Demo Potential (2-3 min)** | Very High (one question, stunning answer) | Very High (earnings event → personalized analysis → action) | High (visual cohort comparison) | High (upload doc → instant analysis) | High (interactive sliders + scenarios) | Very High (weekly savings report) |
| **5-Day Feasibility** | High | High (core events) / Medium (full portfolio intelligence) | Medium-High | High | Medium-High | Medium |
| **Defensible Moat** | Low (any fintech can build this) | High (AI that knows YOUR portfolio is hard to replicate) | Very High (requires 3M users' data) | Low (commoditizable) | Low (any fintech can build this) | Medium (requires transaction access) |
| **Complements AML System** | Low | Very High (shared event/profiling/RAG infrastructure) | Medium | Low | Low | Medium |

---

## Strategic Recommendation

### The Strongest Application Narrative: AML + Enhanced Proposal 7

The single most compelling story for the Wealthsimple AI Builders application is:

> "I built two AI systems that address both sides of Wealthsimple's business:
>
> **Back-office:** An AML investigation agent that auto-closes 80% of false positive alerts, conducts full investigations in 17ms, and generates FINTRAC-compliant STR reports -- saving ~$1.5M/year and freeing compliance officers for complex cases.
>
> **Client-facing:** A Money Moment Orchestrator with personalized portfolio intelligence that turns Wealthsimple from 'an app you open' into 'a financial brain that works for you' -- driving engagement, US stock trading (FX revenue), and Premium upsells.
>
> Both run on shared infrastructure: event-driven architecture, behavioral baselines, RAG knowledge retrieval, multi-agent orchestration, full observability."

This narrative demonstrates:
1. **Systems thinking across the company** (compliance + product, not just one)
2. **Business acumen** (cost reduction AND revenue growth)
3. **Infrastructure thinking** (shared platform, not disconnected features)
4. **Technical breadth** (ML classifiers + LangGraph agents + RAG + real-time events + LLM + observability)
5. **Regulatory awareness** (FINTRAC, PCMLTFA, CSA, AIDA, OSFI E-23)

### Realistic Scope

Given time constraints, the recommendation is:
- **Fully prototype:** The AML system (already built) + a targeted demo of Proposal 7 showing 2-3 event types (paycheck orchestration + earnings intelligence + market event response)
- **Architecture only:** The remaining 4 proposals as a "future roadmap" section in the dashboard, showing strategic thinking without pretending to have built everything

### Alternative Paths

**If pivoting entirely from AML:** Proposal 8 (Peer Intelligence Network) is the most defensible -- it leverages Wealthsimple's 3M-user data moat and creates a network effect no competitor can replicate.

**If optimizing for demo wow-factor:** Proposal 6 (What If Engine) produces the most visually stunning 2-3 minute demo. One natural language question → complete multi-domain financial analysis.

**If going bold:** Proposal 11 (Financial Guardian / "Anti-Bank") is the most memorable. "This app saved me $4,847/year" is a growth engine that aligns perfectly with Wealthsimple's brand.

---

## Wealthsimple Pain Points Summary (Research-Backed)

| Pain Point | Source | How AI Addresses It |
|-----------|--------|-------------------|
| Basic research/charting tools vs competitors | User reviews, comparison sites | Proposal 7: AI reads earnings reports and explains impact on YOUR position |
| 1.5% FX fee makes US trading expensive | User complaints | Better intelligence → more confident, higher-value US trades → fee becomes "worth it" |
| AML/compliance costs scale linearly with user growth | Industry standard | AML System: 80% auto-close rate, 17ms/alert, ~$0.005/investigation |
| Willow (AI chatbot) can't access personal account data | Wealthsimple AI disclosure | Both systems: AI that actually knows your portfolio, transactions, and goals |
| Customer support complaints | User reviews | Proposal 7: proactive intelligence reduces support tickets ("why did my portfolio drop?") |
| Limited differentiation from 14+ competitors | Market analysis | Proposal 8: Peer Intelligence is a data moat. Proposal 7: Portfolio AI is a switching cost |
| Premium requires $100K+ (hard threshold) | Product documentation | Proposal 7: AI surfaces opportunities to consolidate assets, naturally driving toward Premium |

---

## Key Takeaway

V1/V2 asked: "How does AI make Wealthsimple's operations better?"
V3 asks: "How does AI make Wealthsimple the obvious choice for every Canadian?"

The answer is both:
- **Operations:** AI that makes compliance faster, cheaper, and more accurate (AML system -- already built)
- **Product:** AI that actually knows you, works for you, and grows with you (Proposal 7 + enhancements)

The candidate who can think across both sides -- and build shared infrastructure to power them -- is the one Wealthsimple should hire.

---

*V3 generated from competitive analysis (Questrade, Moomoo, Webull, Big Six), Wealthsimple product research (Premium, Willow, trading tools), engineering blog review (LLM Gateway, AI strategy), user pain point analysis, and revenue model research.*
*Previous iterations: V1 (initial proposals), V2 (refined with cost savings + technical depth), V3 (out-of-box, user-growth focused, enhanced Proposal 7 with trading/portfolio intelligence).*
