'use client';

import { useEffect, useState, useCallback } from 'react';
import { getReports, makeDecision, type Report } from '@/lib/api';

const DECISION_STYLE: Record<string, string> = {
    APPROVED: 'badge-green',
    REJECTED: 'badge-red',
    ESCALATED: 'badge-amber',
    PENDING: 'badge-gray',
};

export default function ReportsPage() {
    const [reports, setReports] = useState<Report[]>([]);
    const [loading, setLoading] = useState(true);
    const [expanded, setExpanded] = useState<string | null>(null);
    const [tab, setTab] = useState<'pending' | 'reviewed'>('pending');
    const [acting, setActing] = useState<string | null>(null);

    const load = useCallback(async () => {
        const data = await getReports();
        setReports(data.reports);
        setLoading(false);
    }, []);

    useEffect(() => { load(); }, [load]);

    const decide = async (alertId: string, decision: string) => {
        setActing(alertId);
        try {
            await makeDecision(alertId, decision);
            await load();
        } finally { setActing(null); }
    };

    const pending = reports.filter(r => r.decision === 'PENDING');
    const reviewed = reports.filter(r => r.decision !== 'PENDING');
    const display = tab === 'pending' ? pending : reviewed;

    if (loading) return <div className="loading-center"><div className="spinner spinner-lg" /></div>;

    if (!reports.length) {
        return (
            <div className="empty-state glass-card" style={{ padding: 40 }}>
                <div className="empty-icon">☐</div>
                <h3>No STR Reports Yet</h3>
                <p>Run the pipeline from the Executive Summary page first.</p>
            </div>
        );
    }

    // KPI row
    const approved = reports.filter(r => r.decision === 'APPROVED').length;
    const rejected = reports.filter(r => r.decision === 'REJECTED').length;
    const escalated = reports.filter(r => r.decision === 'ESCALATED').length;

    const expandedReport = reports.find(r => r.alert_id === expanded);

    return (
        <div>
            {/* KPI row */}
            <div className="kpi-grid animate-fade-in">
                {[
                    { label: 'Total Reports', value: reports.length, color: 'teal' },
                    { label: 'Pending Review', value: pending.length, color: 'amber' },
                    { label: 'Approved', value: approved, color: 'green' },
                    { label: 'Rejected', value: rejected, color: 'red' },
                    { label: 'Escalated', value: escalated, color: 'blue' },
                    { label: 'STR Rate', value: `${reports.length ? ((reports.filter(r => r.recommended_filing).length / reports.length) * 100).toFixed(0) : 0}%`, color: 'purple' },
                ].map((k, i) => (
                    <div key={k.label} className={`glass-card kpi-card ${k.color} animate-fade-in-up`} style={{ animationDelay: `${i * 0.05}s` }}>
                        <div className="kpi-label">{k.label}</div>
                        <div className="kpi-value">{k.value}</div>
                    </div>
                ))}
            </div>

            <hr className="section-divider" />

            {/* Tab filter */}
            <div className="tab-bar">
                <button className={`tab-item${tab === 'pending' ? ' active' : ''}`} onClick={() => setTab('pending')}>
                    Pending ({pending.length})
                </button>
                <button className={`tab-item${tab === 'reviewed' ? ' active' : ''}`} onClick={() => setTab('reviewed')}>
                    Reviewed ({reviewed.length})
                </button>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: expandedReport ? '1fr 1.8fr' : '1fr', gap: 20 }}>
                {/* List */}
                <div style={{ maxHeight: '65vh', overflowY: 'auto', paddingRight: 4 }}>
                    {display.length === 0 && (
                        <div className="notice notice-success"><span>✓</span> <span>All reports reviewed!</span></div>
                    )}
                    {display.map((rep, idx) => (
                        <div
                            key={rep.alert_id}
                            className={`glass-card animate-fade-in-up`}
                            style={{
                                padding: '16px 20px', marginBottom: 10, cursor: 'pointer',
                                animationDelay: `${idx * 0.04}s`,
                                borderLeft: `3px solid ${rep.risk_score >= 60 ? 'var(--accent-red)' : rep.risk_score >= 30 ? 'var(--accent-amber)' : 'var(--accent-green)'}`,
                                outline: expanded === rep.alert_id ? '1px solid var(--accent-green)' : 'none',
                            }}
                            onClick={() => setExpanded(expanded === rep.alert_id ? null : rep.alert_id)}
                        >
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 10 }}>
                                <div>
                                    <div style={{ fontFamily: 'monospace', fontSize: '0.72rem', color: 'var(--text-muted)' }}>{rep.report_id}</div>
                                    <div style={{ fontWeight: 600, fontSize: '0.88rem', marginTop: 3 }}>
                                        {(rep.subject_info as Record<string, string>).name ?? rep.alert_id}
                                    </div>
                                </div>
                                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 5 }}>
                                    <span style={{ fontFamily: 'var(--font-display)', fontWeight: 800, fontSize: '1.1rem', color: rep.risk_score >= 60 ? 'var(--accent-red)' : rep.risk_score >= 30 ? 'var(--accent-amber)' : 'var(--accent-green)' }}>
                                        {rep.risk_score.toFixed(0)}/100
                                    </span>
                                    <span className={`badge ${DECISION_STYLE[rep.decision] ?? 'badge-gray'}`}>{rep.decision}</span>
                                </div>
                            </div>
                            {rep.recommended_filing && (
                                <div style={{ marginTop: 8 }}>
                                    <span className="badge badge-red">⚑ STR RECOMMENDED</span>
                                </div>
                            )}
                        </div>
                    ))}
                </div>

                {/* Report detail */}
                {expandedReport && (
                    <div className="glass-card animate-slide-in" style={{ padding: 26, maxHeight: '65vh', overflowY: 'auto' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 16 }}>
                            <div>
                                <div style={{ fontFamily: 'monospace', fontSize: '0.72rem', color: 'var(--text-muted)' }}>{expandedReport.report_id}</div>
                                <h3>{(expandedReport.subject_info as Record<string, string>).name}</h3>
                            </div>
                            <button className="btn btn-secondary btn-sm" onClick={() => setExpanded(null)}>✕</button>
                        </div>

                        {/* Quick stats */}
                        <div style={{ display: 'flex', gap: 10, marginBottom: 16, flexWrap: 'wrap' }}>
                            <span className={`badge ${DECISION_STYLE[expandedReport.decision]}`}>{expandedReport.decision}</span>
                            <span className="badge badge-gray">{expandedReport.suspicion_type.replace(/_/g, ' ')}</span>
                            {expandedReport.recommended_filing && <span className="badge badge-red">⚑ FILE STR</span>}
                        </div>

                        {/* FINTRAC indicators */}
                        {expandedReport.risk_indicators?.length > 0 && (
                            <div style={{ marginBottom: 16 }}>
                                <div className="section-title" style={{ fontSize: '0.76rem', marginBottom: 8 }}>FINTRAC Indicators</div>
                                {expandedReport.risk_indicators.map((ri, i) => (
                                    <div key={i} style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: 3 }}>• {ri}</div>
                                ))}
                            </div>
                        )}

                        {/* Narrative */}
                        <div className="section-title" style={{ fontSize: '0.76rem', marginBottom: 8 }}>Report Narrative</div>
                        <div className="report-narrative" dangerouslySetInnerHTML={{
                            __html: expandedReport.narrative
                                .replace(/^## (.*)/gm, '<h2>$1</h2>')
                                .replace(/^### (.*)/gm, '<h3>$1</h3>')
                                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                                .replace(/\n\n/g, '<br /><br />')
                        }} />

                        {/* Decision panel */}
                        {expandedReport.decision === 'PENDING' && (
                            <>
                                <hr className="section-divider" />
                                <div className="section-title" style={{ marginBottom: 12 }}>Compliance Officer Decision</div>
                                <div className="decision-panel">
                                    <button className="btn btn-success" disabled={acting === expandedReport.alert_id} onClick={() => decide(expandedReport.alert_id, 'APPROVED')}>
                                        {acting === expandedReport.alert_id ? <span className="spinner" style={{ width: 14, height: 14 }} /> : '✓'} Approve
                                    </button>
                                    <button className="btn btn-danger" disabled={acting === expandedReport.alert_id} onClick={() => decide(expandedReport.alert_id, 'REJECTED')}>
                                        ✕ Reject
                                    </button>
                                    <button className="btn btn-warning" disabled={acting === expandedReport.alert_id} onClick={() => decide(expandedReport.alert_id, 'ESCALATED')}>
                                        ↑ Escalate
                                    </button>
                                </div>
                            </>
                        )}

                        {expandedReport.decision !== 'PENDING' && (
                            <div className={`notice ${expandedReport.decision === 'APPROVED' ? 'notice-success' : expandedReport.decision === 'REJECTED' ? 'notice-error' : 'notice-warning'}`} style={{ marginTop: 16 }}>
                                <span>{expandedReport.decision === 'APPROVED' ? '✓' : expandedReport.decision === 'REJECTED' ? '✕' : '↑'}</span>
                                <span>Decision recorded: <strong>{expandedReport.decision}</strong></span>
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}
