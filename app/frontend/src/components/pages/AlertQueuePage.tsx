'use client';

import { useEffect, useState, useCallback } from 'react';
import { getResults, type AlertResult } from '@/lib/api';

const riskColor = (level: string) => {
    switch ((level || '').toLowerCase()) {
        case 'critical': return 'critical';
        case 'high': return 'high';
        case 'medium': return 'medium';
        default: return 'low';
    }
};

const riskBadge = (level: string) => {
    switch ((level || '').toLowerCase()) {
        case 'critical': return 'badge-red';
        case 'high': return 'badge-red';
        case 'medium': return 'badge-amber';
        default: return 'badge-green';
    }
};

const actionBadge = (action: string) => {
    switch (action) {
        case 'file_str': return 'badge-red';
        case 'escalate': return 'badge-amber';
        default: return 'badge-gray';
    }
};

export default function AlertQueuePage() {
    const [results, setResults] = useState<AlertResult[]>([]);
    const [loading, setLoading] = useState(true);
    const [expanded, setExpanded] = useState<string | null>(null);
    const [tab, setTab] = useState<'steps' | 'txns'>('steps');
    const [filter, setFilter] = useState('all');

    const load = useCallback(async () => {
        setLoading(true);
        try {
            const data = await getResults();
            const inv = data.results.filter(r => r.investigation);
            inv.sort((a, b) => (b.investigation?.risk_score ?? 0) - (a.investigation?.risk_score ?? 0));
            setResults(inv);
        } finally { setLoading(false); }
    }, []);

    useEffect(() => { load(); }, [load]);

    const filtered = filter === 'all' ? results
        : filter === 'str' ? results.filter(r => r.status === 'pending_str_review')
            : filter === 'esc' ? results.filter(r => r.status === 'escalated')
                : results;

    if (loading) return <div className="loading-center"><div className="spinner spinner-lg" /></div>;

    if (!results.length) {
        return (
            <div className="empty-state glass-card" style={{ padding: 40 }}>
                <div className="empty-icon">◈</div>
                <h3>No Investigations Yet</h3>
                <p>Run the pipeline from the Executive Summary page first.</p>
            </div>
        );
    }

    const currentExpanded = results.find(r => r.alert_id === expanded);

    return (
        <div>
            {/* Filter bar */}
            <div style={{ display: 'flex', gap: 10, marginBottom: 20, alignItems: 'center', flexWrap: 'wrap' }}>
                {[
                    { id: 'all', label: `All (${results.length})` },
                    { id: 'str', label: `Pending STR (${results.filter(r => r.status === 'pending_str_review').length})` },
                    { id: 'esc', label: `Escalated (${results.filter(r => r.status === 'escalated').length})` },
                ].map(f => (
                    <button
                        key={f.id}
                        className={`btn btn-sm ${filter === f.id ? 'btn-primary' : 'btn-secondary'}`}
                        onClick={() => setFilter(f.id)}
                    >
                        {f.label}
                    </button>
                ))}
                <span style={{ marginLeft: 'auto', fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                    {filtered.length} cases shown
                </span>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: expanded ? '1fr 1.4fr' : '1fr', gap: 20 }}>
                {/* Alert list */}
                <div style={{ maxHeight: '75vh', overflowY: 'auto', paddingRight: 4 }}>
                    {filtered.map((r, idx) => {
                        const inv = r.investigation!;
                        const level = (inv.risk_level || 'low').toLowerCase();
                        const isExp = expanded === r.alert_id;
                        return (
                            <div
                                key={r.alert_id}
                                className={`alert-card ${riskColor(level)} animate-fade-in-up`}
                                style={{ animationDelay: `${idx * 0.04}s`, outline: isExp ? '1px solid var(--accent-green)' : 'none' }}
                                onClick={() => { setExpanded(isExp ? null : r.alert_id); setTab('steps'); }}
                            >
                                <div className="alert-card-top">
                                    <div>
                                        <div className="alert-card-id">{r.alert_id}</div>
                                        <div className="alert-card-meta" style={{ marginTop: 4 }}>
                                            <span className={`badge ${riskBadge(level)}`}>{level.toUpperCase()}</span>
                                            <span className="badge badge-gray">{r.alert_type.replace(/_/g, ' ')}</span>
                                        </div>
                                    </div>
                                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 6 }}>
                                        <div style={{ fontFamily: 'var(--font-display)', fontSize: '1.4rem', fontWeight: 800, color: level === 'critical' || level === 'high' ? 'var(--accent-red)' : level === 'medium' ? 'var(--accent-amber)' : 'var(--accent-green)' }}>
                                            {inv.risk_score.toFixed(0)}
                                        </div>
                                        <span className={`badge ${actionBadge(inv.recommended_action)}`}>{inv.recommended_action.replace(/_/g, ' ')}</span>
                                    </div>
                                </div>
                                <div className="alert-card-body">
                                    <strong>{(inv.client_profile as Record<string, string>).full_name ?? r.client_id}</strong>
                                    {' · '}
                                    {(inv.client_profile as Record<string, string>).occupation ?? ''}
                                    {' · '}
                                    Confidence: {(inv.confidence * 100).toFixed(0)}%
                                    <div style={{ marginTop: 6 }}>
                                        <div className="progress-bar">
                                            <div className={`progress-fill${level === 'high' || level === 'critical' ? ' red' : level === 'medium' ? ' amber' : ''}`}
                                                style={{ width: `${inv.risk_score}%` }} />
                                        </div>
                                    </div>
                                </div>
                            </div>
                        );
                    })}
                </div>

                {/* Detail panel */}
                {currentExpanded && (
                    <div className="glass-card animate-slide-in" style={{ padding: 24, maxHeight: '75vh', overflowY: 'auto' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 18 }}>
                            <div>
                                <div className="alert-card-id">{currentExpanded.alert_id}</div>
                                <h3 style={{ marginTop: 4 }}>{(currentExpanded.investigation!.client_profile as Record<string, string>).full_name}</h3>
                            </div>
                            <button className="btn btn-secondary btn-sm" onClick={() => setExpanded(null)}>✕ Close</button>
                        </div>

                        {/* Risk factors */}
                        <div style={{ marginBottom: 18 }}>
                            <div className="section-title" style={{ marginBottom: 10 }}>Risk Factors</div>
                            {currentExpanded.investigation!.risk_factors.map((rf, i) => (
                                <div key={i} style={{ display: 'flex', gap: 8, marginBottom: 6, fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
                                    <span style={{ color: 'var(--accent-amber)', flexShrink: 0 }}>⚠</span> {rf}
                                </div>
                            ))}
                        </div>

                        {/* Typologies */}
                        {currentExpanded.investigation!.typology_matches?.length > 0 && (
                            <div style={{ marginBottom: 18 }}>
                                <div className="section-title" style={{ marginBottom: 10 }}>FINTRAC Typologies</div>
                                {currentExpanded.investigation!.typology_matches.map((t, i) => (
                                    <div key={i} className="notice notice-warning" style={{ marginBottom: 6, padding: '8px 12px' }}>
                                        <div>
                                            <strong>{t.typology_name}</strong>
                                            <span style={{ marginLeft: 8, fontSize: '0.72rem' }}>{(t.match_score * 100).toFixed(0)}% match</span>
                                            <br />
                                            <span style={{ fontSize: '0.75rem', opacity: 0.8 }}>{t.fintrac_reference}</span>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}

                        {/* Tabs: Steps / Transactions */}
                        <div className="tab-bar">
                            <button className={`tab-item${tab === 'steps' ? ' active' : ''}`} onClick={() => setTab('steps')}>Investigation Steps</button>
                            <button className={`tab-item${tab === 'txns' ? ' active' : ''}`} onClick={() => setTab('txns')}>Transactions</button>
                        </div>

                        {tab === 'steps' && (
                            <div className="table-wrap">
                                <table>
                                    <thead><tr><th>Step</th><th>Tool</th><th>Ms</th></tr></thead>
                                    <tbody>
                                        {currentExpanded.investigation!.steps_taken.map((s, i) => (
                                            <tr key={i}>
                                                <td>{s.step_name}</td>
                                                <td style={{ fontFamily: 'monospace', fontSize: '0.75rem', color: 'var(--accent-teal)' }}>{s.tool_called}</td>
                                                <td style={{ color: 'var(--text-muted)' }}>{s.duration_ms.toFixed(0)}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        )}

                        {tab === 'txns' && (
                            <div className="table-wrap">
                                <table>
                                    <thead><tr><th>Date</th><th>Type</th><th>Amount</th><th>Method</th></tr></thead>
                                    <tbody>
                                        {currentExpanded.investigation!.transaction_history.slice(-20).map((t, i) => (
                                            <tr key={i}>
                                                <td style={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>{t.timestamp?.slice(0, 10)}</td>
                                                <td><span className="badge badge-gray">{t.type}</span></td>
                                                <td style={{ fontWeight: 600, color: t.type === 'withdrawal' ? 'var(--accent-red)' : 'var(--accent-green)' }}>
                                                    ${t.amount_cad?.toLocaleString('en-CA', { minimumFractionDigits: 2 })}
                                                </td>
                                                <td style={{ color: 'var(--text-muted)', fontSize: '0.78rem' }}>{t.method}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        )}

                        <div style={{ marginTop: 16, fontSize: '0.76rem', color: 'var(--text-muted)', textAlign: 'right' }}>
                            Pipeline time: {currentExpanded.total_pipeline_time_ms.toFixed(0)}ms
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
