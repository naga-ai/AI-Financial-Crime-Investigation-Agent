"""Run the investigation pipeline on sample alerts to verify the full flow."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.orchestrator import InvestigationPipeline


def main() -> None:
    print("=" * 70)
    print("AML Investigation Pipeline -- End-to-End Test")
    print("=" * 70)

    pipeline = InvestigationPipeline()
    print(f"Loaded {len(pipeline.alerts)} alerts\n")

    print("Processing all alerts...")
    print("-" * 70)
    results = pipeline.process_batch()

    print("\n" + "=" * 70)
    stats = pipeline.get_statistics()
    print("\nPipeline Statistics:")
    print(f"  Total processed:    {stats['total_processed']}")
    print(f"  Auto-closed:        {stats['auto_close_rate']}")
    print(f"  Investigated:       {stats['investigated']}")
    print(f"  Pending STR review: {stats['pending_str_review']}")
    print(f"  Avg pipeline time:  {stats['timing']['avg_pipeline_ms']:.0f}ms")
    print(f"  Avg triage time:    {stats['timing']['avg_triage_ms']:.1f}ms")

    print("\nStatus breakdown:")
    for status, count in stats["status_breakdown"].items():
        print(f"  {status}: {count}")

    print("\nCache performance:")
    for region in stats["cache_stats"]:
        print(f"  {region['region']}: {region['hits']} hits / {region['misses']} misses "
              f"(hit rate: {region['hit_rate']:.0%})")

    # Show details for one investigated case
    investigated = [r for r in results if r.investigation]
    if investigated:
        case = investigated[0]
        print(f"\n{'=' * 70}")
        print(f"Sample Investigation Detail: {case.alert_id}")
        print(f"{'=' * 70}")
        inv = case.investigation
        print(f"  Client:      {case.client_id}")
        print(f"  Alert type:  {case.alert_type}")
        print(f"  Risk score:  {inv.get('risk_score', 0)}")
        print(f"  Risk level:  {inv.get('risk_level', 'N/A')}")
        print(f"  Confidence:  {inv.get('confidence', 0):.0%}")
        print(f"  Action:      {inv.get('recommended_action', 'N/A')}")
        print(f"\n  Risk factors:")
        for rf in inv.get("risk_factors", []):
            print(f"    - {rf}")
        print(f"\n  Investigation steps ({len(inv.get('steps_taken', []))}):")
        for step in inv.get("steps_taken", []):
            print(f"    {step['step_name']:30s} | {step['tool_called']:30s} | {step['duration_ms']:.0f}ms")


if __name__ == "__main__":
    main()
