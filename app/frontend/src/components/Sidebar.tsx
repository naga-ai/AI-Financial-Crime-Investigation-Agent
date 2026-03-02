'use client';

import { useEffect, useState } from 'react';
import type { Page } from '@/app/page';

const NAV = [
    {
        label: 'WS Clarity — Compliance',
        items: [
            { id: 'dashboard', icon: '⬡', label: 'Executive Summary' },
            { id: 'alerts', icon: '◈', label: 'Investigation Queue' },
            { id: 'reports', icon: '☐', label: 'STR Report Review' },
            { id: 'patterns', icon: '⌬', label: 'Pattern Discovery' },
            { id: 'model', icon: '⎔', label: 'Model Intelligence' },
        ],
    },
    {
        label: 'WS Pulse — Client AI',
        items: [
            { id: 'pulse', icon: '⟁', label: 'Pulse Intelligence' },
        ],
    },
    {
        label: 'Infrastructure',
        items: [
            { id: 'observability', icon: '◎', label: 'Observability & Traces' },
        ],
    },
];

interface Props {
    active: Page;
    onNavigate: (p: Page) => void;
}

export default function Sidebar({ active, onNavigate }: Props) {
    const [apiOk, setApiOk] = useState<boolean | null>(null);

    useEffect(() => {
        fetch((process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000') + '/api/health')
            .then(r => setApiOk(r.ok))
            .catch(() => setApiOk(false));
    }, []);

    return (
        <aside className="sidebar">
            <div className="sidebar-logo">
                <div className="sidebar-logo-icon">W</div>
                <div className="sidebar-logo-text">
                    <div className="sidebar-logo-title">WS Intelligence</div>
                    <div className="sidebar-logo-sub">AI-Native Platform</div>
                </div>
            </div>

            {NAV.map(section => (
                <div key={section.label} className="sidebar-section">
                    <div className="sidebar-label">{section.label}</div>
                    {section.items.map(item => (
                        <button
                            key={item.id}
                            className={`nav-item${active === item.id ? ' active' : ''}`}
                            onClick={() => onNavigate(item.id as Page)}
                        >
                            <span className="nav-icon">{item.icon}</span>
                            {item.label}
                        </button>
                    ))}
                </div>
            ))}

            <div className="sidebar-footer">
                <div className="system-status">
                    <div className={`status-dot${apiOk === false ? ' offline' : ''}`} />
                    <div className="status-text">
                        {apiOk === null ? 'Connecting...' : apiOk ? 'API Connected' : 'API Offline'}
                    </div>
                </div>
            </div>
        </aside>
    );
}
