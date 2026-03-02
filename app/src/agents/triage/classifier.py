"""XGBoost-based alert triage classifier.

Prioritizes AML alerts by likelihood of being true positives,
enabling analysts to focus on the highest-risk cases first.
In production, this replaces manual Level 1 triage entirely.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import classification_report, precision_recall_fscore_support
from sklearn.model_selection import StratifiedKFold
from xgboost import XGBClassifier

from src.config import DATA_DIR
from src.data.models import AMLAlert, ClientProfile, Transaction
from src.agents.triage.features import (
    FEATURE_NAMES,
    build_training_dataset,
    extract_features_for_alert,
    _build_indices,
)

MODEL_DIR = DATA_DIR.parent.parent / "agents" / "triage"
MODEL_PATH = MODEL_DIR / "triage_model.joblib"


@dataclass
class TriageResult:
    """Output of the triage classifier for a single alert."""
    alert_id: str
    should_investigate: bool
    priority: str  # high / medium / low
    confidence: float
    risk_factors: list[str]
    classification_time_ms: float
    cache_hit: bool = False


def train_triage_model(save: bool = True) -> tuple[XGBClassifier, dict]:
    """Train the triage classifier on generated alert data.

    Uses stratified k-fold cross-validation to evaluate, then trains
    a final model on all data. Returns (model, result_dict) where result_dict
    includes cv_metrics, top_features, fold_details, training_samples, etc.
    """
    start_time = time.time()
    df = build_training_dataset()
    X = df[FEATURE_NAMES].values
    y = df["is_true_positive"].values
    n_samples = len(df)
    n_tp = int(y.sum())
    n_fp = int(len(y) - y.sum())

    print(f"Training triage classifier on {n_samples} alerts "
          f"({n_tp} true positives, {n_fp} false positives)")

    model = XGBClassifier(
        n_estimators=200,
        max_depth=5,
        learning_rate=0.1,
        min_child_weight=3,
        subsample=0.8,
        colsample_bytree=0.8,
        scale_pos_weight=(len(y) - y.sum()) / max(y.sum(), 1),
        eval_metric="logloss",
        random_state=42,
    )

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_scores = {"precision": [], "recall": [], "f1": []}
    fold_details: list[dict[str, float]] = []

    for fold, (train_idx, val_idx) in enumerate(cv.split(X, y)):
        X_train, X_val = X[train_idx], X[val_idx]
        y_train, y_val = y[train_idx], y[val_idx]

        model.fit(X_train, y_train)
        y_pred = model.predict(X_val)

        p, r, f1, _ = precision_recall_fscore_support(y_val, y_pred, average="binary", zero_division=0)
        cv_scores["precision"].append(p)
        cv_scores["recall"].append(r)
        cv_scores["f1"].append(f1)
        fold_details.append({"fold": fold + 1, "precision": float(p), "recall": float(r), "f1": float(f1)})
        print(f"  Fold {fold+1}: P={p:.3f} R={r:.3f} F1={f1:.3f}")

    metrics = {k: {"mean": np.mean(v), "std": np.std(v)} for k, v in cv_scores.items()}
    print(f"\nCV Results: P={metrics['precision']['mean']:.3f}±{metrics['precision']['std']:.3f} "
          f"R={metrics['recall']['mean']:.3f}±{metrics['recall']['std']:.3f} "
          f"F1={metrics['f1']['mean']:.3f}±{metrics['f1']['std']:.3f}")

    print("\nTraining final model on all data...")
    model.fit(X, y)

    importances = {k: float(v) for k, v in zip(FEATURE_NAMES, model.feature_importances_)}
    top_features = sorted(importances.items(), key=lambda x: x[1], reverse=True)[:10]
    print("Top 10 features:")
    for feat, imp in top_features:
        print(f"  {feat}: {imp:.4f}")

    training_time_ms = (time.time() - start_time) * 1000
    serializable_metrics = {
        k: {mk: float(mv) for mk, mv in v.items()} for k, v in metrics.items()
    }
    result = {
        "cv_metrics": serializable_metrics,
        "top_features": [[k, v] for k, v in top_features],
        "fold_details": fold_details,
        "training_samples": n_samples,
        "true_positives": n_tp,
        "false_positives": n_fp,
        "training_time_ms": round(training_time_ms, 2),
    }

    if save:
        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        joblib.dump(model, MODEL_PATH)
        metrics_path = MODEL_DIR / "triage_metrics.json"
        with open(metrics_path, "w") as f:
            json.dump(result, f, indent=2)
        print(f"\nModel saved to {MODEL_PATH}")
        print(f"Metrics saved to {metrics_path}")

    return model, result


class TriageClassifier:
    """Production triage classifier with caching and explainability."""

    def __init__(self, model_path: Path = MODEL_PATH):
        self.model: XGBClassifier = joblib.load(model_path)
        self._cache: dict[str, TriageResult] = {}

    def _compute_cache_key(self, features: dict[str, float]) -> str:
        key_features = [
            features.get("alert_type_encoded", 0),
            round(features.get("total_amount", 0), -2),  # round to nearest 100
            features.get("triggered_txn_count", 0),
            features.get("has_crypto", 0),
            features.get("has_privacy_coin", 0),
            features.get("client_risk_encoded", 0),
        ]
        return str(key_features)

    def _extract_risk_factors(self, features: dict[str, float]) -> list[str]:
        """Translate feature values into human-readable risk factors for analysts."""
        factors = []
        if features.get("has_privacy_coin", 0) > 0:
            factors.append("Privacy coin (Monero/Zcash) involvement detected")
        if features.get("amount_near_threshold_ratio", 0) > 0.5:
            factors.append("Multiple transactions near $10K FINTRAC reporting threshold")
        if features.get("velocity_ratio_7d", 0) > 3.0:
            factors.append(f"Transaction velocity {features['velocity_ratio_7d']:.1f}x above baseline (7-day)")
        if features.get("anomalous_ip_ratio", 0) > 0.3:
            factors.append("Transactions from high-risk IP addresses")
        if features.get("amount_to_income_ratio", 0) > 2.0:
            factors.append(f"Transaction amount {features['amount_to_income_ratio']:.1f}x declared income")
        if features.get("client_is_pep", 0) > 0:
            factors.append("Client is a Politically Exposed Person (PEP)")
        if features.get("has_wire", 0) > 0 and features.get("total_amount", 0) > 25_000:
            factors.append(f"Large wire transfer(s) totaling ${features['total_amount']:,.0f}")
        if features.get("client_kyc_flagged", 0) > 0:
            factors.append("Client KYC status is flagged")
        if features.get("off_hours_txn_ratio", 0) > 0.5:
            factors.append("Majority of transactions outside business hours")
        if features.get("deposit_withdrawal_ratio", 0) > 5:
            factors.append("Unusual deposit-to-withdrawal ratio (flow-through pattern)")
        if features.get("txn_time_span_hours", 0) < 2 and features.get("triggered_txn_count", 0) > 3:
            factors.append("Rapid burst of transactions within short window")
        return factors if factors else ["Elevated risk score from combined indicators"]

    def classify(
        self,
        alert: AMLAlert,
        client_map: dict[str, ClientProfile],
        client_txns: dict[str, list[Transaction]],
        txn_map: dict[str, Transaction],
    ) -> TriageResult:
        """Classify a single alert. Returns priority + confidence + risk factors."""
        start = time.time()

        features = extract_features_for_alert(alert, client_map, client_txns, txn_map)

        cache_key = self._compute_cache_key(features)
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            return TriageResult(
                alert_id=alert.alert_id,
                should_investigate=cached.should_investigate,
                priority=cached.priority,
                confidence=cached.confidence,
                risk_factors=cached.risk_factors,
                classification_time_ms=(time.time() - start) * 1000,
                cache_hit=True,
            )

        X = np.array([[features[f] for f in FEATURE_NAMES]])
        proba = self.model.predict_proba(X)[0]
        suspicious_prob = float(proba[1]) if len(proba) > 1 else float(proba[0])

        if suspicious_prob >= 0.7:
            priority = "high"
            investigate = True
        elif suspicious_prob >= 0.4:
            priority = "medium"
            investigate = True
        else:
            priority = "low"
            investigate = False

        risk_factors = self._extract_risk_factors(features)

        elapsed = (time.time() - start) * 1000
        result = TriageResult(
            alert_id=alert.alert_id,
            should_investigate=investigate,
            priority=priority,
            confidence=suspicious_prob,
            risk_factors=risk_factors,
            classification_time_ms=elapsed,
        )

        self._cache[cache_key] = result
        return result
