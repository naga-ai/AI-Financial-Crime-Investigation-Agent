'use client';

import { useEffect, useState, useCallback } from 'react';
import { getModelMetrics, trainModel, type ModelMetrics } from '@/lib/api';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';

const GRADIENT = ['#00D166', '#00BCD4', '#FFC107', '#FF5252', '#448AFF'];

export default function ModelPage() {
    const [metrics, setMetrics] = useState<ModelMetrics | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [training, setTraining] = useState(false);

    const load = useCallback(async () => {
        try {
            setError(null);
            const m = await getModelMetrics();
            setMetrics(m);
        } catch (e) { setError(String(e)); }
        finally { setLoading(false); }
    }, []);

    useEffect(() => { load(); }, [load]);

    const handleRetrain = useCallback(async () => {
        if (!confirm('Retrain the triage model? This takes a few seconds and will replace the current model.')) return;
        setTraining(true);
        setError(null);
        try {
            const result = await trainModel();
            setMetrics(result);
        } catch (e) {
            setError(String(e));
        } finally {
            setTraining(false);
        }
    }, []);

    if (loading) return <div className="loading-center"><div className="spinner spinner-lg" /></div>;
    if (!metrics) {
        return (
            <div>
                <div className="notice notice-error" style={{ marginBottom: 16 }}><span>⚠</span><span>{error ?? 'Model not trained yet.'} Train the model to get started.</span></div>
                <button type="button" className="badge badge-green" style={{ cursor: training ? 'not-allowed' : 'pointer' }} onClick={handleRetrain} disabled={training}>
                    {training ? 'Training…' : 'Train model'}
                </button>
                {training && <div className="spinner spinner-sm" style={{ marginTop: 12 }} />}
            </div>
        );
    }

    const { cv_metrics, top_features } = metrics;
    const featData = top_features.map(([name, imp]) => ({ Feature: name.replace(/_/g, ' '), Importance: parseFloat(imp.toFixed(4)) }));

    const clarityAgents = [
        { name: 'Triage Agent', desc: 'XGBoost classifier — 24 features, sub-2ms inference. Auto-closes ~80% of false positives.', color: 'green' },
        { name: 'Investigation Agent', desc: 'LangGraph state machine — 9 tool nodes: velocity, watchlist, entity graph, RAG, typology matching.', color: 'teal' },
        { name: 'Report Generator', desc: 'GPT-4o-mini + template fallback — FINTRAC-compliant STR narratives with structured risk indicators.', color: 'amber' },
        { name: 'Pattern Discovery', desc: 'K-Means / DBSCAN clustering — identifies emerging fraud typologies across 10 FINTRAC categories.', color: 'blue' },
    ];

    const pulseAgents = [
        { name: 'Event Detector', desc: '6 financial event types — paycheck, earnings, market drop, rate change, dividend, rebalance.', color: 'teal' },
        { name: 'Portfolio Analyzer', desc: 'Personalized impact analysis — tax implications, concentration risk, account-type optimisation.', color: 'blue' },
        { name: 'Recommendation Agent', desc: 'RAG-grounded guidance — TFSA/RRSP-aware, plain-language, regulatory-grounded advice.', color: 'green' },
        { name: 'Narrative Agent', desc: 'Plain-language financial briefing — converts portfolio analysis into clear, jargon-free output.', color: 'purple' },
    ];

    const phases = [
        {
            label: 'Phase 1 · Deployed', title: 'XGBoost Triage Classifier', badge: 'Live', color: 'green',
            items: [
                '24 hand-engineered features across 6 groups',
                '98.3% Precision / 93.7% Recall (5-fold CV)',
                'Sub-2ms inference — fully local, no GPU',
                'Retrain from UI — hot-reloads into pipeline',
                'OSFI E-23 aligned, fully auditable',
            ],
        },
        {
            label: 'Phase 2 · Next', title: 'SFT — Supervised Fine-Tuning', badge: 'Planned', color: 'amber',
            items: [
                'Fine-tune Llama 3.1 8B on ~5,000 investigation transcripts',
                'LoRA adapter — full fine-tune on 1 x A100 in ~8h',
                'Replaces GPT-4o-mini for STR narrative generation',
                'Estimated 90% cost reduction vs OpenAI API calls',
                'Self-hosted — zero data leaves the environment',
            ],
        },
        {
            label: 'Phase 3 · Planned', title: 'DPO — Direct Preference Optimisation', badge: 'Research', color: 'blue',
            items: [
                'Rank STR outputs by compliance officer preference',
                'No reward model needed — contrastive loss on pairs',
                'Targets hallucination reduction and citation accuracy',
                'Training signal: analyst accept / revise / reject decisions',
                'Projected +15–20% accuracy gain over SFT baseline',
            ],
        },
        {
            label: 'Phase 4 · Future', title: 'GRPO — Group Relative Policy Optimisation', badge: 'Horizon', color: 'purple',
            items: [
                'RL fine-tuning without a separate value model',
                'Group sampling estimates reward from within-batch variance',
                'Multi-objective reward: accuracy + cost + latency',
                'Target: fully autonomous investigation, human-in-loop for edge cases only',
                'Enables continuous self-improvement from live compliance decisions',
            ],
        },
    ];

    return (
        <div>
            {/* Retrain + training status */}
            <div className="section-header" style={{ display: 'flex', alignItems: 'center', gap: 16, flexWrap: 'wrap', marginBottom: 16 }}>
                <span className="section-title">Triage classifier</span>
                <button
                    type="button"
                    className="badge badge-green"
                    style={{ cursor: training ? 'not-allowed' : 'pointer', opacity: training ? 0.7 : 1 }}
                    onClick={handleRetrain}
                    disabled={training}
                >
                    {training ? 'Training…' : 'Retrain model'}
                </button>
                {training && <div className="spinner spinner-sm" />}
            </div>
            {error && metrics && <div className="notice notice-error" style={{ marginBottom: 16 }}><span>⚠</span><span>{error}</span></div>}

            {/* Training run stats (when available) */}
            {(metrics.training_samples != null || metrics.training_time_ms != null) && (
                <div className="glass-card" style={{ padding: '12px 20px', marginBottom: 20 }}>
                    <div style={{ display: 'flex', gap: 24, flexWrap: 'wrap', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                        {metrics.training_samples != null && <span><strong style={{ color: 'var(--text-primary)' }}>Samples:</strong> {metrics.training_samples}</span>}
                        {metrics.true_positives != null && <span><strong style={{ color: 'var(--text-primary)' }}>True positives:</strong> {metrics.true_positives}</span>}
                        {metrics.false_positives != null && <span><strong style={{ color: 'var(--text-primary)' }}>False positives:</strong> {metrics.false_positives}</span>}
                        {metrics.training_time_ms != null && <span><strong style={{ color: 'var(--text-primary)' }}>Training time:</strong> {(metrics.training_time_ms / 1000).toFixed(2)}s</span>}
                    </div>
                </div>
            )}

            {/* Fold-by-fold CV results */}
            {metrics.fold_details && metrics.fold_details.length > 0 && (
                <div className="glass-card" style={{ padding: '20px 24px', marginBottom: 20 }}>
                    <div className="section-header"><span className="section-title">Cross-validation (5-fold)</span></div>
                    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
                        <thead>
                            <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
                                <th style={{ textAlign: 'left', padding: '8px 12px', color: 'var(--text-muted)' }}>Fold</th>
                                <th style={{ textAlign: 'right', padding: '8px 12px', color: 'var(--text-muted)' }}>Precision</th>
                                <th style={{ textAlign: 'right', padding: '8px 12px', color: 'var(--text-muted)' }}>Recall</th>
                                <th style={{ textAlign: 'right', padding: '8px 12px', color: 'var(--text-muted)' }}>F1</th>
                            </tr>
                        </thead>
                        <tbody>
                            {metrics.fold_details.map((row) => (
                                <tr key={row.fold} style={{ borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
                                    <td style={{ padding: '8px 12px' }}>{row.fold}</td>
                                    <td style={{ textAlign: 'right', padding: '8px 12px' }}>{(row.precision * 100).toFixed(1)}%</td>
                                    <td style={{ textAlign: 'right', padding: '8px 12px' }}>{(row.recall * 100).toFixed(1)}%</td>
                                    <td style={{ textAlign: 'right', padding: '8px 12px' }}>{(row.f1 * 100).toFixed(1)}%</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}

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

            {/* LLM Configuration + Agent Architecture */}
            <div className="section-header"><span className="section-title">LLM & Agent Architecture</span></div>
            <div className="grid-2 animate-fade-in-up" style={{ animationDelay: '0.1s' }}>
                {/* LLM config */}
                <div className="glass-card" style={{ padding: '20px 24px' }}>
                    <div className="section-header"><span className="section-title" style={{ fontSize: '0.9rem' }}>LLM Configuration</span></div>
                    {[
                        { label: 'Model', value: 'GPT-4o-mini', sub: 'OpenAI API · temperature 0.1' },
                        { label: 'Fallback', value: 'Template engine', sub: 'Activated when no API key is present' },
                        { label: 'Grounding', value: 'RAG', sub: 'ChromaDB semantic + TF-IDF keyword retrieval' },
                        { label: 'PII Protection', value: 'HMAC-SHA256', sub: 'Deterministic token — same input, same token' },
                        { label: 'Observability', value: 'Langfuse', sub: 'Full trace + cost tracking per LLM call' },
                        { label: 'Orchestration', value: 'LangGraph', sub: 'Stateful multi-step agent graphs with conditional routing' },
                    ].map(({ label, value, sub }) => (
                        <div key={label} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12, paddingBottom: 12, borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
                            <div style={{ fontSize: '0.81rem', color: 'var(--text-muted)', minWidth: 100 }}>{label}</div>
                            <div style={{ textAlign: 'right' }}>
                                <div style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-primary)' }}>{value}</div>
                                <div style={{ fontSize: '0.73rem', color: 'var(--text-muted)' }}>{sub}</div>
                            </div>
                        </div>
                    ))}
                </div>

                {/* Agents */}
                <div className="glass-card" style={{ padding: '20px 24px' }}>
                    <div style={{ marginBottom: 16 }}>
                        <div style={{ fontSize: '0.72rem', fontWeight: 700, letterSpacing: '0.08em', color: 'var(--accent-green)', textTransform: 'uppercase', marginBottom: 10 }}>WS Clarity — Compliance</div>
                        {clarityAgents.map(a => (
                            <div key={a.name} style={{ display: 'flex', gap: 10, marginBottom: 11 }}>
                                <div style={{ width: 6, height: 6, borderRadius: '50%', background: `var(--accent-${a.color})`, marginTop: 6, flexShrink: 0 }} />
                                <div>
                                    <div style={{ fontSize: '0.83rem', fontWeight: 600, color: 'var(--text-primary)' }}>{a.name}</div>
                                    <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)', lineHeight: 1.4 }}>{a.desc}</div>
                                </div>
                            </div>
                        ))}
                    </div>
                    <div style={{ borderTop: '1px solid rgba(255,255,255,0.08)', paddingTop: 14 }}>
                        <div style={{ fontSize: '0.72rem', fontWeight: 700, letterSpacing: '0.08em', color: 'var(--accent-teal)', textTransform: 'uppercase', marginBottom: 10 }}>WS Pulse — Client AI</div>
                        {pulseAgents.map(a => (
                            <div key={a.name} style={{ display: 'flex', gap: 10, marginBottom: 11 }}>
                                <div style={{ width: 6, height: 6, borderRadius: '50%', background: `var(--accent-${a.color})`, marginTop: 6, flexShrink: 0 }} />
                                <div>
                                    <div style={{ fontSize: '0.83rem', fontWeight: 600, color: 'var(--text-primary)' }}>{a.name}</div>
                                    <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)', lineHeight: 1.4 }}>{a.desc}</div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            <hr className="section-divider" />

            {/* Post-Training Roadmap */}
            <div className="section-header"><span className="section-title">Model Evolution & Post-Training Roadmap</span></div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 16, marginBottom: 8 }} className="animate-fade-in-up">
                {phases.map(p => (
                    <div key={p.label} className={`glass-card glow-${p.color}`} style={{ padding: '22px 24px' }}>
                        <div style={{ marginBottom: 10 }}>
                            <span className="badge badge-gray" style={{ fontSize: '0.65rem', marginBottom: 8, display: 'inline-block' }}>{p.label}</span>
                            <br />
                            <span className={`badge badge-${p.color}`}>{p.badge}</span>
                        </div>
                        <h4 style={{ marginBottom: 12, fontSize: '0.92rem' }}>{p.title}</h4>
                        {p.items.map(item => (
                            <div key={item} style={{ display: 'flex', gap: 8, marginBottom: 7, fontSize: '0.79rem', color: 'var(--text-secondary)' }}>
                                <span style={{ color: `var(--accent-${p.color})`, flexShrink: 0 }}>→</span> {item}
                            </div>
                        ))}
                    </div>
                ))}
            </div>

            <hr className="section-divider" />

            {/* Cost & Savings Projection */}
            <div className="section-header"><span className="section-title">Post-Training Cost & Performance Projection</span></div>
            <div className="glass-card animate-fade-in-up" style={{ padding: '20px 24px', marginBottom: 16 }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.83rem' }}>
                    <thead>
                        <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.12)' }}>
                            {['Stage', 'Model', 'Cost / Alert', 'Latency', 'Accuracy Gain', 'Hosting'].map(h => (
                                <th key={h} style={{ padding: '10px 14px', textAlign: 'left', color: 'var(--text-muted)', fontWeight: 600, fontSize: '0.76rem', letterSpacing: '0.05em', textTransform: 'uppercase' }}>{h}</th>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        {[
                            { stage: 'Current', badge: 'green', model: 'GPT-4o-mini (API)', cost: '~$0.020', latency: '~3.0 s', accuracy: 'Baseline', hosting: 'OpenAI API' },
                            { stage: 'After SFT', badge: 'amber', model: 'Llama 3.1 8B (LoRA)', cost: '~$0.002', latency: '~1.5 s', accuracy: '+5–10%', hosting: 'Self-hosted GPU' },
                            { stage: 'After DPO', badge: 'blue', model: 'Llama 3.1 8B (aligned)', cost: '~$0.002', latency: '~1.5 s', accuracy: '+15–20%', hosting: 'Self-hosted GPU' },
                            { stage: 'After GRPO', badge: 'purple', model: 'Llama 3.1 8B (RL-tuned)', cost: '~$0.001', latency: '~0.8 s', accuracy: '+25–30%', hosting: 'Self-hosted GPU' },
                        ].map((row, i) => (
                            <tr key={row.stage} style={{ borderBottom: i < 3 ? '1px solid rgba(255,255,255,0.06)' : 'none' }}>
                                <td style={{ padding: '11px 14px' }}><span className={`badge badge-${row.badge}`} style={{ fontSize: '0.72rem' }}>{row.stage}</span></td>
                                <td style={{ padding: '11px 14px', color: 'var(--text-primary)', fontWeight: 500 }}>{row.model}</td>
                                <td style={{ padding: '11px 14px', color: 'var(--accent-green)', fontWeight: 700 }}>{row.cost}</td>
                                <td style={{ padding: '11px 14px', color: 'var(--text-secondary)' }}>{row.latency}</td>
                                <td style={{ padding: '11px 14px', color: 'var(--text-secondary)' }}>{row.accuracy}</td>
                                <td style={{ padding: '11px 14px', color: 'var(--text-muted)', fontSize: '0.78rem' }}>{row.hosting}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
            <div className="glass-card animate-fade-in-up" style={{ padding: '14px 20px', background: 'var(--accent-green-dim)', borderLeft: '3px solid var(--accent-green)' }}>
                <div style={{ fontSize: '0.85rem', color: 'var(--text-primary)', lineHeight: 1.6 }}>
                    <strong style={{ color: 'var(--accent-green)' }}>Projected outcome:</strong> Moving from GPT-4o-mini (API) to a GRPO-tuned Llama 3.1 8B reduces per-alert LLM cost by over <strong>95%</strong>, cuts report generation latency by <strong>4x</strong>, and eliminates any dependency on external API providers — keeping all investigation data fully within Wealthsimple&apos;s infrastructure.
                </div>
            </div>
        </div>
    );
}
