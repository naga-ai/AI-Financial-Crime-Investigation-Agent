'use client';

interface KpiCardProps {
    label: string;
    value: string | number;
    sub?: string;
    color?: 'green' | 'blue' | 'amber' | 'red' | 'teal' | 'purple';
    change?: string;
    changeDir?: 'up' | 'down';
    delay?: number;
}

export default function KpiCard({ label, value, sub, color = 'green', change, changeDir, delay = 0 }: KpiCardProps) {
    return (
        <div
            className={`glass-card kpi-card ${color} animate-fade-in-up`}
            style={{ animationDelay: `${delay}s` }}
        >
            <div className="kpi-label">{label}</div>
            <div className="kpi-value">{value}</div>
            {sub && <div className="kpi-sub">{sub}</div>}
            {change && (
                <div className={`kpi-change ${changeDir ?? 'up'}`}>
                    {changeDir === 'up' ? '↑' : '↓'} {change}
                </div>
            )}
        </div>
    );
}
