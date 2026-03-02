'use client';

import { useEffect, useState, useCallback } from 'react';
import { processPulse, getPulseResults, type PulseResult } from '@/lib/api';

const PRIORITY_COLOR: Record<string, string> = {
    critical: 'badge-red',
    high: 'badge-red',
    medium: 'badge-amber',
    low: 'badge-green',
};

export default function PulsePage() {
    const [results, setResults] = useState<PulseResult[]>([]);
    const [loading, setLoading] = useState(true);
    const [running, setRunning] = useState(false);
    const [maxEvt, setMaxEvt] = useState(15);

    const load = useCallback(async () => {
        try {
            const data = await getPulseResults();
            setResults(data.results);
        } finally { setLoading(false); }
    }, []);

    useEffect(() => { load(); }, [load]);

    const handleRun = async () => {
        setRunning(true);
        try {
            await processPulse(maxEvt);
            await load();
        } finally { setRunning(false); }
    };

    if (loading) return <div className="loading-center"><div className="spinner spinner-lg" /></div>;

    const totalValue = results.reduce((s, r) => s + (r.recommendation?.estimated_value_cad ?? 0), 0);
    const cacheHits = results.filter(r => r.cache_hit).length;

    return (
        <div>
            {/* Header section */}
            <div className="glass-card glow-teal animate-fade-in-up" style={{ padding: '24px 28px', marginBottom: 24, borderColor: 'rgba(0,188,212,0.2)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 20, flexWrap: 'wrap' }}>
                    <div>
                        <h3 style={{ marginBottom: 6 }}>WS Pulse — Client Financial Intelligence</h3>
                        <p style={{ fontSize: '0.85rem', maxWidth: 520 }}>
                            Turns every financial moment (paycheck, earnings report, market shift) into a personalized,
                            tax-aware recommendation for each client — at sub-second speed.
                        </p>
                    </div>
                    <div style={{ display: 'flex', gap: 12, alignItems: 'flex-end' }}>
                        <div style={{ minWidth: 120 }}>
                            <label>Max Events</label>
                            <input type="number" value={maxEvt} min={1} max={50} onChange={e => setMaxEvt(Number(e.target.value))} />
                        </div>
                        <button className="btn btn-primary" onClick={handleRun} disabled={running}>
                            {running ? <><span className="spinner" style={{ width: 14, height: 14 }} /> Processing…</> : '⟁ Run Pulse'}
                        </button>
                    </div>
                </div>
            </div>

            {/* KPIs */}
            {results.length > 0 && (
                <div className="kpi-grid animate-fade-in">
                    {[
                        { label: 'Events Processed', value: results.length, color: 'teal' },
                        { label: 'Recommendations', value: results.filter(r => r.recommendation).length, color: 'green' },
                        { label: 'Total Est. Value', value: `$${(totalValue / 1000).toFixed(0)}K CAD`, color: 'blue' },
                        { label: 'Cache Hits', value: `${cacheHits}/${results.length}`, color: 'amber' },
                        { label: 'Avg Latency', value: `${(results.reduce((s, r) => s + r.processing_time_ms, 0) / results.length).toFixed(0)}ms`, color: 'purple' },
                        { label: 'Hit Rate', value: `${((cacheHits / results.length) * 100).toFixed(0)}%`, color: 'red' },
                    ].map(({ label, value, color }, i) => (
                        <div key={label} className={`glass-card kpi-card ${color} animate-fade-in-up`} style={{ animationDelay: `${i * 0.05}s` }}>
                            <div className="kpi-label">{label}</div>
                            <div className="kpi-value">{value}</div>
                        </div>
                    ))}
                </div>
            )}

            {results.length > 0 && <hr className="section-divider" />}

            {/* Recommendation cards */}
            {results.length > 0 ? (
                <>
                    <div className="section-header"><span className="section-title">Recommendations Generated</span></div>
                    <div className="grid-2 animate-fade-in-up" style={{ animationDelay: '0.15s' }}>
                        {results.filter(r => r.recommendation).map((r, idx) => {
                            const rec = r.recommendation!;
                            return (
                                <div key={idx} className="glass-card" style={{ padding: '18px 22px', borderLeft: `3px solid var(--accent-teal)` }}>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 10 }}>
                                        <div>
                                            <span className={`badge ${PRIORITY_COLOR[rec.priority] ?? 'badge-gray'}`} style={{ marginBottom: 6, display: 'inline-block' }}>
                                                {rec.priority.toUpperCase()}
                                            </span>
                                            <div style={{ fontWeight: 700, fontSize: '0.92rem', color: 'var(--text-primary)' }}>{rec.title}</div>
                                        </div>
                                        <div style={{ textAlign: 'right', flexShrink: 0 }}>
                                            <div style={{ fontFamily: 'var(--font-display)', fontWeight: 800, fontSize: '1rem', color: 'var(--accent-teal)' }}>
                                                ${rec.estimated_value_cad.toLocaleString('en-CA', { minimumFractionDigits: 0 })}
                                            </div>
                                            <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>est. value CAD</div>
                                        </div>
                                    </div>
                                    <p style={{ fontSize: '0.82rem', marginBottom: 10, lineHeight: 1.6 }}>{rec.summary}</p>
                                    <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
                                        <span className="badge badge-blue">{rec.action.replace(/_/g, ' ')}</span>
                                        <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Confidence: {(rec.confidence * 100).toFixed(0)}%</span>
                                        <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>{r.processing_time_ms.toFixed(0)}ms</span>
                                        {r.cache_hit && <span className="badge badge-teal">CACHE ✓</span>}
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </>
            ) : (
                <div className="empty-state glass-card" style={{ padding: 40 }}>
                    <div className="empty-icon">⟁</div>
                    <h3>No Pulse Events Yet</h3>
                    <p>Click &quot;Run Pulse&quot; to process financial events and generate personalized recommendations.</p>
                </div>
            )}
        </div>
    );
}
