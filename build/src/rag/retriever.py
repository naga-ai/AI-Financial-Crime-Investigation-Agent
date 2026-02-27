"""RAG retrieval engine for FINTRAC regulatory knowledge.

Uses ChromaDB as a vector store and LangChain embeddings to enable
semantic search over regulatory guidance, typology indicators, and
STR writing standards. Falls back to keyword matching when embeddings
are unavailable.

Two retrieval modes:
1. Regulatory Context: Given an alert type, retrieve the most relevant
   FINTRAC indicators and guidance for grounding investigation and reports.
2. Case Precedent: Given a completed investigation, find similar past
   cases to provide institutional memory for the analyst.
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from typing import Any

from src.rag.knowledge_base import FINTRAC_DOCUMENTS


@dataclass
class RetrievalResult:
    """A single document chunk returned by the retriever."""
    doc_id: str
    title: str
    content: str
    category: str
    typology: str
    relevance_score: float
    retrieval_method: str  # "semantic" or "keyword"


@dataclass
class RAGContext:
    """Assembled context from RAG retrieval for downstream use."""
    query: str
    results: list[RetrievalResult] = field(default_factory=list)
    retrieval_time_ms: float = 0.0
    method: str = "keyword"
    token_estimate: int = 0

    @property
    def context_text(self) -> str:
        """Format retrieved documents into a single context block."""
        if not self.results:
            return ""
        sections = []
        for i, r in enumerate(self.results, 1):
            sections.append(
                f"--- Source {i}: {r.title} (relevance: {r.relevance_score:.2f}) ---\n"
                f"{r.content.strip()}"
            )
        return "\n\n".join(sections)

    @property
    def source_citations(self) -> list[dict]:
        """Return structured citations for audit trail."""
        return [
            {
                "doc_id": r.doc_id,
                "title": r.title,
                "category": r.category,
                "relevance": round(r.relevance_score, 3),
            }
            for r in self.results
        ]


class RegulatoryKnowledgeRAG:
    """RAG engine for FINTRAC regulatory knowledge.

    Architecture:
    - Primary: ChromaDB with sentence-transformer embeddings (if available)
    - Fallback: TF-IDF keyword matching (always works, no GPU/API needed)

    This dual-mode approach ensures the system works in any environment
    while leveraging better retrieval when resources allow.
    """

    def __init__(self) -> None:
        self._documents = FINTRAC_DOCUMENTS
        self._chroma_collection = None
        self._tfidf_matrix = None
        self._tfidf_vectorizer = None
        self._embedding_fn = None
        self._use_semantic = False
        self._initialized = False
        self._init_time_ms = 0.0
        self._query_count = 0
        self._total_query_ms = 0.0
        self._case_store: list[dict] = []

    def initialize(self) -> dict[str, Any]:
        """Build the vector index. Try ChromaDB first, fall back to TF-IDF."""
        start = time.time()
        info: dict[str, Any] = {"documents_loaded": len(self._documents)}

        try:
            self._init_chromadb()
            self._use_semantic = True
            info["backend"] = "chromadb"
            info["embedding_model"] = "all-MiniLM-L6-v2"
        except Exception:
            self._init_tfidf()
            self._use_semantic = False
            info["backend"] = "tfidf_keyword"

        self._initialized = True
        self._init_time_ms = round((time.time() - start) * 1000, 2)
        info["init_time_ms"] = self._init_time_ms
        return info

    # ── ChromaDB backend ──

    def _init_chromadb(self) -> None:
        import chromadb
        from chromadb.utils import embedding_functions

        ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2",
        )
        self._embedding_fn = ef

        client = chromadb.Client()
        collection = client.get_or_create_collection(
            name="fintrac_regulatory",
            embedding_function=ef,
            metadata={"hnsw:space": "cosine"},
        )

        if collection.count() == 0:
            ids = [d["id"] for d in self._documents]
            documents = [d["content"] for d in self._documents]
            metadatas = [
                {"title": d["title"], "category": d["category"], "typology": d["typology"]}
                for d in self._documents
            ]
            collection.add(ids=ids, documents=documents, metadatas=metadatas)

        self._chroma_collection = collection

    def _query_chromadb(self, query: str, top_k: int) -> list[RetrievalResult]:
        results = self._chroma_collection.query(
            query_texts=[query],
            n_results=min(top_k, self._chroma_collection.count()),
        )
        output = []
        for i, doc_id in enumerate(results["ids"][0]):
            meta = results["metadatas"][0][i]
            distance = results["distances"][0][i] if results.get("distances") else 0.5
            score = max(0.0, 1.0 - distance)
            output.append(RetrievalResult(
                doc_id=doc_id,
                title=meta.get("title", ""),
                content=results["documents"][0][i],
                category=meta.get("category", ""),
                typology=meta.get("typology", ""),
                relevance_score=round(score, 4),
                retrieval_method="semantic",
            ))
        return output

    # ── TF-IDF fallback ──

    def _init_tfidf(self) -> None:
        from sklearn.feature_extraction.text import TfidfVectorizer

        corpus = [d["content"] for d in self._documents]
        self._tfidf_vectorizer = TfidfVectorizer(
            stop_words="english",
            max_features=5000,
            ngram_range=(1, 2),
        )
        self._tfidf_matrix = self._tfidf_vectorizer.fit_transform(corpus)

    def _query_tfidf(self, query: str, top_k: int) -> list[RetrievalResult]:
        from sklearn.metrics.pairwise import cosine_similarity

        query_vec = self._tfidf_vectorizer.transform([query])
        similarities = cosine_similarity(query_vec, self._tfidf_matrix).flatten()

        ranked_indices = similarities.argsort()[::-1][:top_k]
        output = []
        for idx in ranked_indices:
            doc = self._documents[idx]
            output.append(RetrievalResult(
                doc_id=doc["id"],
                title=doc["title"],
                content=doc["content"],
                category=doc["category"],
                typology=doc["typology"],
                relevance_score=round(float(similarities[idx]), 4),
                retrieval_method="keyword",
            ))
        return output

    # ── Public API ──

    def retrieve(self, query: str, top_k: int = 3, min_score: float = 0.1) -> RAGContext:
        """Retrieve relevant regulatory documents for a query.

        Args:
            query: Natural language query or alert type.
            top_k: Maximum documents to return.
            min_score: Minimum relevance score threshold.
        """
        if not self._initialized:
            self.initialize()

        start = time.time()

        if self._use_semantic and self._chroma_collection:
            results = self._query_chromadb(query, top_k)
        else:
            results = self._query_tfidf(query, top_k)

        filtered = [r for r in results if r.relevance_score >= min_score]
        elapsed_ms = round((time.time() - start) * 1000, 2)

        self._query_count += 1
        self._total_query_ms += elapsed_ms

        token_est = sum(len(r.content.split()) for r in filtered) * 1.3

        return RAGContext(
            query=query,
            results=filtered,
            retrieval_time_ms=elapsed_ms,
            method="semantic" if self._use_semantic else "keyword",
            token_estimate=int(token_est),
        )

    def retrieve_for_alert(self, alert_type: str, additional_context: str = "") -> RAGContext:
        """Specialized retrieval for a specific alert type.

        Constructs a targeted query combining the alert type with
        additional investigation context for better retrieval.
        """
        type_queries = {
            "structuring": "FINTRAC structuring smurfing transactions below $10,000 reporting threshold",
            "rapid_movement": "rapid movement of funds layering phase money laundering deposit withdrawal",
            "crypto_layering": "cryptocurrency virtual currency privacy coins mixing tumbling laundering",
            "round_tripping": "round tripping circular transfers wash trading funds return",
            "velocity_spike": "unusual transaction volume velocity spike sudden increase frequency",
            "dormant_activation": "dormant account reactivation sudden activity after long inactivity",
            "geographic_anomaly": "geographic risk high-risk jurisdiction IP address location inconsistency",
            "third_party_pattern": "third party involvement nominee straw-man funnel account",
            "pep_sanctions_hit": "politically exposed person PEP sanctions screening enhanced due diligence",
            "age_amount_mismatch": "client profile inconsistency income occupation transaction mismatch",
        }

        query = type_queries.get(alert_type, f"FINTRAC indicators for {alert_type}")
        if additional_context:
            query += f" {additional_context}"

        return self.retrieve(query, top_k=3, min_score=0.05)

    def retrieve_str_guidance(self) -> RAGContext:
        """Retrieve STR writing guidance for report generation."""
        return self.retrieve(
            "How to write FINTRAC suspicious transaction report STR filing requirements",
            top_k=2,
            min_score=0.05,
        )

    # ── Case Precedent Store ──

    def index_completed_case(self, investigation_state: dict) -> None:
        """Add a completed investigation to the case precedent store."""
        summary = (
            f"Alert type: {investigation_state.get('alert_type', 'unknown')}. "
            f"Risk score: {investigation_state.get('risk_score', 0)}. "
            f"Action: {investigation_state.get('recommended_action', 'unknown')}. "
            f"Factors: {', '.join(investigation_state.get('risk_factors', [])[:5])}."
        )
        self._case_store.append({
            "alert_id": investigation_state.get("alert_id", ""),
            "alert_type": investigation_state.get("alert_type", ""),
            "risk_score": investigation_state.get("risk_score", 0),
            "recommended_action": investigation_state.get("recommended_action", ""),
            "risk_factors": investigation_state.get("risk_factors", []),
            "summary": summary,
        })

    def find_similar_cases(self, alert_type: str, risk_score: float, top_k: int = 3) -> list[dict]:
        """Find similar past investigations by alert type and risk proximity."""
        candidates = []
        for case in self._case_store:
            type_match = 1.0 if case["alert_type"] == alert_type else 0.3
            score_proximity = 1.0 - abs(case["risk_score"] - risk_score) / 100.0
            similarity = type_match * 0.6 + score_proximity * 0.4
            candidates.append({**case, "similarity": round(similarity, 3)})

        candidates.sort(key=lambda x: x["similarity"], reverse=True)
        return candidates[:top_k]

    # ── Stats ──

    @property
    def stats(self) -> dict[str, Any]:
        return {
            "initialized": self._initialized,
            "backend": "chromadb" if self._use_semantic else "tfidf_keyword",
            "documents_indexed": len(self._documents),
            "cases_indexed": len(self._case_store),
            "total_queries": self._query_count,
            "avg_query_ms": round(self._total_query_ms / max(self._query_count, 1), 2),
            "init_time_ms": self._init_time_ms,
        }


# Singleton
_rag_engine: RegulatoryKnowledgeRAG | None = None


def get_rag_engine() -> RegulatoryKnowledgeRAG:
    """Return the singleton RAG engine, initializing on first use."""
    global _rag_engine
    if _rag_engine is None:
        _rag_engine = RegulatoryKnowledgeRAG()
        _rag_engine.initialize()
    return _rag_engine
