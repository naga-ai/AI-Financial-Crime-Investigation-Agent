"""Quick test: pattern discovery + trace collection."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.orchestrator import InvestigationPipeline
from src.agents.pattern_discovery.clustering import discover_patterns
from src.observability.langfuse_setup import trace_store


pipeline = InvestigationPipeline()
results = pipeline.process_batch()

investigations = [r.investigation for r in results if r.investigation]
print(f"Investigations for clustering: {len(investigations)}")

patterns = discover_patterns(investigations, method="kmeans", n_clusters=5)
n = patterns["n_clusters"]
print(f"Clusters found: {n}")
for c in patterns["clusters"]:
    cid = c["cluster_id"]
    sz = c["size"]
    risk = c["avg_risk_score"]
    print(f"  Cluster {cid}: {sz} cases, avg risk={risk:.0f}")
    for char in c["characteristics"]:
        print(f"    - {char}")

stats = trace_store.get_stats()
print(f"\nTrace stats:\n{json.dumps(stats, indent=2)}")
recent = trace_store.get_recent(3)
print(f"\nSample traces:\n{json.dumps(recent, indent=2)}")
