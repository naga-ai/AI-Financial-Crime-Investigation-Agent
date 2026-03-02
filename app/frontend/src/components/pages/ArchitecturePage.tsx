'use client';

// ─── Architecture diagram: agents, ML models, flow ────────────────────

const ARROW = '→';

const CLARITY_NODES = [
  { id: 'alerts', label: 'AML Alerts', sub: 'Ingestion', type: 'input', color: 'blue' },
  { id: 'triage', label: 'Triage Agent', sub: 'XGBoost · <2ms', type: 'ml', color: 'green' },
  { id: 'invest', label: 'Investigation Agent', sub: 'LangGraph · 9 tools', type: 'agent', color: 'teal' },
  { id: 'report', label: 'Report Generator', sub: 'GPT-4o-mini', type: 'agent', color: 'amber' },
  { id: 'human', label: 'Compliance Officer', sub: 'Approve / Escalate', type: 'human', color: 'amber' },
  { id: 'fintrac', label: 'FINTRAC Filing', sub: 'Regulatory', type: 'output', color: 'red' },
];

const PULSE_NODES = [
  { id: 'event', label: 'Financial Event', sub: 'Paycheck / Earnings / Drop', type: 'input', color: 'blue' },
  { id: 'mask', label: 'PII Masking', sub: 'HMAC tokenization', type: 'infra', color: 'purple' },
  { id: 'detect', label: 'Event Detector', sub: '6 types · priority', type: 'ml', color: 'teal' },
  { id: 'portfolio', label: 'Portfolio Analyzer', sub: 'Tax-aware impact', type: 'agent', color: 'green' },
  { id: 'rag', label: 'RAG Retrieval', sub: 'TFSA / RRSP rules', type: 'infra', color: 'purple' },
  { id: 'rec', label: 'Recommendation Agent', sub: 'GPT-4o-mini', type: 'agent', color: 'amber' },
  { id: 'human2', label: 'Human Approval', sub: 'Approve / Dismiss', type: 'human', color: 'amber' },
  { id: 'client', label: 'Client Action', sub: 'Personalised', type: 'output', color: 'green' },
];

const SHARED = [
  { label: 'Redis', sub: 'Queue + Cache' },
  { label: 'ChromaDB', sub: 'RAG store' },
  { label: 'Langfuse', sub: 'Observability' },
  { label: 'Pattern Discovery', sub: 'K-Means / DBSCAN' },
];

function Node({
  node,
  isLast,
}: {
  node: (typeof CLARITY_NODES)[0];
  isLast: boolean;
}) {
  return (
    <div key={node.id} style={{ display: 'flex', alignItems: 'center', gap: 0 }}>
      <div
        className={`arch-node arch-${node.type} arch-color-${node.color}`}
        title={`${node.type === 'ml' ? 'ML Model' : node.type === 'agent' ? 'AI Agent' : node.type}`}
      >
        <div className="arch-node-label">{node.label}</div>
        <div className="arch-node-sub">{node.sub}</div>
      </div>
      {!isLast && <span className="arch-arrow">{ARROW}</span>}
    </div>
  );
}

export default function ArchitecturePage() {
  return (
    <div className="arch-page animate-fade-in">
      <div className="glass-card arch-card">
        <div className="arch-header">
          <h2 className="arch-title">WS Intelligence Platform — Architecture</h2>
          <p className="arch-subtitle">Agents, ML models, and data flow</p>
        </div>

        {/* Legend */}
        <div className="arch-legend">
          <span className="arch-legend-item ml">ML Model</span>
          <span className="arch-legend-item agent">Agent</span>
          <span className="arch-legend-item infra">Infrastructure</span>
          <span className="arch-legend-item human">Human Gate</span>
        </div>

        {/* WS Clarity pipeline */}
        <section className="arch-pipeline">
          <div className="arch-pipeline-label clarity">WS Clarity — Compliance</div>
          <div className="arch-flow">
            {CLARITY_NODES.map((n, i) => (
              <Node key={n.id} node={n} isLast={i === CLARITY_NODES.length - 1} />
            ))}
          </div>
          <div className="arch-branch-note">80% auto-closed at triage · 20% to investigation</div>
        </section>

        {/* WS Pulse pipeline */}
        <section className="arch-pipeline">
          <div className="arch-pipeline-label pulse">WS Pulse — Client Intelligence</div>
          <div className="arch-flow">
            {PULSE_NODES.map((n, i) => (
              <Node key={n.id} node={n} isLast={i === PULSE_NODES.length - 1} />
            ))}
          </div>
        </section>

        {/* Shared infrastructure */}
        <section className="arch-shared">
          <div className="arch-shared-label">Shared Infrastructure</div>
          <div className="arch-shared-grid">
            {SHARED.map((s) => (
              <div key={s.label} className="arch-shared-item">
                <div className="arch-shared-name">{s.label}</div>
                <div className="arch-shared-sub">{s.sub}</div>
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
