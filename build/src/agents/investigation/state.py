"""Investigation state schema for the LangGraph state machine.

Tracks every step of an AML investigation from initial context gathering
through risk assessment, mirroring the workflow a Level 2 AML analyst
follows when reviewing an escalated alert.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field
from typing_extensions import TypedDict


class InvestigationState(TypedDict, total=False):
    """Shared state passed between investigation nodes.

    Each node reads what it needs and writes its findings back,
    building a complete evidence package for the report agent.
    """

    # Input
    alert_id: str
    client_id: str
    alert_type: str
    triggered_transaction_ids: list[str]
    severity_score: float

    # Context gathered
    client_profile: dict[str, Any]
    account_summary: dict[str, Any]
    transaction_history: list[dict[str, Any]]

    # Analysis results
    watchlist_results: dict[str, Any]
    velocity_analysis: dict[str, Any]
    typology_matches: list[dict[str, Any]]
    entity_network: dict[str, Any]
    crypto_analysis: dict[str, Any]
    behavioral_baseline: dict[str, Any]

    # Routing flags
    has_crypto: bool
    has_network: bool

    # Final assessment
    risk_score: float
    risk_level: str  # critical / high / medium / low
    confidence: float
    recommended_action: str  # file_str / escalate / close
    risk_factors: list[str]

    # RAG-retrieved regulatory context
    rag_context: dict[str, Any]

    # Investigation metadata
    steps_taken: list[dict[str, Any]]
    errors: list[str]
    total_cost_usd: float
