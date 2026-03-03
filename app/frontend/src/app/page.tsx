'use client';

import { useEffect, useState } from 'react';
import Sidebar from '@/components/Sidebar';
import OverviewPage from '@/components/pages/OverviewPage';
import DashboardPage from '@/components/pages/DashboardPage';
import ArchitecturePage from '@/components/pages/ArchitecturePage';
import AlertQueuePage from '@/components/pages/AlertQueuePage';
import ReportsPage from '@/components/pages/ReportsPage';
import ModelPage from '@/components/pages/ModelPage';
import ObsPage from '@/components/pages/ObsPage';
import PatternsPage from '@/components/pages/PatternsPage';
import PulsePage from '@/components/pages/PulsePage';

export type Page = 'overview' | 'architecture' | 'dashboard' | 'alerts' | 'reports' | 'model' | 'observability' | 'patterns' | 'pulse';

export default function HomePage() {
  const [page, setPage] = useState<Page>('overview');
  const [theme, setTheme] = useState<'dark' | 'light'>('dark');

  useEffect(() => {
    const saved = localStorage.getItem('ws-theme') as 'dark' | 'light' | null;
    if (saved) setTheme(saved);
  }, []);

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('ws-theme', theme);
  }, [theme]);

  const renderPage = () => {
    switch (page) {
      case 'overview': return <OverviewPage />;
      case 'architecture': return <ArchitecturePage />;
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
    overview: { title: '', subtitle: '' },
    architecture: { title: 'Project Architecture', subtitle: 'Agents, ML models, and data flow — one-pager diagram' },
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

      <main className="main-content" data-page={page}>
        <header className="topbar">
          {meta.title ? (
            <div className="topbar-left">
              <h1>{meta.title}</h1>
              <p>{meta.subtitle}</p>
            </div>
          ) : (
            <div className="topbar-left" />
          )}
          <div className="topbar-right">
            <span className="badge badge-green" style={{ fontSize: '0.7rem' }}>
              ● LIVE
            </span>
            <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
              {new Date().toLocaleDateString('en-CA', { month: 'short', day: 'numeric', year: 'numeric' })}
            </span>
            <button
              onClick={() => setTheme(t => t === 'dark' ? 'light' : 'dark')}
              title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
              style={{
                background: 'var(--bg-card)',
                border: '1px solid var(--border-light)',
                borderRadius: 'var(--radius-md)',
                color: 'var(--text-secondary)',
                cursor: 'pointer',
                fontSize: '0.95rem',
                width: 32,
                height: 32,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                transition: 'background var(--transition), border-color var(--transition)',
                flexShrink: 0,
              }}
            >
              {theme === 'dark' ? '☀' : '🌙'}
            </button>
          </div>
        </header>

        <div className="page-body">
          {renderPage()}
        </div>
      </main>
    </div>
  );
}
