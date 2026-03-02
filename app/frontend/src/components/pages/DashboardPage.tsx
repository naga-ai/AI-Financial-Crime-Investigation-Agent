'use client';

import { useEffect, useState, useCallback } from 'react';
import KpiCard from '@/components/KpiCard';
import {
    getOverview, processAlerts, getStats,
    type Overview, type Stats,
} from '@/lib/api';
import {
    PieChart, Pie, Cell, BarChart, Bar,
    XAxis, YAxis, Tooltip, ResponsiveContainer, Legend,
} from 'recharts';

const PALETTE = ['#00D166', '#00BCD4', '#FFC107', '#FF5252', '#448AFF', '#9C27B0'];
const fmt = (n: number) => n.toLocaleString();

interface TooltipProps {
    active?: boolean;
    payload?: Array<{ name: string; value: number; color: string }>;
    label?: string;
}

const CUSTOM_TOOLTIP = ({ active, payload, label }: TooltipProps) => {
    if (!active || !payload) return null;
    return (
        <div style={{ background: '#0E1520', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, padding: '8px 14px', fontSize: 12 }}>
            {label && <p style={{ color: '#8899AA', marginBottom: 4 }}>{label}</p>}
            {payload.map((e) => (
                <p key={e.name} style={{ color: e.color ?? '#00D166' }}>
                    {e.name}: <strong>{typeof e.value === 'number' ? e.value.toLocaleString() : e.value}</strong>
                </p>
            ))}
        </div>
    );
};

export default function DashboardPage() {
    const [overview, setOverview] = useState<Overview | null>(null);
    const [stats, setStats] = useState<Stats | null>(null);
    const [loading, setLoading] = useState(false);
    const [running, setRunning] = useState(false);
    const [limit, setLimit] = useState(315);
    const [error, setError] = useState<string | null>(null);

    const load = useCallback(async () => {
        setLoading(true);
        try {
            const ov = await getOverview();
            setOverview(ov);
            if (ov.processed) {
                const s = await getStats();
                setStats(s);
            }
        } catch (e) {
            setError(String(e));
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => { load(); }, [load]);

    const handleRun = async () => {
        setRunning(true);
        setError(null);
        try {
            await processAlerts(limit);
            await load();
        } catch (e) {
            setError(String(e));
        } finally {
            setRunning(false);
        }
    };

    if (loading && !overview) {
        return <div className="loading-center"><div className="spinner spinner-lg" /><p>Connecting to API…</p></div>;
    }

    if (error) {
        return (
            <div className="notice notice-error animate-fade-in">
                <span>⚠</span>
                <div>
                    <strong>Connection Error</strong><br />
                    <span style={{ fontSize: '0.78rem' }}>{error}</span><br />
                    <em style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                        Make sure the Python API is running: <code>python -m uvicorn src.api.server:app --port 8000</code>
                    </em>
                </div>
            </div>
        );
    }

    return (
        <div>
            {/* Dataset overview - always visible */}
            {overview && (
                <div className="kpi-grid animate-fade-in">
                    <KpiCard label="Clients" value={fmt(overview.n_clients)} color="teal" delay={0.0} />
                    <KpiCard label="Transactions" value={fmt(overview.n_transactions)} color="blue" delay={0.05} />
                    <KpiCard label="AML Alerts" value={fmt(overview.n_alerts)} color="amber" delay={0.1} />
                    <KpiCard label="True Positives" value={fmt(overview.true_positives)} sub="Ground truth" color="red" delay={0.15} />
                    <KpiCard label="False Positives" value={fmt(overview.false_positives)} sub="80% of total" color="purple" delay={0.2} />
                    <KpiCard label="Status" value={overview.processed ? 'Processed' : 'Ready'} color="green" delay={0.25} />
                </div>
            )}

            {/* Run control */}
            {!stats && (
                <div className="glass-card animate-fade-in-up" style={{ padding: '28px 32px', marginBottom: 24 }}>
                    <div style={{ maxWidth: 560 }}>
                        <h3 style={{ marginBottom: 6 }}>Run the Investigation Pipeline</h3>
                        <p style={{ marginBottom: 20, fontSize: '0.875rem', color: 'var(--text-muted)' }}>
                            Kick off the XGBoost triage → LangGraph investigation → STR report generation pipeline on all {overview?.n_alerts} AML alerts.
                        </p>
                        <div style={{ display: 'flex', gap: 14, alignItems: 'flex-end', flexWrap: 'wrap' }}>
                            <div style={{ flex: 1, minWidth: 200 }}>
                                <label>Alerts to Process</label>
                                <input
                                    type="number"
                                    value={limit}
                                    min={50}
                                    max={overview?.n_alerts ?? 315}
                                    step={10}
                                    onChange={e => setLimit(Number(e.target.value))}
                                />
                            </div>
                            <button className="btn btn-primary btn-lg" onClick={handleRun} disabled={running}>
                                {running ? <><span className="spinner" style={{ width: 16, height: 16 }} /> Processing…</> : '▶ Run Pipeline'}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {stats && (
                <>
                    {/* KPI Results Row */}
                    <div className="kpi-grid animate-fade-in">
                        <KpiCard label="Processed" value={fmt(stats.n)} color="teal" delay={0} />
                        <KpiCard label="Auto-Closed" value={`${(stats.auto_rate * 100).toFixed(0)}%`} sub={`${fmt(stats.auto_closed)} alerts`} color="green" delay={0.05} change={`${fmt(stats.auto_closed)} FP cleared`} changeDir="up" />
                        <KpiCard label="Investigated" value={fmt(stats.investigated)} sub={`${((stats.investigated / stats.n) * 100).toFixed(0)}% of total`} color="amber" delay={0.1} />
                        <KpiCard label="Pending STR" value={stats.pending_str} color="red" delay={0.15} />
                        <KpiCard label="Reports Done" value={`${stats.decisions_made}/${stats.reports}`} color="blue" delay={0.2} />
                        <KpiCard label="Avg Latency" value={`${stats.avg_latency_ms.toFixed(0)}ms`} color="purple" delay={0.25} />
                    </div>

                    <hr className="section-divider" />

                    {/* Charts */}
                    <div className="grid-3 animate-fade-in-up" style={{ animationDelay: '0.2s' }}>
                        {/* Disposition Donut */}
                        <div className="glass-card" style={{ padding: '20px 24px' }}>
                            <div className="section-header">
                                <span className="section-title">Disposition</span>
                            </div>
                            <ResponsiveContainer width="100%" height={220}>
                                <PieChart>
                                    <Pie
                                        data={Object.entries(stats.status_breakdown).map(([k, v]) => ({ name: k.replace(/_/g, ' '), value: v }))}
                                        cx="50%" cy="50%"
                                        innerRadius={55} outerRadius={80}
                                        paddingAngle={3}
                                        dataKey="value"
                                    >
                                        {Object.keys(stats.status_breakdown).map((_, i) => (
                                            <Cell key={i} fill={PALETTE[i % PALETTE.length]} />
                                        ))}
                                    </Pie>
                                    <Tooltip content={<CUSTOM_TOOLTIP />} />
                                    <Legend wrapperStyle={{ fontSize: 11, color: '#8899AA' }} />
                                </PieChart>
                            </ResponsiveContainer>
                        </div>

                        {/* Alert Types Bar */}
                        <div className="glass-card" style={{ padding: '20px 24px' }}>
                            <div className="section-header">
                                <span className="section-title">Alert Types</span>
                            </div>
                            <ResponsiveContainer width="100%" height={220}>
                                <BarChart
                                    layout="vertical"
                                    data={Object.entries(stats.type_breakdown)
                                        .sort(([, a], [, b]) => b - a)
                                        .map(([k, v]) => ({ name: k.replace(/_/g, ' '), count: v }))}
                                    margin={{ left: 10, right: 10, top: 0, bottom: 0 }}
                                >
                                    <XAxis type="number" tick={{ fill: '#4A5568', fontSize: 10 }} axisLine={false} tickLine={false} />
                                    <YAxis type="category" dataKey="name" width={120} tick={{ fill: '#8899AA', fontSize: 10 }} axisLine={false} tickLine={false} />
                                    <Tooltip content={<CUSTOM_TOOLTIP />} />
                                    <Bar dataKey="count" radius={[0, 4, 4, 0]}>
                                        {Object.keys(stats.type_breakdown).map((_, i) => (
                                            <Cell key={i} fill={PALETTE[i % PALETTE.length]} />
                                        ))}
                                    </Bar>
                                </BarChart>
                            </ResponsiveContainer>
                        </div>

                        {/* ROI Panel */}
                        <div className="glass-card glow-green" style={{ padding: '20px 24px' }}>
                            <div className="section-header">
                                <span className="section-title">ROI Projection</span>
                            </div>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 14, paddingTop: 8 }}>
                                {[
                                    { label: 'Hours Saved (batch)', val: `${(stats.auto_closed * 0.75).toFixed(0)}h`, color: 'var(--accent-green)' },
                                    { label: 'Annual Cost Savings', val: `$${((stats.auto_closed * 0.75 * 55 * 12 * 4) / 1000).toFixed(0)}K`, color: 'var(--accent-teal)' },
                                    { label: 'Avg Pipeline Cost', val: `~$0.0001/alert`, color: 'var(--accent-amber)' },
                                    { label: 'vs Manual (6 FTE)', val: `$660K / yr`, color: 'var(--accent-red)' },
                                ].map(row => (
                                    <div key={row.label} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                        <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{row.label}</span>
                                        <span style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: '0.95rem', color: row.color }}>{row.val}</span>
                                    </div>
                                ))}
                            </div>
                            <hr className="section-divider" />
                            <button className="btn btn-secondary btn-sm" style={{ width: '100%', justifyContent: 'center', marginTop: 4 }}
                                onClick={() => { setStats(null); setOverview(prev => prev ? { ...prev, processed: false } : prev); }}>
                                ↺ Reset & Re-run
                            </button>
                        </div>
                    </div>
                </>
            )}
        </div>
    );
}
