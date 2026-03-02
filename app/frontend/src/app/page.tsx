'use client';

import { useState } from 'react';
import Sidebar from '@/components/Sidebar';
import DashboardPage from '@/components/pages/DashboardPage';
import AlertQueuePage from '@/components/pages/AlertQueuePage';
import ReportsPage from '@/components/pages/ReportsPage';
import ModelPage from '@/components/pages/ModelPage';
import ObsPage from '@/components/pages/ObsPage';
import PatternsPage from '@/components/pages/PatternsPage';
import PulsePage from '@/components/pages/PulsePage';

export type Page = 'dashboard' | 'alerts' | 'reports' | 'model' | 'observability' | 'patterns' | 'pulse';

export default function HomePage() {
  const [page, setPage] = useState<Page>('dashboard');

  const renderPage = () => {
    switch (page) {
      case 'dashboard': return <DashboardPage />;
      case 'alerts': return <AlertQueuePage />;
      case 'reports': return <ReportsPage />;
      case 'model': return <ModelPage />;
      case 'observability': return <ObsPage />;
      case 'patterns': return <PatternsPage />;
      case 'pulse': return <PulsePage />;
      default: return <DashboardPage />;
    }
  };

  const PAGE_META: Record<Page, { title: string; subtitle: string }> = {
    dashboard: { title: 'Executive Summary', subtitle: 'Real-time overview of the AI-native AML investigation pipeline' },
    alerts: { title: 'Investigation Queue', subtitle: 'Cases flagged for human review, ranked by risk score' },
    reports: { title: 'STR Report Review', subtitle: 'AI-generated Suspicious Transaction Reports — compliance officer decision required' },
    model: { title: 'Model Intelligence', subtitle: 'XGBoost triage classifier performance, features, and roadmap' },
    observability: { title: 'Observability & Tracing', subtitle: 'Per-span cost tracking, latency distribution, and trace explorer' },
    patterns: { title: 'Pattern Discovery', subtitle: 'Unsupervised clustering reveals emerging fraud typologies' },
    pulse: { title: 'WS Pulse', subtitle: 'Client financial intelligence — personalized, tax-aware recommendations' },
  };

  const meta = PAGE_META[page];

  return (
    <div className="app-shell">
      {/* Background ambient glows */}
      <div className="bg-glow bg-glow-1" />
      <div className="bg-glow bg-glow-2" />

      <Sidebar active={page} onNavigate={setPage} />

      <main className="main-content">
        <header className="topbar">
          <div className="topbar-left">
            <h1>{meta.title}</h1>
            <p>{meta.subtitle}</p>
          </div>
          <div className="topbar-right">
            <span className="badge badge-green" style={{ fontSize: '0.7rem' }}>
              ● LIVE
            </span>
            <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
              {new Date().toLocaleDateString('en-CA', { month: 'short', day: 'numeric', year: 'numeric' })}
            </span>
          </div>
        </header>

        <div className="page-body">
          {renderPage()}
        </div>
      </main>
    </div>
  );
}
