'use client';

import { useState, useCallback } from 'react';
import { getResults, discoverPatterns, type Cluster } from '@/lib/api';
import { ScatterChart, Scatter, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';

const PALETTE = ['#00D166', '#00BCD4', '#FFC107', '#FF5252', '#448AFF', '#9C27B0'];

export default function PatternsPage() {
    const [clusters, setClusters] = useState<Cluster[]>([]);
    const [summary, setSummary] = useState<{ n_clusters: number; total: number; noise: number } | null>(null);
    const [method, setMethod] = useState('kmeans');
    const [n, setN] = useState(5);
    const [running, setRunning] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const run = useCallback(async () => {
        setRunning(true);
        setError(null);
        try {
            // First confirm we have investigations
            const results = await getResults();
            const invCount = results.results.filter(r => r.investigation).length;
            if (invCount < 5) throw new Error(`Need at least 5 investigations (have ${invCount}). Run the pipeline first.`);

            const result = await discoverPatterns(method, n);
            setClusters(result.clusters);
            setSummary({ n_clusters: result.n_clusters, total: result.total_investigations, noise: result.noise_points });
        } catch (e) { setError(String(e)); }
        finally { setRunning(false); }
    }, [method, n]);

    // Simple scatter data from cluster centroids
    const scatterData = clusters.flatMap(c => ([{ x: c.avg_risk_score, y: c.size, cluster: c.cluster_id, label: `Cluster ${c.cluster_id}` }]));

    return (
        <div>
            <div className="glass-card animate-fade-in-up" style={{ padding: '24px 28px', marginBottom: 24 }}>
                <h3 style={{ marginBottom: 6 }}>Unsupervised Fraud Pattern Discovery</h3>
                <p style={{ marginBottom: 20, fontSize: '0.85rem' }}>Run K-Means or DBSCAN clustering on completed investigations to reveal emerging typologies not captured by existing rule-based detection.</p>
                <div style={{ display: 'flex', gap: 16, alignItems: 'flex-end', flexWrap: 'wrap' }}>
                    <div style={{ minWidth: 140 }}>
                        <label>Algorithm</label>
                        <select value={method} onChange={e => setMethod(e.target.value)}>
                            <option value="kmeans">K-Means</option>
                            <option value="dbscan">DBSCAN</option>
                        </select>
                    </div>
                    {method === 'kmeans' && (
                        <div style={{ minWidth: 140 }}>
                            <label>Clusters (k)</label>
                            <input type="number" value={n} min={2} max={8} onChange={e => setN(Number(e.target.value))} />
                        </div>
                    )}
                    <button className="btn btn-primary" onClick={run} disabled={running}>
                        {running ? <><span className="spinner" style={{ width: 14, height: 14 }} /> Discovering…</> : '⌬ Run Clustering'}
                    </button>
                </div>
                {error && <div className="notice notice-error" style={{ marginTop: 14 }}><span>⚠</span><span>{error}</span></div>}
            </div>

            {summary && (
                <>
                    <div className="kpi-grid animate-fade-in">
                        {[
                            { label: 'Clusters Found', value: summary.n_clusters, color: 'green' },
                            { label: 'Cases Analyzed', value: summary.total, color: 'blue' },
                            { label: 'Noise Points', value: summary.noise, color: 'amber' },
                        ].map(({ label, value, color }, i) => (
                            <div key={label} className={`glass-card kpi-card ${color} animate-fade-in-up`} style={{ animationDelay: `${i * 0.07}s` }}>
                                <div className="kpi-label">{label}</div>
                                <div className="kpi-value">{value}</div>
                            </div>
                        ))}
                    </div>

                    <hr className="section-divider" />

                    {/* Scatter: Risk vs Size */}
                    <div className="glass-card animate-fade-in-up" style={{ padding: '20px 24px', marginBottom: 24, animationDelay: '0.15s' }}>
                        <div className="section-header"><span className="section-title">Risk Score vs Cluster Size</span></div>
                        <ResponsiveContainer width="100%" height={200}>
                            <ScatterChart margin={{ left: 10, right: 20, top: 10, bottom: 10 }}>
                                <XAxis dataKey="x" name="Avg Risk Score" tick={{ fill: '#8899AA', fontSize: 11 }} label={{ value: 'Avg Risk Score', position: 'insideBottom', offset: -4, fill: '#4A5568', fontSize: 11 }} />
                                <YAxis dataKey="y" name="Cluster Size" tick={{ fill: '#8899AA', fontSize: 11 }} label={{ value: 'Size', angle: -90, position: 'insideLeft', fill: '#4A5568', fontSize: 11 }} />
                                <Tooltip contentStyle={{ background: '#0E1520', border: '1px solid rgba(255,255,255,0.1)', fontSize: 12, borderRadius: 8 }} cursor={{ strokeDasharray: '3 3', stroke: 'rgba(255,255,255,0.1)' }} />
                                <Scatter data={scatterData} name="Clusters">
                                    {scatterData.map((_, i) => <Cell key={i} fill={PALETTE[i % PALETTE.length]} />)}
                                </Scatter>
                            </ScatterChart>
                        </ResponsiveContainer>
                    </div>

                    {/* Cluster cards */}
                    <div className="section-header"><span className="section-title">Cluster Profiles</span></div>
                    <div className="grid-2 animate-fade-in-up" style={{ animationDelay: '0.2s' }}>
                        {clusters.sort((a, b) => b.avg_risk_score - a.avg_risk_score).map(c => (
                            <div key={c.cluster_id} className={`glass-card ${c.avg_risk_score >= 50 ? 'glow-red' : c.avg_risk_score >= 35 ? 'glow-amber' : 'glow-green'}`} style={{ padding: '20px 22px' }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
                                    <div>
                                        <span className="badge badge-gray" style={{ marginBottom: 5, display: 'inline-block' }}>Cluster {c.cluster_id}</span>
                                        <div style={{ fontFamily: 'var(--font-display)', fontSize: '1.5rem', fontWeight: 800, color: c.avg_risk_score >= 50 ? 'var(--accent-red)' : c.avg_risk_score >= 35 ? 'var(--accent-amber)' : 'var(--accent-green)' }}>
                                            {c.avg_risk_score.toFixed(0)}<span style={{ fontSize: '0.85rem', fontWeight: 400, color: 'var(--text-muted)' }}>/100</span>
                                        </div>
                                    </div>
                                    <div style={{ textAlign: 'right' }}>
                                        <div style={{ fontFamily: 'var(--font-display)', fontSize: '1.8rem', fontWeight: 800, color: 'var(--text-primary)' }}>{c.size}</div>
                                        <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>cases</div>
                                    </div>
                                </div>
                                <hr className="section-divider" style={{ margin: '10px 0' }} />
                                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginTop: 10 }}>
                                    <div>
                                        <div style={{ fontSize: '0.72rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 6 }}>Characteristics</div>
                                        {c.characteristics.slice(0, 4).map((ch, i) => (
                                            <div key={i} style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginBottom: 4 }}>→ {ch}</div>
                                        ))}
                                    </div>
                                    <div>
                                        <div style={{ fontSize: '0.72rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 6 }}>Actions</div>
                                        {Object.entries(c.action_distribution).map(([k, v]) => (
                                            <div key={k} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.78rem', marginBottom: 4 }}>
                                                <span style={{ color: 'var(--text-secondary)' }}>{k.replace(/_/g, ' ')}</span>
                                                <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>{v}</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </>
            )}
        </div>
    );
}
