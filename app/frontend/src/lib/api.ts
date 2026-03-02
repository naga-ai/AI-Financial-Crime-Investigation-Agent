/**
 * API client for the WS Intelligence Platform FastAPI backend.
 * All methods call the Python API running on port 8000.
 */

// Internal Docker service hostnames — not resolvable from a browser
const DOCKER_INTERNAL = new Set(['api', 'backend', 'server']);

function isPrivateIP(hostname: string): boolean {
  // Check for internal/private IP ranges
  if (hostname.startsWith('127.') || hostname.startsWith('10.') || hostname.startsWith('192.168.')) return true;
  if (hostname.startsWith('172.')) {
    const second = parseInt(hostname.split('.')[1], 10);
    if (second >= 16 && second <= 31) return true; // 172.16.0.0/12
  }
  return false;
}

export function getApiBase(): string {
  // In the browser: always derive the API host from the current page host.
  // This makes the app portable across any deployment (EC2, localhost, etc.)
  // without needing the correct URL baked in at build time.
  if (typeof window !== 'undefined') {
    const { protocol, hostname } = window.location;
    // Override only if env var points to a real public host (not Docker internal, not localhost, not private IP)
    const raw = process.env.NEXT_PUBLIC_API_URL || '';
    try {
      if (raw) {
        const u = new URL(raw);
        if (u.hostname && !DOCKER_INTERNAL.has(u.hostname) && u.hostname !== 'localhost' && !isPrivateIP(u.hostname)) {
          return raw;
        }
      }
    } catch { /* ignore */ }
    return `${protocol}//${hostname}:8000`;
  }
  // Server-side (SSR / build): use env var or localhost
  return process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
}

const BASE = getApiBase();

async function api<T>(path: string, options?: RequestInit): Promise<T> {
    const res = await fetch(`${BASE}${path}`, {
        headers: { 'Content-Type': 'application/json' },
        ...options,
    });
    if (!res.ok) {
        const text = await res.text();
        throw new Error(`API ${path} returned ${res.status}: ${text}`);
    }
    return res.json();
}

// ─── Overview ──────────────────────────────────────────────────────
export const getOverview = () => api<Overview>('/api/overview');
export const getHealth = () => api<{ status: string }>('/api/health');

// ─── Pipeline ──────────────────────────────────────────────────────
export const processAlerts = (limit: number) =>
    api<{ processed: number; timestamp: string }>('/api/alerts/process', {
        method: 'POST',
        body: JSON.stringify({ limit }),
    });

export const getResults = () => api<ResultsResponse>('/api/alerts/results');
export const getStats = () => api<Stats>('/api/alerts/stats');

// ─── Reports ───────────────────────────────────────────────────────
export const getReports = () => api<{ reports: Report[] }>('/api/reports');
export const makeDecision = (alertId: string, decision: string) =>
    api<{ alert_id: string; decision: string }>(`/api/reports/${alertId}/decision`, {
        method: 'POST',
        body: JSON.stringify({ decision }),
    });

// ─── Patterns ──────────────────────────────────────────────────────
export const discoverPatterns = () =>
    api<PatternResult>('/api/patterns/discover', {
        method: 'POST',
        body: JSON.stringify({ method: 'kmeans', n_clusters: 5 }),
    });

// ─── Observability ─────────────────────────────────────────────────
export const getObsStats = () => api<ObsStats>('/api/observability/stats');
export const getObsTraces = (limit = 50) => api<{ traces: Trace[] }>(`/api/observability/traces?limit=${limit}`);

// ─── Model ─────────────────────────────────────────────────────────
export const getModelMetrics = () => api<ModelMetrics>('/api/model/metrics');
export const trainModel = () =>
    api<ModelMetrics>('/api/model/train', { method: 'POST' });

// ─── Pulse ─────────────────────────────────────────────────────────
export const processPulse = (maxEvents: number) =>
    api<{ processed: number }>(`/api/pulse/process?max_events=${maxEvents}`, { method: 'POST' });
export const getPulseResults = () => api<{ results: PulseResult[] }>('/api/pulse/results');

// ─── Types ─────────────────────────────────────────────────────────
export interface Overview {
    n_clients: number;
    n_transactions: number;
    n_alerts: number;
    true_positives: number;
    false_positives: number;
    alert_types: Record<string, number>;
    processed: boolean;
    run_timestamp: string | null;
}

export interface Triage {
    priority: string;
    confidence: number;
    should_investigate: boolean;
    classification_time_ms: number;
    risk_factors: string[];
}

export interface Investigation {
    risk_score: number;
    risk_level: string;
    confidence: number;
    recommended_action: string;
    risk_factors: string[];
    steps_taken: Step[];
    typology_matches: Typology[];
    client_profile: Record<string, unknown>;
    transaction_history: Transaction[];
}

export interface Step {
    step_name: string;
    tool_called: string;
    duration_ms: number;
    timestamp?: string;
}

export interface Typology {
    typology_name: string;
    match_score: number;
    fintrac_reference: string;
}

export interface Transaction {
    timestamp: string;
    type: string;
    amount_cad: number;
    currency: string;
    method: string;
    description: string;
}

export interface ReportSummary {
    report_id: string;
    risk_score: number;
    recommended_filing: boolean;
    narrative: string;
    risk_indicators: string[];
    suspicion_type: string;
    subject_info: Record<string, unknown>;
}

export interface AlertResult {
    alert_id: string;
    client_id: string;
    alert_type: string;
    status: string;
    total_pipeline_time_ms: number;
    triage: Triage | null;
    investigation: Investigation | null;
    report: ReportSummary | null;
}

export interface ResultsResponse {
    processed: boolean;
    run_timestamp: string;
    results: AlertResult[];
}

export interface Stats {
    n: number;
    auto_closed: number;
    auto_rate: number;
    investigated: number;
    pending_str: number;
    escalated: number;
    reports: number;
    decisions_made: number;
    avg_latency_ms: number;
    status_breakdown: Record<string, number>;
    type_breakdown: Record<string, number>;
    risk_data: Array<{ risk_score: number; risk_level: string; alert_type: string; action: string; pipeline_ms: number }>;
}

export interface Report extends ReportSummary {
    alert_id: string;
    decision: string;
}

export interface Cluster {
    cluster_id: number;
    size: number;
    avg_risk_score: number;
    characteristics: string[];
    dominant_alert_types: string[];
    action_distribution: Record<string, number>;
    centroid: Record<string, number>;
}

export interface PatternResult {
    n_clusters: number;
    total_investigations: number;
    noise_points: number;
    clusters: Cluster[];
    cluster_assignments: Record<string, number>;
    point_coordinates?: Record<string, [number, number]>;
}

export interface ObsStats {
    total_traces: number;
    total_spans: number;
    total_cost_usd: number;
    avg_cost_usd: number;
    avg_duration_ms: number;
    max_duration_ms: number;
}

export interface Trace {
    trace_id: string;
    alert_id: string;
    span_count: number;
    total_duration_ms: number;
    total_cost_usd: number;
    metadata: Record<string, unknown>;
    spans: SpanData[];
}

export interface SpanData {
    name: string;
    duration_ms: number;
    cost_usd: number;
    status: string;
}

export interface FoldDetail {
    fold: number;
    precision: number;
    recall: number;
    f1: number;
}

export interface ModelMetrics {
    cv_metrics: {
        precision: { mean: number; std: number };
        recall: { mean: number; std: number };
        f1: { mean: number; std: number };
    };
    top_features: [string, number][];
    fold_details?: FoldDetail[];
    training_samples?: number;
    true_positives?: number;
    false_positives?: number;
    training_time_ms?: number;
}

export interface PulseResult {
    user_id: string;
    display_name?: string;
    event_type: string;
    processing_time_ms: number;
    cache_hit: boolean;
    recommendation: {
        title: string;
        priority: string;
        action: string;
        confidence: number;
        estimated_value_cad: number;
        summary: string;
    } | null;
}
