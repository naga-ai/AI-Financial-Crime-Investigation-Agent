#!/usr/bin/env python3
"""
End-to-end demo: WS Intelligence Platform
==========================================

Demonstrates both WS Clarity (AML compliance) and WS Pilot (client
financial intelligence) pipelines, including shared production
infrastructure (PII masking, event queuing, latency tracking).

Run:  python scripts/demo.py
"""

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.orchestrator import InvestigationPipeline
from src.agents.pattern_discovery.clustering import discover_patterns
from src.observability.langfuse_setup import trace_store


DIVIDER = "=" * 72
THIN = "-" * 72


def print_header(title: str) -> None:
    print(f"\n{DIVIDER}")
    print(f"  {title}")
    print(DIVIDER)


def demo_data_overview(pipeline: InvestigationPipeline) -> None:
    """Show the scale and diversity of the synthetic dataset."""
    print_header("STAGE 0: Synthetic Dataset Overview")

    n_clients = len(pipeline.clients)
    n_txns = len(pipeline.transactions)
    n_alerts = len(pipeline.alerts)

    alert_types = {}
    for a in pipeline.alerts:
        t = a.alert_type.value
        alert_types[t] = alert_types.get(t, 0) + 1
    tp_count = sum(1 for a in pipeline.alerts if a.is_true_positive)

    print(f"""
  Wealthsimple clients:     {n_clients:,}
  Transactions generated:   {n_txns:,}
  AML alerts triggered:     {n_alerts:,}
  True positives (ground):  {tp_count} ({tp_count/n_alerts*100:.0f}%)
  False positives:          {n_alerts - tp_count} ({(n_alerts-tp_count)/n_alerts*100:.0f}%)

  Alert type distribution:""")
    for atype, count in sorted(alert_types.items(), key=lambda x: -x[1]):
        print(f"    {atype:30s} {count:4d}")


def demo_single_alert(pipeline: InvestigationPipeline) -> None:
    """Walk through a single high-risk alert step by step."""
    print_header("STAGE 1: Single Alert Deep Dive")

    high_risk_alert = None
    for alert in pipeline.alerts:
        if alert.is_true_positive and alert.alert_type.value in ("structuring", "crypto_layering", "pep_sanctions_hit"):
            high_risk_alert = alert
            break
    if not high_risk_alert:
        high_risk_alert = next(a for a in pipeline.alerts if a.is_true_positive)

    print(f"""
  Selected alert: {high_risk_alert.alert_id}
  Type:           {high_risk_alert.alert_type.value}
  Client:         {high_risk_alert.client_id}
  Severity:       {high_risk_alert.severity_score:.0f}/100
  Rule:           {high_risk_alert.rule_name}
  Transactions:   {len(high_risk_alert.triggered_transactions)} flagged
""")

    # Step 1: Triage
    print(f"  {THIN}")
    print("  STEP 1 -- XGBoost Triage Classification")
    print(f"  {THIN}")
    result = pipeline.process_alert(high_risk_alert)
    triage = result.triage
    if triage:
        print(f"    Priority:     {triage.priority.upper()}")
        print(f"    Confidence:   {triage.confidence:.1%}")
        print(f"    Investigate:  {triage.should_investigate}")
        print(f"    Time:         {triage.classification_time_ms:.1f}ms")
        print(f"    Risk factors:")
        for rf in triage.risk_factors:
            print(f"      - {rf}")

    # Step 2: Investigation
    if result.investigation:
        inv = result.investigation
        print(f"\n  {THIN}")
        print("  STEP 2 -- LangGraph Investigation (9 tools, conditional routing)")
        print(f"  {THIN}")
        print(f"    Risk score:   {inv.get('risk_score', 0):.1f}/100")
        print(f"    Risk level:   {inv.get('risk_level', 'unknown')}")
        print(f"    Confidence:   {inv.get('confidence', 0):.0%}")
        print(f"    Action:       {inv.get('recommended_action', 'unknown')}")
        print(f"    Has crypto:   {inv.get('has_crypto', False)}")
        print(f"    Risk factors:")
        for rf in inv.get("risk_factors", []):
            print(f"      - {rf}")

        print(f"\n    Investigation steps ({len(inv.get('steps_taken', []))}):")
        for step in inv.get("steps_taken", []):
            name = step.get("step_name", "")
            tool = step.get("tool_called", "")
            ms = step.get("duration_ms", 0)
            print(f"      {name:35s} | {tool:35s} | {ms:.0f}ms")

    # Step 3: Report
    if result.report:
        print(f"\n  {THIN}")
        print("  STEP 3 -- FINTRAC STR Report Generation")
        print(f"  {THIN}")
        report = result.report
        print(f"    Report ID:    {report.report_id}")
        print(f"    Risk score:   {report.risk_score:.0f}/100")
        print(f"    File STR:     {'RECOMMENDED' if report.recommended_filing else 'Not recommended'}")
        print(f"    Indicators:   {len(report.risk_indicators)}")
        for ri in report.risk_indicators[:5]:
            print(f"      - {ri}")
        print(f"\n    Narrative preview (first 500 chars):")
        print(f"    {THIN}")
        for line in report.narrative[:500].split("\n"):
            print(f"    {line}")
        print(f"    ...")

    print(f"\n  Total pipeline time: {result.total_pipeline_time_ms:.0f}ms")
    print(f"  Final status: {result.status}")


def demo_batch_processing(pipeline: InvestigationPipeline) -> list:
    """Process all alerts and show aggregate statistics."""
    print_header("STAGE 2: Full Batch Processing (315 alerts)")

    t0 = time.time()
    remaining_alerts = [a for a in pipeline.alerts if a.alert_id not in {r.alert_id for r in pipeline.results}]
    results = pipeline.process_batch(alerts=remaining_alerts)
    elapsed = time.time() - t0

    all_results = pipeline.results
    stats = pipeline.get_statistics()

    statuses = {}
    for r in all_results:
        statuses[r.status] = statuses.get(r.status, 0) + 1

    investigated = [r for r in all_results if r.investigation]
    reports_generated = sum(1 for r in all_results if r.report)

    print(f"""
  Total processed:        {len(all_results)}
  Processing time:        {elapsed:.1f}s ({elapsed/len(all_results)*1000:.0f}ms/alert avg)

  Disposition breakdown:
    Auto-closed (FP):     {statuses.get('auto_closed', 0):4d}  ({statuses.get('auto_closed',0)/len(all_results)*100:.0f}%)
    Investigated:         {len(investigated):4d}  ({len(investigated)/len(all_results)*100:.0f}%)
    Pending STR review:   {statuses.get('pending_str_review', 0):4d}
    Escalated:            {statuses.get('escalated', 0):4d}
    Closed after inv:     {statuses.get('closed_after_investigation', 0):4d}
    STR reports created:  {reports_generated:4d}
""")

    # Cache performance
    from src.cache.manager import cache
    print("  Cache performance:")
    for region_stats in cache.stats:
        name = region_stats.get("region", "unknown")
        hits = region_stats.get("hits", 0)
        misses = region_stats.get("misses", 0)
        total = hits + misses
        rate = hits / total * 100 if total > 0 else 0
        if total > 0:
            print(f"    {name:20s} {hits:3d} hits / {misses:3d} misses ({rate:.0f}%)")

    return all_results


def demo_pattern_discovery(all_results: list) -> None:
    """Run unsupervised clustering to discover emerging typologies."""
    print_header("STAGE 3: Pattern Discovery (K-Means Clustering)")

    investigations = [r.investigation for r in all_results if r.investigation]
    print(f"\n  Clustering {len(investigations)} completed investigations...\n")

    patterns = discover_patterns(investigations, method="kmeans", n_clusters=5)

    for cluster in patterns["clusters"]:
        cid = cluster["cluster_id"]
        size = cluster["size"]
        risk = cluster["avg_risk_score"]
        print(f"  Cluster {cid}: {size} cases | Avg Risk: {risk:.0f}/100")
        for char in cluster["characteristics"]:
            print(f"    - {char}")
        actions = cluster["action_distribution"]
        action_str = ", ".join(f"{k}: {v}" for k, v in actions.items())
        print(f"    Actions: {action_str}")
        print()


def demo_observability() -> None:
    """Show trace and cost statistics."""
    print_header("STAGE 4: Observability & Cost Tracking")

    stats = trace_store.get_stats()
    print(f"""
  Total traces:           {stats.get('total_traces', 0)}
  Total spans:            {stats.get('total_spans', 0)}
  Estimated total cost:   ${stats.get('total_cost_usd', 0):.4f}
  Avg cost/investigation: ${stats.get('avg_cost_usd', 0):.6f}
  Avg latency:            {stats.get('avg_duration_ms', 0):.0f}ms
  Max latency:            {stats.get('max_duration_ms', 0):.0f}ms

  Production cost projection (10,000 alerts/month):
    Triage:               ~$0.01 (XGBoost, near-zero)
    Investigations:       ~$0.53 (simulated tools)
    LLM report gen:       ~$3.00 (GPT-4o-mini, 2K alerts needing reports)
    Total monthly:        ~$3.54
    vs. manual cost:      ~$166,000 (6 FTE analysts * $110K/yr / 4)
""")


def demo_human_ai_boundary() -> None:
    """Emphasize the compliance officer's role."""
    print_header("STAGE 5: Human-AI Boundary")
    print("""
  The system is designed with a clear human-in-the-loop architecture:

  WHAT THE AI DOES:
    [+] Triages 80% of false-positive alerts automatically (XGBoost)
    [+] Investigates suspicious cases through 9 analytical tools
    [+] Generates FINTRAC-compliant STR narratives
    [+] Discovers emerging typologies via unsupervised clustering
    [+] Provides full audit trail with per-span tracing

  WHAT THE COMPLIANCE OFFICER DOES:
    [*] Reviews AI-generated investigation summaries
    [*] Reads STR narratives with AI-highlighted risk indicators
    [*] Makes the FINAL decision: Approve / Reject / Escalate
    [*] Files the STR with FINTRAC (regulatory requirement)
    [*] Validates new pattern clusters for rule updates

  The AI never files an STR. It recommends. The human decides.
  This is the legally and ethically correct boundary for Canadian AML.
""")


def main():
    print(DIVIDER)
    print("  AI-Native Financial Crime Investigation Agent")
    print("  for Wealthsimple -- End-to-End Demo")
    print(DIVIDER)
    print("  Built with: LangGraph | XGBoost | LangChain | Langfuse | Streamlit")
    print(f"  Date: {time.strftime('%Y-%m-%d %H:%M')}")

    pipeline = InvestigationPipeline()

    demo_data_overview(pipeline)
    demo_single_alert(pipeline)
    all_results = demo_batch_processing(pipeline)
    demo_pattern_discovery(all_results)
    demo_observability()
    demo_human_ai_boundary()

    # ── WS Pilot Demo ──
    demo_pulse()

    print_header("DEMO COMPLETE")
    print("""
  To explore interactively:
    streamlit run src/dashboard/app.py

  Dashboard sections:
    SENTINEL  -- AML investigation pipeline
    PULSE     -- Client financial intelligence
    SHARED    -- Production metrics, model scorecards, RAG, observability
""")


def demo_pulse():
    """Demonstrate WS Pilot financial event processing."""
    print_header("WS PULSE: CLIENT FINANCIAL INTELLIGENCE")
    print()

    from src.pulse.orchestrator import PulseOrchestrator
    from src.shared.pii import pii_masker
    from src.shared.queue import event_queue
    from src.shared.latency import latency_tracker

    pulse = PulseOrchestrator()

    print(f"  Portfolios loaded: {len(pulse.portfolios)}")
    print(f"  Financial events: {len(pulse.events)}")
    print()

    for p in pulse.portfolios[:3]:
        print(f"  {p.display_name} ({p.age}, {p.province}) -- ${p.total_value:,.0f}")
        print(f"    Accounts: {len(p.accounts)} | Holdings: {len(p.all_holdings)}")
        print(f"    Risk: {p.goals.risk_profile.value} | Premium: {p.goals.has_premium}")
        print()

    print(f"  {THIN}")
    print(f"  Processing events (max 15)...")
    print()

    results = pulse.process_all_events(max_events=15)

    print(f"  Results: {len(results)} recommendations generated")
    print()

    for r in results[:5]:
        rec = r.recommendation
        if rec:
            print(f"  [{rec.priority.value.upper()}] {rec.title}")
            print(f"    User: {r.user_id} | Action: {rec.action.value}")
            print(f"    Confidence: {rec.confidence:.0%} | Value: ${rec.estimated_value_cad:,.2f}")
            print(f"    Time: {r.processing_time_ms:.1f}ms | Cache: {r.cache_hit}")
            print()

    stats = pulse.stats
    print(f"  {THIN}")
    print(f"  Pipeline Stats:")
    print(f"    Total processed: {stats['total_processed']}")
    print(f"    Avg time: {stats.get('avg_processing_time_ms', 0):.1f}ms")
    print(f"    Cache hit rate: {stats.get('cache_hit_rate', 0):.1f}%")
    print(f"    Total est. value: ${stats.get('total_estimated_value_cad', 0):,.0f}")
    print()

    print(f"  Shared Infrastructure Stats:")
    pii_stats = pii_masker.stats
    print(f"    PII operations: {pii_stats['total_operations']} ({pii_stats['unique_tokens']} unique tokens)")
    health = event_queue.health
    print(f"    Queue: {health.total_enqueued} enqueued, {health.total_processed} processed")
    all_p = latency_tracker.all_percentiles()
    for comp, p in list(all_p.items())[:5]:
        print(f"    Latency [{comp}]: P50={p['p50']:.1f}ms P95={p['p95']:.1f}ms P99={p['p99']:.1f}ms ({p['count']} samples)")
    print()


if __name__ == "__main__":
    main()
