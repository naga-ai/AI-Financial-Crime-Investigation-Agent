"""PII masking and tokenization for financial data pipelines.

Implements field-level data classification and deterministic tokenization
following the Capital One pattern: data is masked before entering any AI
pipeline (LLM prompts, RAG, cache) and only detokenized at the final
render layer with audit logging.
"""

from __future__ import annotations

import enum
import hashlib
import hmac
import re
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


class PIIClassification(str, enum.Enum):
    RESTRICTED = "restricted"
    CONFIDENTIAL = "confidential"
    INTERNAL = "internal"
    PUBLIC = "public"


FIELD_CLASSIFICATIONS: dict[str, PIIClassification] = {
    "sin": PIIClassification.RESTRICTED,
    "social_insurance_number": PIIClassification.RESTRICTED,
    "account_number": PIIClassification.RESTRICTED,
    "bank_account": PIIClassification.RESTRICTED,
    "credit_card": PIIClassification.RESTRICTED,

    "name": PIIClassification.CONFIDENTIAL,
    "first_name": PIIClassification.CONFIDENTIAL,
    "last_name": PIIClassification.CONFIDENTIAL,
    "full_name": PIIClassification.CONFIDENTIAL,
    "client_name": PIIClassification.CONFIDENTIAL,
    "email": PIIClassification.CONFIDENTIAL,
    "phone": PIIClassification.CONFIDENTIAL,
    "phone_number": PIIClassification.CONFIDENTIAL,
    "address": PIIClassification.CONFIDENTIAL,
    "date_of_birth": PIIClassification.CONFIDENTIAL,
    "dob": PIIClassification.CONFIDENTIAL,
    "ip_address": PIIClassification.CONFIDENTIAL,

    "amount": PIIClassification.INTERNAL,
    "balance": PIIClassification.INTERNAL,
    "transaction_amount": PIIClassification.INTERNAL,
    "risk_score": PIIClassification.INTERNAL,
    "salary": PIIClassification.INTERNAL,

    "ticker": PIIClassification.PUBLIC,
    "market_data": PIIClassification.PUBLIC,
    "exchange_rate": PIIClassification.PUBLIC,
    "interest_rate": PIIClassification.PUBLIC,
}


@dataclass
class PIIAuditEntry:
    timestamp: str
    operation: str  # "tokenize" | "detokenize"
    field_name: str
    classification: str
    purpose: str
    component: str
    token_preview: str


@dataclass
class PIIMasker:
    """Deterministic PII tokenization with format preservation and audit logging."""

    _secret: str = field(default_factory=lambda: uuid.uuid4().hex)
    _token_store: dict[str, str] = field(default_factory=dict)
    _reverse_store: dict[str, str] = field(default_factory=dict)
    _audit_log: list[PIIAuditEntry] = field(default_factory=list)

    def classify_field(self, field_name: str) -> PIIClassification:
        normalized = field_name.lower().strip()
        if normalized in FIELD_CLASSIFICATIONS:
            return FIELD_CLASSIFICATIONS[normalized]
        for key, classification in FIELD_CLASSIFICATIONS.items():
            if key in normalized or normalized in key:
                return classification
        return PIIClassification.PUBLIC

    def tokenize(
        self,
        value: str,
        field_name: str,
        purpose: str = "pipeline",
        component: str = "unknown",
    ) -> str:
        if not value:
            return value

        classification = self.classify_field(field_name)
        if classification == PIIClassification.PUBLIC:
            return value

        token = self._deterministic_token(value, field_name)

        self._token_store[token] = value
        self._reverse_store[value] = token

        self._audit_log.append(PIIAuditEntry(
            timestamp=datetime.utcnow().isoformat(),
            operation="tokenize",
            field_name=field_name,
            classification=classification.value,
            purpose=purpose,
            component=component,
            token_preview=token[:16] + "...",
        ))

        return token

    def detokenize(
        self,
        token: str,
        purpose: str = "dashboard_render",
        component: str = "dashboard",
    ) -> str:
        original = self._token_store.get(token)
        if original is None:
            return token

        self._audit_log.append(PIIAuditEntry(
            timestamp=datetime.utcnow().isoformat(),
            operation="detokenize",
            field_name="unknown",
            classification="unknown",
            purpose=purpose,
            component=component,
            token_preview=token[:16] + "...",
        ))

        return original

    def mask_record(
        self,
        record: dict[str, Any],
        purpose: str = "pipeline",
        component: str = "unknown",
    ) -> dict[str, Any]:
        masked = {}
        for key, value in record.items():
            if isinstance(value, str):
                classification = self.classify_field(key)
                if classification in (PIIClassification.RESTRICTED, PIIClassification.CONFIDENTIAL):
                    masked[key] = self.tokenize(value, key, purpose, component)
                else:
                    masked[key] = value
            elif isinstance(value, dict):
                masked[key] = self.mask_record(value, purpose, component)
            else:
                masked[key] = value
        return masked

    def unmask_record(
        self,
        record: dict[str, Any],
        purpose: str = "dashboard_render",
        component: str = "dashboard",
    ) -> dict[str, Any]:
        unmasked = {}
        for key, value in record.items():
            if isinstance(value, str) and value.startswith("PII-"):
                unmasked[key] = self.detokenize(value, purpose, component)
            elif isinstance(value, dict):
                unmasked[key] = self.unmask_record(value, purpose, component)
            else:
                unmasked[key] = value
        return unmasked

    def mask_for_llm(self, text: str, component: str = "llm") -> str:
        masked = text
        for original, token in self._reverse_store.items():
            if original in masked:
                masked = masked.replace(original, token)
        masked = self._mask_sin_patterns(masked)
        masked = self._mask_email_patterns(masked)
        masked = self._mask_phone_patterns(masked)
        return masked

    def _deterministic_token(self, value: str, field_name: str) -> str:
        h = hmac.new(
            self._secret.encode(),
            f"{field_name}:{value}".encode(),
            hashlib.sha256,
        ).hexdigest()[:12]
        return f"PII-{h}"

    def _mask_sin_patterns(self, text: str) -> str:
        return re.sub(r'\b\d{3}[-\s]?\d{3}[-\s]?\d{3}\b', '[SIN-REDACTED]', text)

    def _mask_email_patterns(self, text: str) -> str:
        return re.sub(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            '[EMAIL-REDACTED]',
            text,
        )

    def _mask_phone_patterns(self, text: str) -> str:
        return re.sub(
            r'\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b',
            '[PHONE-REDACTED]',
            text,
        )

    @property
    def audit_log(self) -> list[dict[str, str]]:
        return [
            {
                "timestamp": e.timestamp,
                "operation": e.operation,
                "field_name": e.field_name,
                "classification": e.classification,
                "purpose": e.purpose,
                "component": e.component,
                "token_preview": e.token_preview,
            }
            for e in self._audit_log
        ]

    @property
    def stats(self) -> dict[str, Any]:
        tokenize_ops = sum(1 for e in self._audit_log if e.operation == "tokenize")
        detokenize_ops = sum(1 for e in self._audit_log if e.operation == "detokenize")
        by_classification: dict[str, int] = {}
        for e in self._audit_log:
            by_classification[e.classification] = by_classification.get(e.classification, 0) + 1
        return {
            "total_operations": len(self._audit_log),
            "tokenize_operations": tokenize_ops,
            "detokenize_operations": detokenize_ops,
            "unique_tokens": len(self._token_store),
            "by_classification": by_classification,
        }


pii_masker = PIIMasker()
