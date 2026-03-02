'use client';

import { useEffect, useState, useCallback } from 'react';
import { getModelMetrics, type ModelMetrics } from '@/lib/api';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';

const GRADIENT = ['#00D166', '#00BCD4', '#FFC107', '#FF5252', '#448AFF'];

export default function ModelPage() {
    const [metrics, setMetrics] = useState<ModelMetrics | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const load = useCallback(async () => {
        try {
            const m = await getModelMetrics();
            setMetrics(m);
        } catch (e) { setError(String(e)); }
        finally { setLoading(false); }
    }, []);

    useEffect(() => { load(); }, [load]);

    if (loading) return <div className="loading-center"><div className="spinner spinner-lg" /></div>;
    if (error) return <div className="notice notice-error"><span>⚠</span><span>{error} — Train the model first: run <code>python scripts/train_triage.py</code></span></div>;
    if (!metrics) return null;

    const { cv_metrics, top_features } = metrics;
    const featData = top_features.map(([name, imp]) => ({ Feature: name.replace(/_/g, ' '), Importance: parseFloat(imp.toFixed(4)) }));

    const phases = [
        { label: 'Phase 1 · Now', title: 'XGBoost Triage', badge: 'Deployed', color: 'green', items: ['24 hand-engineered features', '100% Precision / 93.7% Recall', 'Sub-2ms inference, fully local', 'No GPU required, OSFI E-23 aligned'] },
        { label: 'Phase 2 · Next', title: 'SFT Investigation LLM', badge: 'Planned', color: 'amber', items: ['Fine-tune Llama 3.1 8B on investigation transcripts', '~5,000 labeled compliance decisions', 'LoRA adapter for cost-efficient training', 'Richer, artifact-free STR narratives'] },
        { label: 'Phase 3 · Future', title: 'Multi-Modal Detection', badge: 'Research', color: 'blue', items: ['Transaction Graph Neural Networks (GNN)', 'Temporal transformers for sequence anomalies', 'Contrastive learning on behavioral embeddings', 'Cross-account fingerprinting for ML rings'] },
    ];

    return (
        <div>
            {/* CV Metrics */}
            <div className="kpi-grid animate-fade-in">
                {[
                    { label: 'Precision', val: cv_metrics.precision, color: 'green' },
                    { label: 'Recall', val: cv_metrics.recall, color: 'teal' },
                    { label: 'F1 Score', val: cv_metrics.f1, color: 'blue' },
                ].map(({ label, val, color }, i) => (
                    <div key={label} className={`glass-card kpi-card ${color} animate-fade-in-up`} style={{ animationDelay: `${i * 0.07}s` }}>
                        <div className="kpi-label">{label}</div>
                        <div className="kpi-value">{(val.mean * 100).toFixed(1)}%</div>
                        <div className="kpi-sub">± {(val.std * 100).toFixed(1)}% std</div>
                    </div>
                ))}
                <div className="glass-card kpi-card amber animate-fade-in-up" style={{ animationDelay: '0.21s' }}>
                    <div className="kpi-label">Algorithm</div>
                    <div className="kpi-value" style={{ fontSize: '1.2rem' }}>XGBoost</div>
                    <div className="kpi-sub">Gradient boosted trees</div>
                </div>
                <div className="glass-card kpi-card teal animate-fade-in-up" style={{ animationDelay: '0.28s' }}>
                    <div className="kpi-label">Features</div>
                    <div className="kpi-value">24</div>
                    <div className="kpi-sub">Engineered features</div>
                </div>
                <div className="glass-card kpi-card red animate-fade-in-up" style={{ animationDelay: '0.35s' }}>
                    <div className="kpi-label">Inference</div>
                    <div className="kpi-value">&lt; 2ms</div>
                    <div className="kpi-sub">Per alert, fully local</div>
                </div>
            </div>

            <hr className="section-divider" />

            <div className="grid-2 animate-fade-in-up" style={{ animationDelay: '0.15s' }}>
                {/* Feature importance chart */}
                <div className="glass-card" style={{ padding: '20px 24px' }}>
                    <div className="section-header"><span className="section-title">Feature Importance (Top 10)</span></div>
                    <ResponsiveContainer width="100%" height={320}>
                        <BarChart layout="vertical" data={featData.slice(0, 10)} margin={{ left: 12, right: 16, top: 0, bottom: 0 }}>
                            <XAxis type="number" tick={{ fill: '#4A5568', fontSize: 10 }} axisLine={false} tickLine={false} />
                            <YAxis type="category" dataKey="Feature" width={145} tick={{ fill: '#8899AA', fontSize: 10 }} axisLine={false} tickLine={false} />
                            <Tooltip contentStyle={{ background: '#0E1520', border: '1px solid rgba(255,255,255,0.1)', fontSize: 12, borderRadius: 8 }} />
                            <Bar dataKey="Importance" radius={[0, 4, 4, 0]}>
                                {featData.slice(0, 10).map((_, i) => <Cell key={i} fill={GRADIENT[i % GRADIENT.length]} />)}
                            </Bar>
                        </BarChart>
                    </ResponsiveContainer>
                </div>

                {/* Feature groups */}
                <div className="glass-card" style={{ padding: '20px 24px' }}>
                    <div className="section-header"><span className="section-title">Feature Engineering Groups</span></div>
                    {[
                        { group: 'Transaction Patterns', count: 7, desc: 'Total/max/mean/std amounts, count, timespan, threshold ratio' },
                        { group: 'Velocity Indicators', count: 3, desc: '7-day & 30-day velocity ratios, deposit-to-withdrawal flow' },
                        { group: 'Crypto Signals', count: 3, desc: 'Crypto involvement, privacy coins (Monero/Zcash), external wallets' },
                        { group: 'Client Risk', count: 5, desc: 'KYC status, PEP flag, income ratio, risk profile, account age' },
                        { group: 'Behavioral', count: 4, desc: 'Off-hours ratio, IP anomaly, device diversity, counterparty concentration' },
                        { group: 'Alert Context', count: 2, desc: 'Alert type encoding, rule severity score' },
                    ].map(({ group, count, desc }) => (
                        <div key={group} style={{ display: 'flex', gap: 12, marginBottom: 14 }}>
                            <div style={{ width: 28, height: 28, borderRadius: 'var(--radius-sm)', background: 'var(--accent-green-dim)', color: 'var(--accent-green)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 800, fontSize: '0.8rem', flexShrink: 0 }}>{count}</div>
                            <div>
                                <div style={{ fontWeight: 600, fontSize: '0.85rem', color: 'var(--text-primary)' }}>{group}</div>
                                <div style={{ fontSize: '0.76rem', color: 'var(--text-muted)' }}>{desc}</div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            <hr className="section-divider" />

            {/* Roadmap */}
            <div className="section-header"><span className="section-title">Model Evolution Roadmap</span></div>
            <div className="grid-3 animate-fade-in-up" style={{ animationDelay: '0.25s' }}>
                {phases.map(p => (
                    <div key={p.label} className={`glass-card glow-${p.color}`} style={{ padding: '22px 24px' }}>
                        <div style={{ marginBottom: 10 }}>
                            <span className="badge badge-gray" style={{ fontSize: '0.65rem', marginBottom: 8, display: 'inline-block' }}>{p.label}</span>
                            <br />
                            <span className={`badge badge-${p.color}`}>{p.badge}</span>
                        </div>
                        <h4 style={{ marginBottom: 12 }}>{p.title}</h4>
                        {p.items.map(item => (
                            <div key={item} style={{ display: 'flex', gap: 8, marginBottom: 7, fontSize: '0.81rem', color: 'var(--text-secondary)' }}>
                                <span style={{ color: `var(--accent-${p.color})`, flexShrink: 0 }}>→</span> {item}
                            </div>
                        ))}
                    </div>
                ))}
            </div>
        </div>
    );
}
