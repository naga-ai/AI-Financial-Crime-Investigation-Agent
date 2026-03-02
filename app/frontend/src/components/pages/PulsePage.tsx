'use client';

import { useEffect, useState, useCallback, useRef } from 'react';
import { processPulse, getPulseResults, type PulseResult } from '@/lib/api';

const PRIORITY_COLOR: Record<string, string> = {
    critical: 'badge-red',
    high: 'badge-red',
    medium: 'badge-amber',
    low: 'badge-green',
};

const PULSE_STEPS = [
    { label: 'Queuing Financial Events',      icon: '⟁',  color: 'var(--accent-teal)' },
    { label: 'Masking PII Data',              icon: '🔒', color: 'var(--accent-amber)' },
    { label: 'Checking Cache',                icon: '⚡', color: 'var(--accent-green)' },
    { label: 'Loading Client Portfolios',     icon: '◉',  color: 'var(--accent-blue)' },
    { label: 'Running LangGraph Agent',       icon: '⬡',  color: 'var(--accent-purple)' },
    { label: 'GPT-4o-mini Reasoning',         icon: '✦',  color: 'var(--accent-teal)' },
    { label: 'Scoring Recommendations',       icon: '⎔',  color: 'var(--accent-green)' },
    { label: 'Delivering Insights',           icon: '✅', color: 'var(--accent-green)' },
];

const SAMPLE_NAMES = ['SC', 'JL', 'AM', 'RK', 'MP', 'TN', 'BW', 'FD', 'YC', 'HL', 'GR', 'SB', 'DM', 'KP', 'AL'];
const AVATAR_COLORS = ['#00BCD4', '#00D166', '#FFC107', '#448AFF', '#9C27B0', '#FF5252'];

function PulseAnimation({ maxEvt }: { maxEvt: number }) {
    const [step, setStep] = useState(0);
    const [processed, setProcessed] = useState(0);
    const [avatars, setAvatars] = useState<Array<{ id: number; initials: string; color: string; done: boolean }>>([]);
    const idRef = useRef(0);

    useEffect(() => {
        const t = setInterval(() => setStep(s => (s + 1) % PULSE_STEPS.length), 1200);
        return () => clearInterval(t);
    }, []);

    useEffect(() => {
        const t = setInterval(() => {
            setProcessed(p => Math.min(p + 1, maxEvt));
        }, 900);
        return () => clearInterval(t);
    }, [maxEvt]);

    useEffect(() => {
        const t = setInterval(() => {
            idRef.current += 1;
            const id = idRef.current;
            const initials = SAMPLE_NAMES[id % SAMPLE_NAMES.length];
            const color = AVATAR_COLORS[id % AVATAR_COLORS.length];
            setAvatars(prev => {
                const next = [...prev, { id, initials, color, done: false }];
                if (next.length > 2) next[next.length - 3] = { ...next[next.length - 3], done: true };
                return next.slice(-8);
            });
        }, 700);
        return () => clearInterval(t);
    }, []);

    const current = PULSE_STEPS[step];
    const progress = Math.round((processed / maxEvt) * 100);

    return (
        <div style={{ padding: '36px 28px', textAlign: 'center' }}>
            {/* Title */}
            <div style={{ marginBottom: 28 }}>
                <div style={{ fontSize: '0.7rem', fontWeight: 700, letterSpacing: '0.12em', textTransform: 'uppercase', color: 'var(--accent-teal)', marginBottom: 8 }}>
                    WS Pulse — Client AI
                </div>
                <div style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--text-primary)' }}>
                    Processing {maxEvt} Financial Events
                </div>
            </div>

            {/* Rolling avatar row */}
            <div style={{ display: 'flex', justifyContent: 'center', gap: 10, marginBottom: 28, minHeight: 56, alignItems: 'center' }}>
                {avatars.map((a) => (
                    <div key={a.id} style={{
                        width: 44, height: 44, borderRadius: '50%',
                        border: `2px solid ${a.done ? 'rgba(0,209,102,0.5)' : a.color}`,
                        background: a.done ? 'rgba(0,209,102,0.08)' : `${a.color}18`,
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        fontSize: '0.78rem', fontWeight: 800,
                        color: a.done ? 'var(--accent-green)' : a.color,
                        transition: 'all 0.5s ease',
                        flexShrink: 0,
                        position: 'relative',
                    }}>
                        {a.done ? '✓' : a.initials}
                        {!a.done && (
                            <div style={{
                                position: 'absolute', inset: -4, borderRadius: '50%',
                                border: `1px solid ${a.color}`,
                                opacity: 0.3,
                                animation: 'pulse-ring 1.5s ease-out infinite',
                            }} />
                        )}
                    </div>
                ))}
            </div>

            {/* Active step */}
            <div style={{ marginBottom: 20, minHeight: 72 }}>
                <div style={{ fontSize: '1.8rem', marginBottom: 8 }}>{current.icon}</div>
                <div style={{ fontSize: '1.05rem', fontWeight: 700, color: current.color, transition: 'color 0.4s' }}>
                    {current.label}
                </div>
                <div style={{ display: 'flex', justifyContent: 'center', gap: 5, marginTop: 10 }}>
                    {[0, 1, 2].map(i => (
                        <div key={i} style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--accent-teal)', animation: `bounce 1.2s ${i * 0.2}s infinite` }} />
                    ))}
                </div>
            </div>

            {/* Step progress dots */}
            <div style={{ display: 'flex', justifyContent: 'center', gap: 8, marginBottom: 22 }}>
                {PULSE_STEPS.map((s, i) => (
                    <div key={s.label} style={{
                        width: i === step ? 20 : 8, height: 8, borderRadius: 4,
                        background: i <= step ? 'var(--accent-teal)' : 'rgba(255,255,255,0.12)',
                        transition: 'all 0.4s',
                    }} />
                ))}
            </div>

            {/* Progress bar */}
            <div style={{ margin: '0 auto 20px', maxWidth: 400 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', color: 'var(--text-muted)', marginBottom: 6 }}>
                    <span>Events processed</span>
                    <span style={{ color: 'var(--accent-teal)', fontWeight: 700 }}>{processed} / {maxEvt}</span>
                </div>
                <div style={{ height: 6, background: 'rgba(255,255,255,0.08)', borderRadius: 6, overflow: 'hidden' }}>
                    <div style={{
                        height: '100%', borderRadius: 6,
                        background: 'linear-gradient(90deg, var(--accent-teal), var(--accent-green))',
                        width: `${progress}%`, transition: 'width 0.8s ease',
                    }} />
                </div>
            </div>

            {/* Stats strip */}
            <div style={{ display: 'flex', justifyContent: 'center', gap: 32, fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                {[
                    { label: 'LangGraph', val: 'Agent' },
                    { label: 'LLM', val: 'GPT-4o-mini' },
                    { label: 'Latency', val: '<1s' },
                    { label: 'PII', val: 'Masked' },
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

            {/* Processing animation */}
            {running && (
                <div className="glass-card glow-teal animate-fade-in" style={{ marginBottom: 24, borderColor: 'rgba(0,188,212,0.2)' }}>
                    <PulseAnimation maxEvt={maxEvt} />
                </div>
            )}

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
                    <div className="section-header">
                        <span className="section-title">Users & Recommendations</span>
                        <span className="badge badge-gray">{results.filter(r => r.recommendation).length} of {results.length} events generated actions</span>
                    </div>
                    <div className="grid-2 animate-fade-in-up" style={{ animationDelay: '0.15s' }}>
                        {results.map((r, idx) => {
                            const rec = r.recommendation;
                            return (
                                <div key={idx} className="glass-card" style={{
                                    padding: '18px 22px',
                                    borderLeft: `3px solid ${rec ? 'var(--accent-teal)' : 'rgba(255,255,255,0.1)'}`,
                                    opacity: rec ? 1 : 0.6,
                                }}>
                                    {/* User + event header */}
                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12, paddingBottom: 10, borderBottom: '1px solid rgba(255,255,255,0.07)' }}>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                                            <div style={{ width: 36, height: 36, borderRadius: '50%', border: '1px solid rgba(0,188,212,0.35)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.8rem', fontWeight: 800, color: 'var(--accent-teal)', background: 'rgba(0,188,212,0.08)', flexShrink: 0 }}>
                                                {(r.display_name ?? r.user_id).split(' ').map((w: string) => w[0]).join('').slice(0, 2).toUpperCase()}
                                            </div>
                                            <div>
                                                <div style={{ fontWeight: 700, fontSize: '0.9rem', color: 'var(--text-primary)' }}>{r.display_name ?? r.user_id}</div>
                                                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontFamily: 'monospace' }}>
                                                    {r.user_id} · {r.event_type.replace(/_/g, ' ').toLowerCase()}
                                                </div>
                                            </div>
                                        </div>
                                        <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
                                            {rec && <span className={`badge ${PRIORITY_COLOR[rec.priority] ?? 'badge-gray'}`}>{rec.priority.toUpperCase()}</span>}
                                            {r.cache_hit && <span className="badge badge-teal" style={{ fontSize: '0.62rem' }}>CACHE ✓</span>}
                                            {!rec && <span className="badge badge-gray" style={{ fontSize: '0.62rem' }}>NO ACTION</span>}
                                        </div>
                                    </div>

                                    {rec ? (
                                        <>
                                            {/* Recommendation body */}
                                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
                                                <div style={{ fontWeight: 700, fontSize: '0.9rem', color: 'var(--text-primary)', flex: 1, marginRight: 12 }}>{rec.title}</div>
                                                <div style={{ textAlign: 'right', flexShrink: 0 }}>
                                                    <div style={{ fontFamily: 'var(--font-display)', fontWeight: 800, fontSize: '1rem', color: 'var(--accent-teal)' }}>
                                                        ${rec.estimated_value_cad.toLocaleString('en-CA', { minimumFractionDigits: 0 })}
                                                    </div>
                                                    <div style={{ fontSize: '0.66rem', color: 'var(--text-muted)' }}>est. value CAD</div>
                                                </div>
                                            </div>
                                            <p style={{ fontSize: '0.8rem', marginBottom: 10, lineHeight: 1.55, color: 'var(--text-secondary)' }}>{rec.summary}</p>
                                            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
                                                <span className="badge badge-blue">{rec.action.replace(/_/g, ' ')}</span>
                                                <span style={{ fontSize: '0.71rem', color: 'var(--text-muted)' }}>Confidence: {(rec.confidence * 100).toFixed(0)}%</span>
                                                <span style={{ fontSize: '0.71rem', color: 'var(--text-muted)' }}>{r.processing_time_ms.toFixed(0)}ms</span>
                                            </div>
                                        </>
                                    ) : (
                                        <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontStyle: 'italic' }}>
                                            Event processed — no actionable recommendation generated for this event type.
                                        </div>
                                    )}
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
