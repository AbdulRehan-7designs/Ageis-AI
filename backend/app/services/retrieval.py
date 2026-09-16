"""Hybrid retrieval pipeline for the industrial RAG stack.

This module performs dense + sparse retrieval from Qdrant, fuses the candidates
with Reciprocal Rank Fusion (RRF), reranks top candidates, and returns citation-friendly payloads.
"""

import logging
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from fastembed import TextEmbedding
try:
    from fastembed import TextCrossEncoder
except ImportError:
    TextCrossEncoder = None

from qdrant_client import QdrantClient
from qdrant_client.models import FieldCondition, Filter, MatchAny, SparseVector

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class RetrievalResult:
    chunk_id: str
    doc_name: str
    page: int
    section_title: str
    classification_tag: str
    text: str
    rerank_score: Optional[float] = None


class RetrievalService:
    """Dense + sparse retrieval with RRF fusion and reranking."""

    DENSE_MODEL = settings.DENSE_EMBEDDING_MODEL
    SPARSE_MODEL = settings.SPARSE_EMBEDDING_MODEL
    RERANKER_MODEL = settings.RERANKER_MODEL
    COLLECTION_NAME = settings.QDRANT_COLLECTION
    TOP_K_PREFETCH = settings.TOP_K_PREFETCH
    TOP_K_FINAL = settings.TOP_K_RETRIEVE

    def __init__(self) -> None:
        self.qdrant_client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT, check_compatibility=False)
        self.dense_embedder = None
        self.sparse_embedder = None
        self.reranker = None

    def _load_supported_dense_model(self):
        try:
            model = TextEmbedding(model_name=self.DENSE_MODEL)
            return model
        except Exception as exc:
            logger.warning("Failed to initialize dense embedder '%s': %s", self.DENSE_MODEL, exc)
            return None

    def _ensure_ready(self) -> bool:
        if self.dense_embedder is None:
            dense_model = self._load_supported_dense_model()
            if dense_model is None:
                logger.warning("Dense embedding model could not be initialized.")
                return False
            self.dense_embedder = dense_model

        if self.reranker is None and TextCrossEncoder is not None:
            try:
                self.reranker = TextCrossEncoder(model_name=self.RERANKER_MODEL)
            except Exception as exc:
                logger.warning("Reranker model could not be initialized: %s", exc)
                self.reranker = None

        return self.dense_embedder is not None

    def retrieve(
        self,
        query: str,
        user_clearance: Optional[List[str]] = None,
        top_k: Optional[int] = None,
    ) -> List[RetrievalResult]:
        if top_k is None:
            top_k = self.TOP_K_FINAL
        if user_clearance is None:
            user_clearance = ["INTERNAL"]

        logger.info("Retrieving docs for query: '%s'", query)
        logger.info("User clearance: %s", user_clearance)

        if not self._ensure_ready():
            logger.warning("Dense embedding model is unavailable; returning no results.")
            return []

        query_dense = self._embed_query_dense(query)
        query_sparse = self._embed_query_sparse(query)

        rbac_filter = Filter(
            must=[
                FieldCondition(
                    key="classification_tag",
                    match=MatchAny(any=user_clearance),
                )
            ]
        )

        dense_hits = self._search_qdrant(query_dense, rbac_filter, self.TOP_K_PREFETCH, vector_name="dense")
        sparse_hits = self._search_qdrant(query_sparse, rbac_filter, self.TOP_K_PREFETCH, vector_name="sparse") if query_sparse else []

        candidates = self._rrf_fusion(dense_hits, sparse_hits)
        reranked = self._rerank_results(candidates, query)
        return reranked[:top_k]

    def _embed_query_dense(self, query: str) -> List[float]:
        embeddings = list(self.dense_embedder.embed([query]))
        return embeddings[0].tolist()

    def _embed_query_sparse(self, query: str) -> Optional[Dict[str, Any]]:
        return None

    def _rrf_fusion(
        self,
        dense_hits: List[Dict[str, Any]],
        sparse_hits: List[Dict[str, Any]],
    ) -> List[RetrievalResult]:
        candidate_scores: Dict[str, float] = defaultdict(float)
        candidates: Dict[str, RetrievalResult] = {}

        for rank, item in enumerate(dense_hits, start=1):
            score = 1.0 / (60 + rank)
            candidate_scores[item["chunk_id"]] += score
            candidates[item["chunk_id"]] = item["result"]

        for rank, item in enumerate(sparse_hits, start=1):
            score = 1.0 / (60 + rank)
            candidate_scores[item["chunk_id"]] += score
            candidates[item["chunk_id"]] = item["result"]

        merged = sorted(candidates.items(), key=lambda item: candidate_scores[item[0]], reverse=True)
        return [result for _, result in merged[: self.TOP_K_PREFETCH]]

    def _search_qdrant(
        self,
        query_vector: Any,
        query_filter: Filter,
        limit: int,
        vector_name: str = "dense",
    ) -> List[Dict[str, Any]]:
        try:
            query = query_vector
            if isinstance(query_vector, dict) and "indices" in query_vector:
                query = SparseVector(indices=query_vector["indices"], values=query_vector["values"])

            response = self.qdrant_client.query_points(
                collection_name=self.COLLECTION_NAME,
                query=query,
                using=vector_name,
                query_filter=query_filter,
                limit=limit,
                with_payload=True,
                with_vectors=False,
            )
            hits = response.points
        except Exception as exc:
            logger.warning("Qdrant query_points failed for vector '%s': %s", vector_name, exc)
            return []

        results: List[Dict[str, Any]] = []
        for hit in hits:
            payload = hit.payload or {}
            result = RetrievalResult(
                chunk_id=str(payload.get("chunk_id", "unknown")),
                doc_name=str(payload.get("doc_name", "")),
                page=int(payload.get("page", 0) or 0),
                section_title=str(payload.get("section_title", "")),
                classification_tag=str(payload.get("classification_tag", "INTERNAL")),
                text=str(payload.get("text", "")),
            )
            results.append({"chunk_id": result.chunk_id, "result": result})
        return results

    def _rerank_results(self, results: List[RetrievalResult], query: str) -> List[RetrievalResult]:
        if not results:
            return []
        if self.reranker is None:
            logger.info("Reranker unavailable; keeping results in RRF order.")
            return results

        try:
            documents = [result.text for result in results]
            scores = list(self.reranker.rerank(query, documents))
            for result, score in zip(results, scores):
                result.rerank_score = float(score)
            return sorted(results, key=lambda item: item.rerank_score or 0.0, reverse=True)
        except Exception as exc:
            logger.warning("Rerank failed: %s", exc)
            return results

    def to_citation_dicts(self, results: List[RetrievalResult]) -> List[Dict[str, Any]]:
        citations: List[Dict[str, Any]] = []
        for result in results:
            citations.append(
                {
                    "document": result.doc_name,
                    "page": result.page,
                    "section_title": result.section_title or "General",
                    "tag": result.classification_tag,
                    "snippet": result.text[:500],
                }
            )
        return citations


retrieval_service = RetrievalService()
