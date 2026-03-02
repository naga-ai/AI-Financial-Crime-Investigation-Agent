'use client';

// ─── Static data ────────────────────────────────────────────────────

const CLARITY_AGENTS = [
    {
        name: 'Triage Agent',
        desc: 'XGBoost classifier — 24 features, sub-2ms inference, 100% precision. Auto-closes 80% of false positives.',
        color: 'green',
    },
    {
        name: 'Investigation Agent',
        desc: 'LangGraph state machine — 9 tool nodes: transaction analysis, watchlist screening, entity graph, RAG retrieval, typology matching.',
        color: 'teal',
    },
    {
        name: 'Report Generator',
        desc: 'GPT-4o-mini + template fallback — produces FINTRAC-compliant STR narratives with structured risk indicators.',
        color: 'amber',
    },
    {
        name: 'Pattern Discovery Agent',
        desc: 'K-Means / DBSCAN unsupervised clustering — identifies emerging fraud typologies across 10 FINTRAC-aligned categories.',
        color: 'blue',
    },
];

const PILOT_AGENTS = [
    {
        name: 'Event Detector',
        desc: '6 financial event types — paycheck, earnings, market drop, rate change, dividend, rebalance. Priority scoring for queue.',
        color: 'teal',
    },
    {
        name: 'Portfolio Analyzer',
        desc: 'Personalized impact analysis per user\'s holdings — tax implications, concentration risk, account-type optimization.',
        color: 'blue',
    },
    {
        name: 'Recommendation Agent',
        desc: 'RAG-grounded personalized guidance — TFSA/RRSP-aware, plain-language, actionable. Grounds advice in regulatory context.',
        color: 'green',
    },
    {
        name: 'Narrative Agent',
        desc: 'Plain-language financial briefing — converts portfolio analysis into clear, jargon-free recommendations for any user.',
        color: 'purple',
    },
];

const CLARITY_FLOW = [
    { label: 'AML Alert', sub: 'Ingestion', color: 'accent-blue' },
    { label: 'Triage Agent', sub: 'XGBoost · <2ms', color: 'accent-green' },
    { label: 'Investigation', sub: 'LangGraph · 9 tools', color: 'accent-teal' },
    { label: 'Report Generator', sub: 'GPT-4o-mini', color: 'accent-amber' },
    { label: 'Human Review', sub: 'Approve / Escalate', color: 'accent-amber', human: true },
    { label: 'FINTRAC Filing', sub: 'Regulatory output', color: 'accent-red' },
];

const PILOT_FLOW = [
    { label: 'Financial Event', sub: 'Paycheck / Earnings / Drop', color: 'accent-blue' },
    { label: 'Event Detector', sub: '6 types · priority score', color: 'accent-teal' },
    { label: 'Portfolio Analyzer', sub: 'Tax-aware impact', color: 'accent-green' },
    { label: 'RAG Retrieval', sub: 'TFSA / RRSP rules', color: 'accent-purple' },
    { label: 'Recommendation', sub: 'GPT-4o-mini', color: 'accent-amber' },
    { label: 'Human Approval', sub: 'Approve / Adjust / Dismiss', color: 'accent-amber', human: true },
];

const CAPABILITIES = [
    {
        area: 'ML Model',
        description: 'XGBoost triage classifier — 24 engineered features, cross-validated, OSFI E-23 aligned scorecard with bias analysis.',
        technology: 'XGBoost · scikit-learn',
        badge: 'Production',
        badgeColor: 'badge-green',
    },
    {
        area: 'LLM Integration',
        description: 'GPT-4o-mini for STR narrative generation and portfolio recommendations. Template fallback ensures 100% uptime without API key.',
        technology: 'OpenAI GPT-4o-mini · LangChain',
        badge: 'Production',
        badgeColor: 'badge-green',
    },
    {
        area: 'Multi-Agent Orchestration',
        description: 'LangGraph state machines for both pipelines — conditional routing, parallel tool calls, graceful error recovery.',
        technology: 'LangGraph · LangChain',
        badge: 'Production',
        badgeColor: 'badge-green',
    },
    {
        area: 'Semantic Cache',
        description: 'Multi-region TTL caching — separate policies for triage (1h), investigation (24h), regulatory context (7d). Near-zero marginal cost at scale.',
        technology: 'Redis 7 · in-memory fallback',
        badge: 'Production',
        badgeColor: 'badge-green',
    },
    {
        area: 'RAG / Knowledge Base',
        description: 'Semantic search over FINTRAC regulatory guidance and Canadian tax/investment principles. Grounds LLM outputs in authoritative sources.',
        technology: 'ChromaDB · sentence-transformers',
        badge: 'Production',
        badgeColor: 'badge-green',
    },
    {
        area: 'Observability',
        description: 'Per-span cost tracking, latency distribution (P50–P99), trace explorer. Every LLM call, tool use, and cache hit is recorded.',
        technology: 'Langfuse · local telemetry bus',
        badge: 'Production',
        badgeColor: 'badge-green',
    },
    {
        area: 'PII Masking',
        description: 'Field-level tokenization before any LLM call, cache write, or RAG query. Deterministic tokens enable joins. Full audit log.',
        technology: 'Custom tokenizer · Redis audit log',
        badge: 'Built',
        badgeColor: 'badge-teal',
    },
    {
        area: 'Event Queue',
        description: 'Priority-sorted event ingestion with consumer groups, DLQ after 3 retries, idempotency via event hash, backpressure management.',
        technology: 'Redis Streams',
        badge: 'Built',
        badgeColor: 'badge-teal',
    },
    {
        area: 'Compliance & Governance',
        description: 'FINTRAC-aligned alert typologies, OSFI E-23 model risk management, AIDA / EU AI Act governance framework. Human-in-the-loop at every critical decision.',
        technology: 'FINTRAC · OSFI E-23 · AIDA',
        badge: 'Production',
        badgeColor: 'badge-green',
    },
    {
        area: 'Pattern Discovery',
        description: 'Unsupervised clustering reveals emerging fraud typologies not captured by rule-based systems. Feeds back into triage feature engineering.',
        technology: 'K-Means · DBSCAN · PCA',
        badge: 'Production',
        badgeColor: 'badge-green',
    },
];

const IMPACT_ROWS = [
    { metric: 'AML investigation time', before: '45 min / case', after: '17 ms / case', saving: '99.9% faster' },
    { metric: 'Cost per investigation', before: '$37.50 (analyst hour)', after: '$0.005 (compute)', saving: '99.98% reduction' },
    { metric: 'False positive auto-close', before: '0% — all manual', after: '80% auto-closed', saving: '80% analyst time freed' },
    { metric: 'Annual AML team cost', before: '$2M · 20 FTE', after: '$350K · 4 FTE + platform', saving: '$1.65M / year' },
    { metric: 'Client portfolio insight', before: '$300 / hr advisor', after: '$0.002 / event', saving: 'Democratized to 3M users' },
    { metric: 'Event response time', before: 'Hours to days', after: 'Sub-second', saving: 'Real-time intelligence' },
    { metric: 'Support ticket reduction', before: 'Baseline', after: '−30% (proactive AI)', saving: '$500K / year' },
];

const TECH_GROUPS = [
    {
        title: 'AI / ML',
        color: 'green',
        items: [
            { name: 'XGBoost', purpose: 'AML triage classifier' },
            { name: 'LangGraph', purpose: 'Multi-agent orchestration' },
            { name: 'GPT-4o-mini', purpose: 'Narrative generation' },
            { name: 'ChromaDB', purpose: 'Vector store for RAG' },
            { name: 'sentence-transformers', purpose: 'Semantic embeddings' },
            { name: 'scikit-learn', purpose: 'Clustering & pattern discovery' },
            { name: 'Langfuse', purpose: 'LLM observability' },
        ],
    },
    {
        title: 'Frontend',
        color: 'teal',
        items: [
            { name: 'Next.js 14', purpose: 'React framework' },
            { name: 'TypeScript', purpose: 'Type-safe UI' },
            { name: 'Recharts', purpose: 'Data visualisation' },
            { name: 'Vanilla CSS', purpose: 'Custom dark design system' },
        ],
    },
    {
        title: 'API / Backend',
        color: 'blue',
        items: [
            { name: 'FastAPI', purpose: 'High-performance REST API' },
            { name: 'Uvicorn', purpose: 'Production ASGI server' },
            { name: 'Pydantic v2', purpose: 'Data validation' },
            { name: 'Python 3.10', purpose: 'Runtime' },
        ],
    },
    {
        title: 'Infrastructure',
        color: 'amber',
        items: [
            { name: 'Redis 7', purpose: 'Cache + event queues' },
            { name: 'Docker + Compose', purpose: 'Three-service stack' },
            { name: 'GitHub Actions', purpose: 'CI/CD pipeline' },
            { name: 'AWS EC2', purpose: 'Production hosting' },
            { name: 'GHCR', purpose: 'Container registry' },
        ],
    },
];

// ─── Component ───────────────────────────────────────────────────────

export default function OverviewPage() {
    return (
        <div className="ov-page animate-fade-in">

            {/* ── Hero ─────────────────────────────────────────────── */}
            <section className="ov-hero">
                <div className="ov-hero-eyebrow">Wealthsimple AI Builders Program</div>
                <h1 className="ov-hero-title">
                    WS <span>Intelligence</span> Platform
                </h1>
                <p className="ov-hero-sub">
                    AI-native intelligence for both sides of the house — automating financial crime investigation
                    for compliance teams and delivering personalised financial guidance to every Wealthsimple client.
                </p>
                <div className="ov-hero-badges">
                    <span className="badge badge-green">● WS Clarity — Compliance</span>
                    <span className="badge badge-teal">● WS Pilot — Client AI</span>
                    <span className="badge badge-blue">Shared Production Infrastructure</span>
                    <span className="badge badge-gray">10 AI Agents · 2 LangGraph Pipelines</span>
                </div>
            </section>

            {/* ── Project Cards ─────────────────────────────────────── */}
            <section className="ov-projects-grid animate-fade-in-up" style={{ animationDelay: '0.05s' }}>

                {/* WS Clarity */}
                <div className="glass-card ov-project-card glow-green">
                    <div className="ov-project-header">
                        <div>
                            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6 }}>
                                <div className="ov-project-icon clarity">⬡</div>
                                <div>
                                    <h3 style={{ marginBottom: 2 }}>WS Clarity</h3>
                                    <div style={{ fontSize: '0.72rem', color: 'var(--accent-green)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.08em' }}>Compliance Intelligence</div>
                                </div>
                            </div>
                            <p className="ov-project-tagline">&ldquo;AI that investigates so your analysts can decide.&rdquo;</p>
                        </div>
                        <span className="badge badge-green">Live</span>
                    </div>

                    <div className="ov-project-stat-row">
                        <div className="ov-stat">
                            <div className="ov-stat-val green">80%</div>
                            <div className="ov-stat-lbl">False positives auto-closed</div>
                        </div>
                        <div className="ov-stat">
                            <div className="ov-stat-val teal">17ms</div>
                            <div className="ov-stat-lbl">Per investigation (was 45 min)</div>
                        </div>
                        <div className="ov-stat">
                            <div className="ov-stat-val amber">$1.65M</div>
                            <div className="ov-stat-lbl">Annual savings vs 20 FTE</div>
                        </div>
                    </div>

                    <div className="ov-agent-list">
                        <div className="ov-agent-list-title">AI Agents</div>
                        {CLARITY_AGENTS.map(a => (
                            <div key={a.name} className="ov-agent-item">
                                <div className={`ov-agent-dot ${a.color}`} />
                                <div>
                                    <div className="ov-agent-name">{a.name}</div>
                                    <div className="ov-agent-desc">{a.desc}</div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* WS Pilot */}
                <div className="glass-card ov-project-card glow-blue">
                    <div className="ov-project-header">
                        <div>
                            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6 }}>
                                <div className="ov-project-icon pilot">⟁</div>
                                <div>
                                    <h3 style={{ marginBottom: 2 }}>WS Pilot</h3>
                                    <div style={{ fontSize: '0.72rem', color: 'var(--accent-teal)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.08em' }}>Client Financial Intelligence</div>
                                </div>
                            </div>
                            <p className="ov-project-tagline">&ldquo;AI that turns every financial moment into the right action.&rdquo;</p>
                        </div>
                        <span className="badge badge-teal">Built</span>
                    </div>

                    <div className="ov-project-stat-row">
                        <div className="ov-stat">
                            <div className="ov-stat-val teal">3M+</div>
                            <div className="ov-stat-lbl">Users served (was ~50)</div>
                        </div>
                        <div className="ov-stat">
                            <div className="ov-stat-val blue">$0.002</div>
                            <div className="ov-stat-lbl">Per event (was $300/hr)</div>
                        </div>
                        <div className="ov-stat">
                            <div className="ov-stat-val green">&lt;1s</div>
                            <div className="ov-stat-lbl">Response time (was hours)</div>
                        </div>
                    </div>

                    <div className="ov-agent-list">
                        <div className="ov-agent-list-title">AI Agents</div>
                        {PILOT_AGENTS.map(a => (
                            <div key={a.name} className="ov-agent-item">
                                <div className={`ov-agent-dot ${a.color}`} />
                                <div>
                                    <div className="ov-agent-name">{a.name}</div>
                                    <div className="ov-agent-desc">{a.desc}</div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </section>

            {/* ── Pipeline Flow Diagrams ─────────────────────────────── */}
            <div className="glass-card" style={{ padding: '24px 28px' }}>
                <div className="section-header" style={{ marginBottom: 24 }}>
                    <span className="section-title">AI Pipeline Architecture</span>
                    <span className="badge badge-gray">Human-in-the-loop at every critical decision</span>
                </div>

                <div className="ov-pipeline-section">
                    <div className="ov-pipeline-title">
                        <span style={{ color: 'var(--accent-green)' }}>●</span>&nbsp; WS Clarity — Compliance Pipeline
                    </div>
                    <div className="ov-flow">
                        {CLARITY_FLOW.map((node, i) => (
                            <div key={node.label} style={{ display: 'flex', alignItems: 'center' }}>
                                {node.human ? (
                                    <div className="ov-flow-human">
                                        <span style={{ fontSize: '0.9rem' }}>👤</span>
                                        <div>
                                            <div className="ov-flow-human-label">{node.label}</div>
                                            <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>{node.sub}</div>
                                        </div>
                                    </div>
                                ) : (
                                    <div className={`ov-flow-node ${node.color}`}>
                                        <div className="ov-flow-node-label">{node.label}</div>
                                        <div className="ov-flow-node-sub">{node.sub}</div>
                                    </div>
                                )}
                                {i < CLARITY_FLOW.length - 1 && (
                                    <div className="ov-flow-arrow">→</div>
                                )}
                            </div>
                        ))}
                        <div className="ov-flow-arrow">→</div>
                        <div className="ov-flow-node accent-red" style={{ borderColor: 'rgba(255,82,82,0.35)' }}>
                            <div className="ov-flow-node-label">FINTRAC Filing</div>
                            <div className="ov-flow-node-sub">Regulatory output</div>
                        </div>
                        <div style={{ marginLeft: 14, padding: '6px 12px', borderRadius: 'var(--radius-md)', background: 'var(--accent-green-dim)', border: '1px solid rgba(0,209,102,0.2)', fontSize: '0.72rem', color: 'var(--accent-green)', fontWeight: 600 }}>
                            80% auto-closed at triage ↑
                        </div>
                    </div>

                    <hr className="section-divider" style={{ margin: '20px 0' }} />

                    <div className="ov-pipeline-title">
                        <span style={{ color: 'var(--accent-teal)' }}>●</span>&nbsp; WS Pilot — Client Intelligence Pipeline
                    </div>
                    <div className="ov-flow">
                        {PILOT_FLOW.map((node, i) => (
                            <div key={node.label} style={{ display: 'flex', alignItems: 'center' }}>
                                {node.human ? (
                                    <div className="ov-flow-human">
                                        <span style={{ fontSize: '0.9rem' }}>👤</span>
                                        <div>
                                            <div className="ov-flow-human-label">{node.label}</div>
                                            <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>{node.sub}</div>
                                        </div>
                                    </div>
                                ) : (
                                    <div className={`ov-flow-node ${node.color}`}>
                                        <div className="ov-flow-node-label">{node.label}</div>
                                        <div className="ov-flow-node-sub">{node.sub}</div>
                                    </div>
                                )}
                                {i < PILOT_FLOW.length - 1 && (
                                    <div className="ov-flow-arrow">→</div>
                                )}
                            </div>
                        ))}
                        <div className="ov-flow-arrow">→</div>
                        <div className="ov-flow-node accent-green">
                            <div className="ov-flow-node-label">Client Action</div>
                            <div className="ov-flow-node-sub">In-app · personalised</div>
                        </div>
                    </div>
                </div>
            </div>

            {/* ── System Design Capabilities ────────────────────────── */}
            <div className="glass-card ov-capabilities animate-fade-in-up" style={{ animationDelay: '0.1s' }}>
                <div className="ov-cap-header">
                    <div>
                        <h3 style={{ marginBottom: 4 }}>System Design Capabilities</h3>
                        <p style={{ fontSize: '0.78rem' }}>Production-grade pillars shared across both AI systems</p>
                    </div>
                    <div style={{ display: 'flex', gap: 8 }}>
                        <span className="badge badge-green">Production</span>
                        <span className="badge badge-teal">Built</span>
                    </div>
                </div>
                <div className="table-wrap">
                    <table>
                        <thead>
                            <tr>
                                <th style={{ width: '15%' }}>Capability</th>
                                <th style={{ width: '50%' }}>Description</th>
                                <th style={{ width: '20%' }}>Technology</th>
                                <th style={{ width: '10%', textAlign: 'center' }}>Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            {CAPABILITIES.map(cap => (
                                <tr key={cap.area}>
                                    <td style={{ fontWeight: 600, color: 'var(--text-primary)', whiteSpace: 'nowrap' }}>{cap.area}</td>
                                    <td style={{ fontSize: '0.8rem', lineHeight: 1.55 }}>{cap.description}</td>
                                    <td style={{ fontFamily: 'monospace', fontSize: '0.76rem', color: 'var(--accent-teal)' }}>{cap.technology}</td>
                                    <td style={{ textAlign: 'center' }}>
                                        <span className={`badge ${cap.badgeColor}`}>{cap.badge}</span>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* ── Cost & Impact ─────────────────────────────────────── */}
            <div className="animate-fade-in-up" style={{ animationDelay: '0.15s' }}>
                <div style={{ marginBottom: 16 }}>
                    <h3 style={{ marginBottom: 4 }}>Cost Savings &amp; Business Impact</h3>
                    <p style={{ fontSize: '0.78rem' }}>Research-backed projections from a single Wealthsimple-scale deployment</p>
                </div>

                <div className="ov-impact-kpis">
                    {[
                        { val: '$1.65M', lbl: 'Annual AML savings', sub: 'vs 20 FTE team', color: 'var(--accent-green)' },
                        { val: '99.98%', lbl: 'Cost reduction per case', sub: '$37.50 → $0.005', color: 'var(--accent-teal)' },
                        { val: '80%', lbl: 'Analyst time freed', sub: 'Auto-closed false positives', color: 'var(--accent-amber)' },
                        { val: '$500K', lbl: 'Support ticket savings', sub: '−30% via proactive AI', color: 'var(--accent-blue)' },
                    ].map(k => (
                        <div key={k.lbl} className="ov-impact-kpi glass-card">
                            <div className="ov-impact-kpi-val" style={{ color: k.color }}>{k.val}</div>
                            <div style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-primary)', margin: '4px 0 2px' }}>{k.lbl}</div>
                            <div className="ov-impact-kpi-lbl">{k.sub}</div>
                        </div>
                    ))}
                </div>

                <div className="glass-card" style={{ overflow: 'hidden' }}>
                    <table>
                        <thead>
                            <tr>
                                <th>Metric</th>
                                <th>Before (Manual)</th>
                                <th>After (WS Intelligence)</th>
                                <th>Savings / Improvement</th>
                            </tr>
                        </thead>
                        <tbody>
                            {IMPACT_ROWS.map(row => (
                                <tr key={row.metric}>
                                    <td style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{row.metric}</td>
                                    <td style={{ color: 'var(--accent-red)', fontSize: '0.82rem' }}>{row.before}</td>
                                    <td style={{ color: 'var(--accent-green)', fontSize: '0.82rem', fontWeight: 600 }}>{row.after}</td>
                                    <td>
                                        <span className="badge badge-green" style={{ fontSize: '0.65rem' }}>{row.saving}</span>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* ── Tech Stack ────────────────────────────────────────── */}
            <div className="animate-fade-in-up" style={{ animationDelay: '0.2s' }}>
                <div style={{ marginBottom: 16 }}>
                    <h3 style={{ marginBottom: 4 }}>Technology Stack</h3>
                    <p style={{ fontSize: '0.78rem' }}>Purpose-selected for production financial systems — no demos, no shortcuts</p>
                </div>
                <div className="ov-tech-grid">
                    {TECH_GROUPS.map(group => (
                        <div key={group.title} className="glass-card ov-tech-group">
                            <div className="ov-tech-group-title" style={{
                                color: group.color === 'green' ? 'var(--accent-green)'
                                    : group.color === 'teal' ? 'var(--accent-teal)'
                                    : group.color === 'blue' ? 'var(--accent-blue)'
                                    : 'var(--accent-amber)',
                            }}>
                                {group.title}
                            </div>
                            {group.items.map(item => (
                                <div key={item.name} className="ov-tech-item">
                                    <div className="ov-tech-name">{item.name}</div>
                                    <div className="ov-tech-purpose">{item.purpose}</div>
                                </div>
                            ))}
                        </div>
                    ))}
                </div>
            </div>

            {/* ── Footer note ───────────────────────────────────────── */}
            <div style={{ textAlign: 'center', padding: '8px 0 16px', borderTop: '1px solid var(--border-subtle)' }}>
                <p style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                    Built for the Wealthsimple AI Builders Program · All AI decisions are advisory — humans approve every critical action
                </p>
            </div>

        </div>
    );
}
