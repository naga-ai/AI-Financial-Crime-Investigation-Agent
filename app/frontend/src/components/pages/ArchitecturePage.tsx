'use client';

const ICONS: Record<string, string> = {
  input: '⚡', ml: '🧠', agent: '🤖', infra: '⚙', human: '👤', output: '✅', llm: '💬',
};

const CLARITY_NODES = [
  { id: 'alerts', label: 'AML Alerts', sub: '315 alerts · 10 typologies', type: 'input', color: 'blue' },
  { id: 'triage', label: 'Triage Agent', sub: 'XGBoost · 24 features · <2ms', type: 'ml', color: 'green', detail: '100% precision · stratified K-fold CV' },
  { id: 'invest', label: 'Investigation Agent', sub: 'LangGraph · 9 tool nodes', type: 'agent', color: 'teal', detail: 'Transaction analysis · Watchlists · Entity graph · Typology matching' },
  { id: 'rag', label: 'RAG Retrieval', sub: 'ChromaDB + sentence-transformers', type: 'infra', color: 'purple', detail: 'FINTRAC regulatory guidance' },
  { id: 'report', label: 'Report Generator', sub: 'GPT-4o-mini + template fallback', type: 'llm', color: 'amber', detail: 'FINTRAC STR narratives · 100% uptime' },
  { id: 'human', label: 'Compliance Officer', sub: 'Approve / Reject / Escalate', type: 'human', color: 'amber' },
  { id: 'fintrac', label: 'FINTRAC Filing', sub: 'Regulatory submission', type: 'output', color: 'red' },
];

const PULSE_NODES = [
  { id: 'event', label: 'Financial Event', sub: 'Paycheck · Earnings · Market drop · Rate change', type: 'input', color: 'blue' },
  { id: 'mask', label: 'PII Masking', sub: 'HMAC-SHA256 tokenization', type: 'infra', color: 'purple', detail: 'Field-level · full audit log' },
  { id: 'detect', label: 'Event Detector', sub: '6 event types · priority scoring', type: 'ml', color: 'teal', detail: 'Queue priority for Redis Streams' },
  { id: 'portfolio', label: 'Portfolio Analyzer', sub: 'Per-user holdings · tax-aware', type: 'agent', color: 'green', detail: 'TFSA · RRSP · concentration risk' },
  { id: 'rag2', label: 'RAG Retrieval', sub: 'ChromaDB + sentence-transformers', type: 'infra', color: 'purple', detail: 'Canadian tax & investment guidance' },
  { id: 'rec', label: 'Recommendation Agent', sub: 'GPT-4o-mini · plain language', type: 'llm', color: 'amber', detail: 'Personalised · actionable · tax-aware' },
  { id: 'human2', label: 'Human Approval', sub: 'Approve / Adjust / Dismiss', type: 'human', color: 'amber' },
  { id: 'client', label: 'Client Action', sub: 'In-app personalised guidance', type: 'output', color: 'green' },
];

const INVESTIGATION_TOOLS = [
  { name: 'gather_context', desc: 'Client profile & history' },
  { name: 'analyze_transactions', desc: 'Pattern detection' },
  { name: 'screen_watchlists', desc: 'Sanctions & PEP' },
  { name: 'match_typologies', desc: '10 FINTRAC types' },
  { name: 'deep_crypto_analysis', desc: 'Conditional' },
  { name: 'retrieve_regulatory', desc: 'RAG over guidance' },
  { name: 'assess_risk', desc: 'Score & classify' },
  { name: 'build_entity_graph', desc: 'Network analysis' },
  { name: 'generate_narrative', desc: 'STR draft' },
];

const SHARED = [
  { label: 'Redis 7', sub: 'Event queue + semantic cache', detail: 'Streams · DLQ · backpressure · multi-region TTL', icon: '⟐' },
  { label: 'ChromaDB', sub: 'Vector store for RAG', detail: 'sentence-transformers embeddings', icon: '◈' },
  { label: 'Langfuse', sub: 'LLM observability', detail: 'Per-span cost · latency · trace explorer', icon: '◎' },
  { label: 'PII Masking', sub: 'HMAC-SHA256 tokenization', detail: 'Before any LLM / cache / RAG call', icon: '🔒' },
  { label: 'Model Scorecards', sub: 'OSFI E-23 aligned', detail: 'Bias analysis · performance metrics', icon: '📋' },
  { label: 'Pattern Discovery', sub: 'K-Means / DBSCAN', detail: 'Emerging fraud typology detection', icon: '⌬' },
];

const STATS = [
  { val: '10', label: 'AI Agents', color: 'var(--accent-teal)' },
  { val: '2', label: 'LangGraph Pipelines', color: 'var(--accent-green)' },
  { val: '1', label: 'ML Classifier', color: 'var(--accent-amber)' },
  { val: '2', label: 'LLM Integrations', color: 'var(--accent-purple)' },
  { val: '9', label: 'Investigation Tools', color: 'var(--accent-blue)' },
  { val: '6', label: 'Infra Modules', color: 'var(--accent-red)' },
];

function FlowNode({ node, isLast }: { node: typeof CLARITY_NODES[0]; isLast: boolean }) {
  const icon = node.type === 'llm' ? ICONS.llm : ICONS[node.type] || '•';
  const detail = (node as { detail?: string }).detail;
  return (
    <div style={{ display: 'flex', alignItems: 'center' }}>
      <div className={`arch-node arch-${node.type} arch-color-${node.color}`}>
        <div style={{ fontSize: '1.1rem', marginBottom: 4 }}>{icon}</div>
        <div className="arch-node-label">{node.label}</div>
        <div className="arch-node-sub">{node.sub}</div>
        {detail && <div className="arch-node-detail">{detail}</div>}
      </div>
      {!isLast && <span className="arch-arrow">→</span>}
    </div>
  );
}

export default function ArchitecturePage() {
  return (
    <div className="arch-page animate-fade-in">

      {/* Hero stats */}
      <div className="arch-stats-row">
        {STATS.map(s => (
          <div key={s.label} className="glass-card arch-stat-card">
            <div className="arch-stat-val" style={{ color: s.color }}>{s.val}</div>
            <div className="arch-stat-lbl">{s.label}</div>
          </div>
        ))}
      </div>

      {/* WS Clarity */}
      <div className="glass-card arch-card">
        <div className="arch-section-header">
          <div>
            <div className="arch-section-icon" style={{ background: 'var(--accent-green-dim)', color: 'var(--accent-green)' }}>⬡</div>
          </div>
          <div>
            <h3 style={{ marginBottom: 2 }}>WS Clarity — Compliance Pipeline</h3>
            <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>AI investigates AML alerts end-to-end · human approves final filing</p>
          </div>
          <div style={{ marginLeft: 'auto', display: 'flex', gap: 8 }}>
            <span className="badge badge-green">LangGraph</span>
            <span className="badge badge-amber">GPT-4o-mini</span>
            <span className="badge badge-teal">XGBoost</span>
          </div>
        </div>

        <div className="arch-flow" style={{ marginBottom: 12 }}>
          {CLARITY_NODES.map((n, i) => (
            <FlowNode key={n.id} node={n} isLast={i === CLARITY_NODES.length - 1} />
          ))}
        </div>
        <div className="arch-branch-note">⚡ 80% auto-closed at triage · 20% proceed to full investigation</div>

        {/* Investigation tools detail */}
        <div className="arch-tools-section">
          <div className="arch-tools-title">Investigation Agent — 9 Tool Nodes</div>
          <div className="arch-tools-grid">
            {INVESTIGATION_TOOLS.map(t => (
              <div key={t.name} className="arch-tool-chip">
                <span className="arch-tool-name">{t.name}</span>
                <span className="arch-tool-desc">{t.desc}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* WS Pulse */}
      <div className="glass-card arch-card">
        <div className="arch-section-header">
          <div>
            <div className="arch-section-icon" style={{ background: 'var(--accent-teal-dim)', color: 'var(--accent-teal)' }}>⟁</div>
          </div>
          <div>
            <h3 style={{ marginBottom: 2 }}>WS Pulse — Client Intelligence Pipeline</h3>
            <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Personalised, tax-aware guidance for 3M+ users at $0.002 per event</p>
          </div>
          <div style={{ marginLeft: 'auto', display: 'flex', gap: 8 }}>
            <span className="badge badge-green">LangGraph</span>
            <span className="badge badge-amber">GPT-4o-mini</span>
            <span className="badge badge-purple">RAG</span>
          </div>
        </div>

        <div className="arch-flow">
          {PULSE_NODES.map((n, i) => (
            <FlowNode key={n.id} node={n} isLast={i === PULSE_NODES.length - 1} />
          ))}
        </div>
      </div>

      {/* Shared Infrastructure */}
      <div className="glass-card arch-card">
        <div className="arch-section-header">
          <div>
            <div className="arch-section-icon" style={{ background: 'var(--accent-blue-dim)', color: 'var(--accent-blue)' }}>⚙</div>
          </div>
          <div>
            <h3 style={{ marginBottom: 2 }}>Shared Production Infrastructure</h3>
            <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Production-grade modules shared across both AI systems</p>
          </div>
        </div>

        <div className="arch-infra-grid">
          {SHARED.map(s => (
            <div key={s.label} className="arch-infra-card">
              <div className="arch-infra-icon">{s.icon}</div>
              <div>
                <div className="arch-infra-name">{s.label}</div>
                <div className="arch-infra-sub">{s.sub}</div>
                <div className="arch-infra-detail">{s.detail}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Legend */}
      <div className="arch-legend-bar">
        <span className="arch-legend-item ml">🧠 ML Model</span>
        <span className="arch-legend-item llm">💬 LLM (GPT-4o-mini)</span>
        <span className="arch-legend-item agent">🤖 AI Agent</span>
        <span className="arch-legend-item infra">⚙ Infrastructure</span>
        <span className="arch-legend-item human">👤 Human-in-the-Loop</span>
      </div>

    </div>
  );
}
