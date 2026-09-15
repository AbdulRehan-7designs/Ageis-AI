"""Unified RAG service facade for AegisAI.

This module provides a single interface for:
  - Document ingestion (PDF → Qdrant)
  - Hybrid retrieval (dense + sparse + rerank + RBAC)
  - Collection health/stats reporting

All components delegate to the specialised ingestion and retrieval services.
The agent orchestrator and API endpoints should import from this module rather
than calling ingestion_service / retrieval_service directly.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.services.ingestion import ingestion_service, IngestionService
from app.services.retrieval import retrieval_service, RetrievalResult, RetrievalService

logger = logging.getLogger(__name__)


class RAGService:
    """Unified facade over the hybrid-RAG ingestion + retrieval stack."""

    def __init__(
        self,
        ingestor: IngestionService = ingestion_service,
        retriever: RetrievalService = retrieval_service,
    ) -> None:
        self._ingestor = ingestor
        self._retriever = retriever

    # ------------------------------------------------------------------
    # Ingestion
    # ------------------------------------------------------------------

    def ingest_pdf(
        self,
        pdf_path: str,
        doc_name: str,
        classification_tag: str = "INTERNAL",
        section_context: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Ingest a PDF file into Qdrant.

        Returns a stats dict:
            {
                "total_chunks": int,
                "total_tables": int,
                "upserted_ids": List[str],
            }
        """
        logger.info("RAGService.ingest_pdf: doc=%s tag=%s", doc_name, classification_tag)
        stats = self._ingestor.ingest_pdf(
            pdf_path=pdf_path,
            doc_name=doc_name,
            classification_tag=classification_tag,
            section_context=section_context,
        )
        logger.info(
            "RAGService.ingest_pdf done: %d chunks, %d tables for %s",
            stats.get("total_chunks", 0),
            stats.get("total_tables", 0),
            doc_name,
        )
        return stats

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------

    def retrieve(
        self,
        query: str,
        user_clearance: Optional[List[str]] = None,
        top_k: Optional[int] = None,
    ) -> List[RetrievalResult]:
        """Run hybrid retrieval (dense + sparse RRF + rerank + RBAC).

        Args:
            query: Natural-language search query.
            user_clearance: List of classification tags the user is allowed to
                see (e.g. ["INTERNAL", "RESTRICTED"]).  Defaults to
                [settings.CLASSIFICATION_TAG_DEFAULT].
            top_k: Max number of results to return.  Defaults to
                settings.TOP_K_RETRIEVE.

        Returns:
            Ranked list of RetrievalResult objects.
        """
        if user_clearance is None:
            user_clearance = [settings.CLASSIFICATION_TAG_DEFAULT]
        if top_k is None:
            top_k = settings.TOP_K_RETRIEVE

        logger.info(
            "RAGService.retrieve: query='%s' clearance=%s top_k=%d",
            query[:80],
            user_clearance,
            top_k,
        )
        results = self._retriever.retrieve(
            query=query,
            user_clearance=user_clearance,
            top_k=top_k,
        )
        logger.info("RAGService.retrieve: returned %d results", len(results))
        return results

    def to_citation_dicts(
        self, results: List[RetrievalResult]
    ) -> List[Dict[str, Any]]:
        """Convert RetrievalResult objects to citation dicts for the API."""
        return self._retriever.to_citation_dicts(results)

    def retrieve_and_format(
        self,
        query: str,
        user_clearance: Optional[List[str]] = None,
        top_k: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Convenience: retrieve + convert to citation dicts in one call."""
        results = self.retrieve(query=query, user_clearance=user_clearance, top_k=top_k)
        return self.to_citation_dicts(results)

    # ------------------------------------------------------------------
    # Context-building for LLM prompt
    # ------------------------------------------------------------------

    def build_rag_context(
        self,
        query: str,
        user_clearance: Optional[List[str]] = None,
        top_k: Optional[int] = None,
        max_context_chars: int = 3000,
    ) -> Dict[str, Any]:
        """Retrieve evidence and format it as an LLM-ready context block.

        Returns:
            {
                "context_text": str,   # Formatted evidence for LLM prompt
                "citations":    list,  # Citation dicts for API response
                "result_count": int,
            }
        """
        results = self.retrieve(query=query, user_clearance=user_clearance, top_k=top_k)
        citations = self.to_citation_dicts(results)

        # Build the context block injected into the LLM prompt
        context_parts: List[str] = []
        total_chars = 0
        for i, result in enumerate(results, start=1):
            excerpt = result.text[:500].strip()
            snippet = (
                f"[Source {i}] {result.doc_name} | Page {result.page} "
                f"| {result.section_title} | Tag: {result.classification_tag}\n"
                f"{excerpt}"
            )
            if total_chars + len(snippet) > max_context_chars:
                break
            context_parts.append(snippet)
            total_chars += len(snippet)

        context_text = "\n\n---\n\n".join(context_parts) if context_parts else ""

        return {
            "context_text": context_text,
            "citations": citations,
            "result_count": len(results),
        }

    # ------------------------------------------------------------------
    # Health & stats
    # ------------------------------------------------------------------

    def health(self) -> Dict[str, Any]:
        """Return Qdrant collection health info."""
        try:
            info = self._retriever.qdrant_client.get_collection(
                settings.QDRANT_COLLECTION
            )
            vectors_count = getattr(info, "vectors_count", None)
            if vectors_count is None:
                vectors_count = getattr(info, "indexed_vectors_count", 0) or getattr(info, "points_count", 0)

            return {
                "status": "ok",
                "collection": settings.QDRANT_COLLECTION,
                "vectors_count": vectors_count,
                "points_count": getattr(info, "points_count", 0),
                "error": None,
            }
        except Exception as exc:
            try:
                self._retriever.qdrant_client.get_collections()
                return {
                    "status": "ok (collection uninitialized)",
                    "collection": settings.QDRANT_COLLECTION,
                    "vectors_count": 0,
                    "points_count": 0,
                    "error": None,
                }
            except Exception as conn_exc:
                logger.warning("RAGService.health: Qdrant not reachable — %s", conn_exc)
                return {
                    "status": "error",
                    "collection": settings.QDRANT_COLLECTION,
                    "vectors_count": 0,
                    "points_count": 0,
                    "error": str(conn_exc),
                }

    def collection_stats(self) -> Dict[str, Any]:
        """Alias for health() — included for backward compatibility."""
        return self.health()


# Singleton — used by agent_orchestrator and API endpoints
rag_service = RAGService()
