"""Pattern discovery through unsupervised clustering.

Analyzes completed AML investigations to discover emerging fraud
typologies that weren't in the original rule set. New patterns
feed back into the triage classifier and investigation agent.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans, DBSCAN
from sklearn.preprocessing import StandardScaler

from src.agents.pattern_discovery.feature_extraction import (
    CLUSTER_FEATURE_NAMES,
    build_clustering_dataset,
)


def discover_patterns(
    investigations: list[dict[str, Any]],
    method: str = "kmeans",
    n_clusters: int = 5,
    min_samples: int = 3,
) -> dict[str, Any]:
    """Run clustering on completed investigations to find patterns.

    Args:
        investigations: List of completed investigation states.
        method: 'kmeans' or 'dbscan'.
        n_clusters: Number of clusters for K-Means.
        min_samples: Minimum samples per cluster for DBSCAN.

    Returns:
        Dict with cluster assignments, centroids, and pattern descriptions.
    """
    if len(investigations) < 5:
        return {"error": "Need at least 5 investigations for pattern discovery"}

    df = build_clustering_dataset(investigations)
    X = df[CLUSTER_FEATURE_NAMES].values

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    if method == "dbscan":
        model = DBSCAN(eps=1.5, min_samples=min_samples)
        labels = model.fit_predict(X_scaled)
    else:
        actual_k = min(n_clusters, len(X))
        model = KMeans(n_clusters=actual_k, random_state=42, n_init=10)
        labels = model.fit_predict(X_scaled)

    df["cluster"] = labels

    clusters = _analyze_clusters(df, labels, CLUSTER_FEATURE_NAMES)

    return {
        "method": method,
        "n_clusters": len(set(labels) - {-1}),
        "noise_points": int(sum(1 for l in labels if l == -1)),
        "total_investigations": len(investigations),
        "clusters": clusters,
        "cluster_assignments": {
            row["alert_id"]: int(row["cluster"])
            for _, row in df.iterrows()
        },
    }


def _analyze_clusters(
    df: pd.DataFrame,
    labels: np.ndarray,
    feature_names: list[str],
) -> list[dict[str, Any]]:
    """Analyze each cluster to describe its characteristics."""
    clusters = []
    unique_labels = sorted(set(labels))

    for label in unique_labels:
        if label == -1:
            continue

        mask = df["cluster"] == label
        cluster_df = df[mask]

        centroid = {
            feat: round(float(cluster_df[feat].mean()), 3)
            for feat in feature_names
        }

        characteristics = _describe_cluster(centroid, cluster_df)

        alert_types = cluster_df["alert_type_encoded"].value_counts()
        from src.data.models import AlertType
        type_map = {i: t.value for i, t in enumerate(AlertType)}
        dominant_types = [
            type_map.get(int(idx), f"type_{int(idx)}")
            for idx in alert_types.index[:3]
        ]

        actions = cluster_df["recommended_action"].value_counts().to_dict()

        clusters.append({
            "cluster_id": int(label),
            "size": int(mask.sum()),
            "avg_risk_score": round(float(cluster_df["risk_score"].mean()), 1),
            "dominant_alert_types": dominant_types,
            "action_distribution": actions,
            "centroid": centroid,
            "characteristics": characteristics,
            "sample_alert_ids": cluster_df["alert_id"].tolist()[:5],
        })

    return clusters


def _describe_cluster(centroid: dict[str, float], df: pd.DataFrame) -> list[str]:
    """Generate human-readable descriptions of cluster characteristics."""
    descriptions = []

    if centroid.get("risk_score", 0) >= 60:
        descriptions.append(f"High-risk cluster (avg score: {centroid['risk_score']:.0f})")
    elif centroid.get("risk_score", 0) >= 35:
        descriptions.append(f"Medium-risk cluster (avg score: {centroid['risk_score']:.0f})")
    else:
        descriptions.append(f"Low-risk cluster (avg score: {centroid['risk_score']:.0f})")

    if centroid.get("has_crypto", 0) > 0.5:
        descriptions.append("Predominantly crypto-involved cases")
    if centroid.get("has_privacy_coin", 0) > 0.3:
        descriptions.append("Privacy coin usage detected in this cluster")
    if centroid.get("has_watchlist_hit", 0) > 0.3:
        descriptions.append("Elevated watchlist match rate")
    if centroid.get("network_size", 0) > 3:
        descriptions.append(f"Complex entity networks (avg {centroid['network_size']:.0f} connections)")
    if centroid.get("velocity_ratio", 1) > 3:
        descriptions.append(f"High velocity anomaly (avg {centroid['velocity_ratio']:.1f}x baseline)")
    if centroid.get("has_wire", 0) > 0.5:
        descriptions.append("Wire transfer heavy")
    if centroid.get("off_hours_ratio", 0) > 0.3:
        descriptions.append("Significant off-hours activity")
    if centroid.get("max_amount", 0) > 50_000:
        descriptions.append(f"Large transaction values (avg max ${centroid['max_amount']:,.0f})")

    if not descriptions:
        descriptions.append("General mixed-pattern cluster")

    return descriptions
