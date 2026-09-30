"""Intent routing for an engineering evidence-first RAG system."""

from __future__ import annotations

import re
from typing import Any, Dict, List

from app.services.identifiers import expand_identifier_query, extract_identifiers

_STOPWORDS = {
    "the",
    "a",
    "an",
    "is",
    "are",
    "where",
    "what",
    "when",
    "which",
    "how",
    "to",
    "of",
    "on",
    "in",
    "for",
    "and",
    "or",
    "with",
    "from",
    "does",
    "did",
    "this",
    "that",
    "these",
    "those",
}


class QueryRouter:
    """Classify user intent and expand identifier-heavy queries."""

    def route(self, query: str) -> Dict[str, Any]:
        text = (query or "").strip()
        lowered = text.lower()
        identifiers = extract_identifiers(text)

        if not text:
            return {
                "intent": "unknown",
                "strategy": "semantic",
                "identifiers": [],
                "expanded_query": "",
                "keywords": [],
            }

        keywords = [
            token
            for token in re.findall(r"[A-Za-z][A-Za-z0-9-]{1,}", text)
            if token.lower() not in _STOPWORDS
        ]

        drawing_terms = ("p&id", "pid", "drawing", "sheet", "isometric", "connected", "connection", "line list")
        maintenance_terms = ("maintenance", "inspection", "repair", "preventive", "vibration", "failure", "breakdown", "limit", "threshold")
        if any(token in lowered for token in drawing_terms):
            intent = "drawing"
            strategy = "identifier" if identifiers else "semantic"
        elif any(token in lowered for token in maintenance_terms):
            intent = "maintenance"
            strategy = "identifier" if identifiers else "semantic"
        elif identifiers or any(token in lowered for token in ("tag", "equipment", "asset", "everything related")):
            intent = "asset_lookup"
            strategy = "identifier"
        elif any(token in lowered for token in ("compare", "difference", "between", "delta")):
            intent = "compare"
            strategy = "semantic"
        else:
            intent = "semantic"
            strategy = "semantic"

        return {
            "intent": intent,
            "strategy": strategy,
            "identifiers": identifiers,
            "asset": identifiers[0] if identifiers else None,
            "related_identifiers": identifiers[1:],
            "search_strategy": "exact_identifier_plus_semantic" if identifiers else "semantic",
            "expanded_query": expand_identifier_query(text),
            "keywords": keywords,
        }


query_router = QueryRouter()
__all__ = ["QueryRouter", "query_router"]
