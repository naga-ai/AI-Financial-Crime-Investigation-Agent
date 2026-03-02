'use client';

import { useEffect, useState, useCallback } from 'react';
import { getObsStats, getObsTraces, type ObsStats, type Trace } from '@/lib/api';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';

const PALETTE = ['#00D166', '#00BCD4', '#FFC107', '#FF5252', '#448AFF'];

export default function ObsPage() {
    const [stats, setStats] = useState<ObsStats | null>(null);
    const [traces, setTraces] = useState<Trace[]>([]);
    const [loading, setLoading] = useState(true);
    const [selectedTrace, setSelectedTrace] = useState<Trace | null>(null);

    const load = useCallback(async () => {
        try {
            const [s, t] = await Promise.all([getObsStats(), getObsTraces(60)]);
            setStats(s);
            setTraces(t.traces);
        } finally { setLoading(false); }
    }, []);

    useEffect(() => { load(); }, [load]);

    if (loading) return <div className="loading-center"><div className="spinner spinner-lg" /></div>;

    if (!stats || stats.total_traces === 0) {
        return (
            <div className="empty-state glass-card" style={{ padding: 40 }}>
                <div className="empty-icon">◎</div>
                <h3>No Traces Yet</h3>
                <p>Run the investigation pipeline first to generate traces.</p>
            </div>
        );
    }

    // Span breakdown
    const spanData: Record<string, { total: number; count: number }> = {};
    traces.forEach(t => t.spans?.forEach(sp => {
        const k = sp.name.replace('tool:', '');
        if (!spanData[k]) spanData[k] = { total: 0, count: 0 };
        spanData[k].total += sp.duration_ms;
        spanData[k].count += 1;
    }));
    const spanChart = Object.entries(spanData)
        .map(([k, v]) => ({ Tool: k, 'Avg (ms)': parseFloat((v.total / v.count).toFixed(1)), Calls: v.count }))
        .sort((a, b) => b['Avg (ms)'] - a['Avg (ms)'])
        .slice(0, 10);

    const costChart = traces.slice(0, 30).map(t => ({
        Trace: t.trace_id.slice(0, 8),
        Cost: parseFloat((t.total_cost_usd * 1000).toFixed(4)),
    }));

    return (
        <div>
            {/* KPIs */}
            <div className="kpi-grid animate-fade-in">
                {[
                    { label: 'Traces', value: stats.total_traces.toLocaleString(), color: 'teal' },
                    { label: 'Total Spans', value: stats.total_spans.toLocaleString(), color: 'blue' },
                    { label: 'Total Cost (USD)', value: `$${stats.total_cost_usd.toFixed(4)}`, color: 'green' },
                    { label: 'Avg Cost/Case', value: `$${stats.avg_cost_usd.toFixed(6)}`, color: 'amber' },
                    { label: 'Avg Latency', value: `${stats.avg_duration_ms.toFixed(0)}ms`, color: 'red' },
                    { label: 'Max Latency', value: `${stats.max_duration_ms.toFixed(0)}ms`, color: 'purple' },
                ].map(({ label, value, color }, i) => (
                    <div key={label} className={`glass-card kpi-card ${color} animate-fade-in-up`} style={{ animationDelay: `${i * 0.05}s` }}>
                        <div className="kpi-label">{label}</div>
                        <div className="kpi-value">{value}</div>
                    </div>
                ))}
            </div>

            <hr className="section-divider" />

            <div className="grid-2 animate-fade-in-up" style={{ animationDelay: '0.2s' }}>
                {/* Cost chart */}
                <div className="glass-card" style={{ padding: '20px 24px' }}>
                    <div className="section-header"><span className="section-title">Cost Per Investigation (milli-$)</span></div>
                    <ResponsiveContainer width="100%" height={240}>
                        <BarChart data={costChart} margin={{ left: 0, right: 0, top: 0, bottom: 0 }}>
                            <XAxis dataKey="Trace" tick={{ fill: '#4A5568', fontSize: 9 }} axisLine={false} tickLine={false} />
                            <YAxis tick={{ fill: '#4A5568', fontSize: 10 }} axisLine={false} tickLine={false} />
                            <Tooltip contentStyle={{ background: '#0E1520', border: '1px solid rgba(255,255,255,0.1)', fontSize: 11, borderRadius: 8 }} />
                            <Bar dataKey="Cost" radius={[3, 3, 0, 0]}>
                                {costChart.map((_, i) => <Cell key={i} fill={PALETTE[i % PALETTE.length]} />)}
                            </Bar>
                        </BarChart>
                    </ResponsiveContainer>
                </div>

                {/* Span latency chart */}
                <div className="glass-card" style={{ padding: '20px 24px' }}>
                    <div className="section-header"><span className="section-title">Avg Latency by Tool</span></div>
                    <ResponsiveContainer width="100%" height={240}>
                        <BarChart layout="vertical" data={spanChart} margin={{ left: 10, right: 10, top: 0, bottom: 0 }}>
                            <XAxis type="number" tick={{ fill: '#4A5568', fontSize: 10 }} axisLine={false} tickLine={false} />
                            <YAxis type="category" dataKey="Tool" width={120} tick={{ fill: '#8899AA', fontSize: 10 }} axisLine={false} tickLine={false} />
                            <Tooltip contentStyle={{ background: '#0E1520', border: '1px solid rgba(255,255,255,0.1)', fontSize: 11, borderRadius: 8 }} />
                            <Bar dataKey="Avg (ms)" radius={[0, 4, 4, 0]}>
                                {spanChart.map((_, i) => <Cell key={i} fill={PALETTE[i % PALETTE.length]} />)}
                            </Bar>
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            </div>

            <hr className="section-divider" />

            {/* Trace explorer */}
            <div className="section-header"><span className="section-title">Trace Explorer</span></div>
            <div style={{ display: 'grid', gridTemplateColumns: selectedTrace ? '1fr 1.5fr' : '1fr', gap: 20 }}>
                <div style={{ maxHeight: '50vh', overflowY: 'auto' }}>
                    <table>
                        <thead><tr><th>Trace ID</th><th>Alert</th><th>Spans</th><th>Duration</th><th>Cost</th><th>Action</th></tr></thead>
                        <tbody>
                            {traces.slice(0, 50).map(t => (
                                <tr key={t.trace_id} onClick={() => setSelectedTrace(t === selectedTrace ? null : t)} style={{ cursor: 'pointer' }}>
                                    <td style={{ fontFamily: 'monospace', fontSize: '0.72rem', color: 'var(--text-muted)' }}>{t.trace_id.slice(0, 10)}</td>
                                    <td style={{ fontFamily: 'monospace', fontSize: '0.72rem' }}>{t.alert_id?.slice(0, 12)}</td>
                                    <td><span className="badge badge-gray">{t.span_count}</span></td>
                                    <td>{t.total_duration_ms?.toFixed(0)}ms</td>
                                    <td style={{ color: 'var(--accent-green)', fontWeight: 600 }}>${(t.total_cost_usd * 1000).toFixed(4)}m</td>
                                    <td><span className="badge badge-blue">{String((t.metadata?.recommended_action ?? '—')).replace(/_/g, ' ')}</span></td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>

                {selectedTrace && (
                    <div className="glass-card animate-slide-in" style={{ padding: 20, maxHeight: '50vh', overflowY: 'auto' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 14 }}>
                            <h4 style={{ fontFamily: 'monospace', fontSize: '0.85rem' }}>{selectedTrace.trace_id?.slice(0, 16)}</h4>
                            <button className="btn btn-secondary btn-sm" onClick={() => setSelectedTrace(null)}>✕</button>
                        </div>
                        <div style={{ marginBottom: 14 }}>
                            {[
                                ['Alert', selectedTrace.alert_id],
                                ['Spans', selectedTrace.span_count],
                                ['Duration', `${selectedTrace.total_duration_ms?.toFixed(1)}ms`],
                                ['Cost', `$${selectedTrace.total_cost_usd?.toFixed(6)}`],
                                ['Risk Score', String(selectedTrace.metadata?.risk_score ?? '—')],
                                ['Action', String(selectedTrace.metadata?.recommended_action ?? '—').replace(/_/g, ' ')],
                            ].map(([k, v]) => (
                                <div key={k as string} style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6, fontSize: '0.82rem' }}>
                                    <span style={{ color: 'var(--text-muted)' }}>{k}</span>
                                    <span style={{ color: 'var(--text-primary)', fontWeight: 500 }}>{v}</span>
                                </div>
                            ))}
                        </div>
                        <div className="section-title" style={{ fontSize: '0.76rem', marginBottom: 8 }}>Spans</div>
                        <table>
                            <thead><tr><th>Name</th><th>ms</th><th>Cost</th><th>Status</th></tr></thead>
                            <tbody>
                                {selectedTrace.spans?.map((sp, i) => (
                                    <tr key={i}>
                                        <td style={{ fontFamily: 'monospace', fontSize: '0.72rem', color: 'var(--accent-teal)' }}>{sp.name}</td>
                                        <td>{sp.duration_ms?.toFixed(0)}</td>
                                        <td style={{ color: 'var(--accent-green)' }}>${sp.cost_usd?.toFixed(7)}</td>
                                        <td><span className={`badge ${sp.status === 'ok' ? 'badge-green' : 'badge-red'}`}>{sp.status}</span></td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>
        </div>
    );
}
