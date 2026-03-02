'use client';

import { useEffect, useState, useCallback, useRef } from 'react';
import KpiCard from '@/components/KpiCard';
import {
    getOverview, processAlerts, getStats, getApiBase,
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

const PIPELINE_STEPS = [
    { label: 'Ingesting AML Alerts',     icon: '⚠',  color: 'var(--accent-amber)' },
    { label: 'XGBoost Triage',           icon: '⚡', color: 'var(--accent-green)' },
    { label: 'Auto-closing False Positives', icon: '✓', color: 'var(--accent-green)' },
    { label: 'LangGraph Investigation',  icon: '🔍', color: 'var(--accent-teal)' },
    { label: 'Watchlist Screening',      icon: '🛡',  color: 'var(--accent-blue)' },
    { label: 'Typology Matching',        icon: '⬡',  color: 'var(--accent-purple)' },
    { label: 'GPT-4o-mini STR Report',   icon: '📄', color: 'var(--accent-amber)' },
    { label: 'Regulatory Filing Ready',  icon: '✅', color: 'var(--accent-green)' },
];

const TXN_ICONS = ['$', '€', '₿', '$', '$', '⟁', '$', '€', '$', '₿'];

function PipelineAnimation({ limit }: { limit: number }) {
    const [step, setStep] = useState(0);
    const [txns, setTxns] = useState<Array<{ id: number; x: number; flagged: boolean }>>([]);
    const idRef = useRef(0);

    useEffect(() => {
        const stepTimer = setInterval(() => {
            setStep(s => (s + 1) % PIPELINE_STEPS.length);
        }, 1400);
        return () => clearInterval(stepTimer);
    }, []);

    useEffect(() => {
        const spawnTimer = setInterval(() => {
            idRef.current += 1;
            const id = idRef.current;
            setTxns(prev => [...prev.slice(-14), { id, x: 0, flagged: Math.random() < 0.2 }]);
        }, 280);
        return () => clearInterval(spawnTimer);
    }, []);

    useEffect(() => {
        const moveTimer = setInterval(() => {
            setTxns(prev => prev.map(t => ({ ...t, x: t.x + 3 })).filter(t => t.x < 110));
        }, 60);
        return () => clearInterval(moveTimer);
    }, []);

    const current = PIPELINE_STEPS[step];

    return (
        <div style={{ padding: '32px 28px', textAlign: 'center' }}>
            {/* Title */}
            <div style={{ marginBottom: 28 }}>
                <div style={{ fontSize: '0.7rem', fontWeight: 700, letterSpacing: '0.12em', textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: 8 }}>
                    AI Pipeline Processing
                </div>
                <div style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--text-primary)' }}>
                    Analysing {limit.toLocaleString()} AML Alerts
                </div>
            </div>

            {/* Transaction river */}
            <div style={{ position: 'relative', height: 48, background: 'rgba(0,0,0,0.25)', borderRadius: 12, overflow: 'hidden', marginBottom: 24, border: '1px solid rgba(255,255,255,0.07)' }}>
                <div style={{ position: 'absolute', left: 0, top: 0, bottom: 0, width: '22%', background: 'linear-gradient(90deg, rgba(14,21,32,0.9) 60%, transparent)', zIndex: 2, pointerEvents: 'none' }} />
                <div style={{ position: 'absolute', right: 0, top: 0, bottom: 0, width: '22%', background: 'linear-gradient(270deg, rgba(14,21,32,0.9) 60%, transparent)', zIndex: 2, pointerEvents: 'none' }} />
                {txns.map((t, i) => (
                    <div key={t.id} style={{
                        position: 'absolute',
                        top: '50%',
                        left: `${t.x}%`,
                        transform: 'translateY(-50%)',
                        fontSize: '0.78rem',
                        fontWeight: 700,
                        color: t.flagged ? 'var(--accent-red)' : 'var(--accent-green)',
                        opacity: t.flagged ? 1 : 0.65,
                        transition: 'left 0.06s linear',
                        userSelect: 'none',
                    }}>
                        {TXN_ICONS[i % TXN_ICONS.length]}
                    </div>
                ))}
                <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.65rem', color: 'var(--text-muted)', letterSpacing: '0.1em', textTransform: 'uppercase', zIndex: 1, pointerEvents: 'none' }}>
                    Transaction stream
                </div>
            </div>

            {/* Active step */}
            <div style={{ marginBottom: 24, minHeight: 64 }}>
                <div style={{ fontSize: '2rem', marginBottom: 8 }}>{current.icon}</div>
                <div style={{ fontSize: '1.1rem', fontWeight: 700, color: current.color, transition: 'color 0.4s' }}>
                    {current.label}
                </div>
                <div style={{ display: 'flex', justifyContent: 'center', gap: 4, marginTop: 10 }}>
                    {[0, 1, 2].map(i => (
                        <div key={i} style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--accent-green)', animation: `bounce 1.2s ${i * 0.2}s infinite` }} />
                    ))}
                </div>
            </div>

            {/* Step progress dots */}
            <div style={{ display: 'flex', justifyContent: 'center', gap: 8, marginBottom: 24 }}>
                {PIPELINE_STEPS.map((s, i) => (
                    <div key={s.label} style={{
                        width: i === step ? 20 : 8, height: 8, borderRadius: 4,
                        background: i <= step ? 'var(--accent-green)' : 'rgba(255,255,255,0.12)',
                        transition: 'all 0.4s',
                    }} />
                ))}
            </div>

            {/* Stats strip */}
            <div style={{ display: 'flex', justifyContent: 'center', gap: 32, fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                {[
                    { label: 'XGBoost', val: '<2ms' },
                    { label: 'Auto-close', val: '~80%' },
                    { label: 'LangGraph', val: '9 tools' },
                    { label: 'LLM model', val: 'GPT-4o-mini' },
                ].map(s => (
                    <div key={s.label}>
                        <div style={{ fontWeight: 700, color: 'var(--text-secondary)', fontSize: '0.85rem' }}>{s.val}</div>
                        <div>{s.label}</div>
                    </div>
                ))}
            </div>
        </div>
    );
}

export default function DashboardPage() {
    const [overview, setOverview] = useState<Overview | null>(null);
    const [stats, setStats] = useState<Stats | null>(null);
    const [loading, setLoading] = useState(false);
    const [running, setRunning] = useState(false);
    const [limit, setLimit] = useState(100);
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
        const apiUrl = getApiBase();
        return (
            <div className="notice notice-error animate-fade-in">
                <span>⚠</span>
                <div>
                    <strong>Connection Error</strong><br />
                    <span style={{ fontSize: '0.78rem' }}>{error}</span><br />
                    <em style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                        API expected at <code>{apiUrl}</code> — ensure the backend container is running and port 8000 is open.
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
                    <KpiCard label="False Positives" value={fmt(overview.false_positives)} color="purple" delay={0.2} />
                    <KpiCard label="Status" value={overview.processed ? 'Processed' : 'Ready'} color="green" delay={0.25} />
                </div>
            )}

            {/* Run control */}
            {!stats && (
                <div className="glass-card animate-fade-in-up" style={{ marginBottom: 24, overflow: 'hidden' }}>
                    {running ? (
                        <PipelineAnimation limit={limit} />
                    ) : (
                        <div style={{ padding: '28px 32px', maxWidth: 560 }}>
                            <h3 style={{ marginBottom: 6 }}>Run the Investigation Pipeline</h3>
                            <p style={{ marginBottom: 20, fontSize: '0.875rem', color: 'var(--text-muted)' }}>
                                Kick off the XGBoost triage → LangGraph investigation → STR report generation pipeline on all {overview?.n_alerts} AML alerts.
                            </p>
                            <div style={{ display: 'flex', gap: 14, alignItems: 'flex-end', flexWrap: 'wrap' }}>
                                <div style={{ flex: 1, minWidth: 200 }}>
                                    <label>Alerts to Process</label>
                                    <select
                                        value={limit}
                                        onChange={e => setLimit(Number(e.target.value))}
                                        style={{ width: '100%' }}
                                    >
                                        {[25, 50, 100, 150, 200, overview?.n_alerts].filter((v): v is number => !!v && v > 0).filter((v, i, arr) => arr.indexOf(v) === i).sort((a, b) => a - b).map(n => (
                                            <option key={n} value={n}>{n === overview?.n_alerts ? `${n} (all)` : n}</option>
                                        ))}
                                    </select>
                                </div>
                                <button className="btn btn-primary btn-lg" onClick={handleRun} disabled={running}>
                                    ▶ Run Pipeline
                                </button>
                            </div>
                        </div>
                    )}
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
                                    { label: 'Est. Annual Savings', val: `$${((stats.auto_closed * 0.75 * 50 * 12) / 1000).toFixed(0)}K`, color: 'var(--accent-teal)' },
                                    { label: 'Avg Pipeline Cost', val: `~$0.04 / alert`, color: 'var(--accent-amber)' },
                                    { label: 'Manual Equivalent', val: `~$${(stats.auto_closed * 0.75 * 50 / 1000).toFixed(0)}K / batch`, color: 'var(--accent-red)' },
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
