"""Hybrid retrieval service for the AegisAI knowledge base."""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional, Sequence

from fastembed import TextEmbedding
try:
    from fastembed import SparseTextEmbedding
except ImportError:
    SparseTextEmbedding = None
try:
    from fastembed.rerank.cross_encoder import TextCrossEncoder
except ImportError:
    try:
        from fastembed import TextCrossEncoder
    except ImportError:
        TextCrossEncoder = None
from qdrant_client import QdrantClient

from app.core.config import settings
from app.services.ingestion import ingestion_service
from app.services.identifiers import extract_identifiers
from app.services.query_router import query_router
from app.services.retrieval import RetrievalResult, RetrievalService

logger = logging.getLogger(__name__)


class RAGService:
    """Minimal hybrid retrieval layer that serves the app contracts."""

    def __init__(self) -> None:
        self.collection = settings.QDRANT_COLLECTION
        self.client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT, check_compatibility=False)
        self.retrieval = RetrievalService()
        self._embedder: Optional[TextEmbedding] = None
        self._sparse_embedder = None
        self._reranker = None

    def _get_embedder(self) -> Optional[TextEmbedding]:
        if self._embedder is not None:
            return self._embedder
        try:
            self._embedder = TextEmbedding(model_name=settings.DENSE_EMBEDDING_MODEL)
            return self._embedder
        except Exception as exc:  # pragma: no cover - environment dependent
            logger.warning("Dense embedder unavailable: %s", exc)
            return None

    def _get_sparse_embedder(self):
        """Lazy-load the BM25 sparse embedding model."""
        if self._sparse_embedder is not None:
            return self._sparse_embedder
        if SparseTextEmbedding is None:
            return None
        try:
            self._sparse_embedder = SparseTextEmbedding(model_name=settings.SPARSE_EMBEDDING_MODEL)
            logger.info("Sparse embedder loaded: %s", settings.SPARSE_EMBEDDING_MODEL)
            return self._sparse_embedder
        except Exception as exc:
            logger.warning("Sparse embedder unavailable (hybrid search disabled): %s", exc)
            return None

    def _get_reranker(self):
        """Lazy-load the cross-encoder reranker model."""
        if self._reranker is not None:
            return self._reranker
        if TextCrossEncoder is None:
            return None
        try:
            self._reranker = TextCrossEncoder(model_name=settings.RERANKER_MODEL)
            logger.info("Reranker loaded: %s", settings.RERANKER_MODEL)
            return self._reranker
        except Exception as exc:
            logger.warning("Reranker unavailable (returning fused order): %s", exc)
            return None

    def _hits_to_results(self, hits: List[Any]) -> List[RetrievalResult]:
        """Convert raw Qdrant hits to RetrievalResult objects."""
        results: List[RetrievalResult] = []
        for hit in hits or []:
            payload = getattr(hit, "payload", {}) or {}
            if hasattr(hit, "score"):
                score = float(getattr(hit, "score", 0.0) or 0.0)
            elif isinstance(hit, dict):
                score = float(hit.get("score", 0.0) or 0.0)
            else:
                score = 0.0
            results.append(
                RetrievalResult(
                    chunk_id=str(payload.get("chunk_id", getattr(hit, "id", ""))),
                    doc_name=str(payload.get("doc_name", "unknown.pdf")),
                    page=int(payload.get("page", 1) or 1),
                    section_title=str(payload.get("section_title", "Introduction")),
                    classification_tag=str(payload.get("classification_tag", settings.CLASSIFICATION_TAG_DEFAULT)),
                    text=str(payload.get("text", "")),
                    stored_filename=payload.get("stored_filename"),
                    bbox=payload.get("bbox"),
                    page_width=payload.get("page_width"),
                    page_height=payload.get("page_height"),
                    score=score,
                    metadata=dict(payload),
                )
            )
        return results

    def _query_sparse_collection(
        self, *, sparse_vector: Any, allowed_tags: set, top_k: int,
    ) -> List[Any]:
        """Query Qdrant using the sparse (BM25) named vector."""
        from qdrant_client.models import SparseVector as QdrantSparseVector

        # Normalise sparse vector to Qdrant's SparseVector model
        if hasattr(sparse_vector, "indices") and hasattr(sparse_vector, "values"):
            sv = QdrantSparseVector(
                indices=[int(i) for i in sparse_vector.indices],
                values=[float(v) for v in sparse_vector.values],
            )
        elif isinstance(sparse_vector, dict):
            sv = QdrantSparseVector(
                indices=[int(i) for i in sparse_vector.get("indices", [])],
                values=[float(v) for v in sparse_vector.get("values", [])],
            )
        else:
            sv = sparse_vector

        search_kwargs: Dict[str, Any] = {
            "collection_name": self.collection,
            "limit": max(1, int(top_k)),
            "with_payload": True,
            "with_vectors": False,
        }
        if allowed_tags:
            search_kwargs["query_filter"] = {
                "must": [{"key": "classification_tag", "match": {"any": sorted(allowed_tags)}}]
            }

        # Prefer newer query_points API, fall back to search()
        try:
            if hasattr(self.client, "query_points"):
                search_kwargs["query"] = sv
                search_kwargs["using"] = "sparse"
                response = self.client.query_points(**search_kwargs)
                if hasattr(response, "points"):
                    return list(response.points or [])
                return list(response or [])
            else:
                from qdrant_client.models import NamedSparseVector
                search_kwargs["query_vector"] = NamedSparseVector(name="sparse", vector=sv)
                return list(self.client.search(**search_kwargs) or [])
        except Exception as exc:
            logger.warning("Sparse vector search failed: %s", exc)
            return []

    def _rerank_results(
        self, query: str, results: List[RetrievalResult], top_k: int,
    ) -> List[RetrievalResult]:
        """Apply cross-encoder reranking to improve precision."""
        reranker = self._get_reranker()
        if reranker is None or not results:
            return results[:top_k]

        documents = [r.text for r in results if r.text and r.text.strip()]
        if not documents:
            return results[:top_k]

        try:
            reranked = list(reranker.rerank(query, documents, top_k=min(top_k, len(documents))))
            reranked_results: List[RetrievalResult] = []
            for item in reranked:
                # fastembed may use .doc_index, .index, or dict key
                idx = getattr(item, "doc_index", None)
                if idx is None:
                    idx = getattr(item, "index", None)
                if idx is None and isinstance(item, dict):
                    idx = item.get("doc_index", item.get("index", 0))
                if idx is None:
                    continue
                score = getattr(item, "score", None)
                if score is None and isinstance(item, dict):
                    score = item.get("score", 0.0)
                if 0 <= idx < len(results):
                    result = results[idx]
                    result.rerank_score = float(score or 0.0)
                    reranked_results.append(result)
            return reranked_results if reranked_results else results[:top_k]
        except Exception as exc:
            logger.warning("Reranking failed, returning fused order: %s", exc)
            return results[:top_k]

    def _normalize_clearance(self, clearance_tags: Optional[Sequence[str]]) -> set[str]:
        tags = clearance_tags or [settings.CLASSIFICATION_TAG_DEFAULT]
        normalized = {str(tag).upper() for tag in tags if str(tag).strip()}
        return normalized or {settings.CLASSIFICATION_TAG_DEFAULT.upper()}

    def _coerce_embedding_vector(self, embedding_output: Any) -> List[float]:
        def flatten(value: Any) -> Optional[List[float]]:
            if value is None:
                return None
            if hasattr(value, "tolist"):
                value = value.tolist()

            if isinstance(value, (int, float)):
                return [float(value)]

            if isinstance(value, (list, tuple)):
                if not value:
                    return None
                if all(isinstance(item, (int, float)) for item in value):
                    return [float(item) for item in value]
                for item in value:
                    flattened = flatten(item)
                    if flattened is not None:
                        return flattened
                return None

            if isinstance(value, str):
                return None

            try:
                iterator = list(value)
            except TypeError:
                return None

            if not iterator:
                return None
            if all(isinstance(item, (int, float)) for item in iterator):
                return [float(item) for item in iterator]
            for item in iterator:
                flattened = flatten(item)
                if flattened is not None:
                    return flattened
            return None

        flattened = flatten(embedding_output)
        if flattened is None:
            raise TypeError(f"Unsupported embedding vector type: {type(embedding_output).__name__}")
        return flattened

    def _query_vector_collection(self, *, vector: Sequence[float], allowed_tags: set[str], top_k: int) -> List[Any]:
        """Compatibility wrapper for Qdrant's old and new client search APIs."""
        search_kwargs: Dict[str, Any] = {
            "collection_name": self.collection,
            "limit": max(1, int(top_k)),
            "with_payload": True,
            "with_vectors": False,
        }
        if allowed_tags:
            search_kwargs["query_filter"] = {
                "must": [{"key": "classification_tag", "match": {"any": sorted(allowed_tags)}}]
            }

        if hasattr(self.client, "search"):
            search_kwargs["query_vector"] = list(vector)
            return list(self.client.search(**search_kwargs) or [])

        search_kwargs["query"] = list(vector)
        search_kwargs["using"] = "dense"
        response = self.client.query_points(**search_kwargs)
        if hasattr(response, "points"):
            return list(response.points or [])
        return list(response or [])

    def _memory_search(self, query_text: str, allowed_tags: set[str], top_k: int) -> List[RetrievalResult]:
        tokens = {token.lower() for token in re.findall(r"[A-Za-z0-9]+", query_text or "") if token}
        scored: List[tuple[int, RetrievalResult]] = []
        for payload in getattr(ingestion_service, "_memory_chunks", []) or []:
            tag = str(payload.get("classification_tag") or settings.CLASSIFICATION_TAG_DEFAULT).upper()
            if allowed_tags and tag not in allowed_tags:
                continue
            text = str(payload.get("text", ""))
            doc_name = str(payload.get("doc_name", ""))
            haystack = f"{doc_name} {text}".lower()
            score = sum(1 for token in tokens if token in haystack)
            if not tokens or score > 0:
                scored.append(
                    (
                        score,
                        RetrievalResult(
                            chunk_id=str(payload.get("chunk_id", "")),
                            doc_name=doc_name,
                            page=int(payload.get("page", 1) or 1),
                            section_title=str(payload.get("section_title", "Introduction")),
                            classification_tag=tag,
                            text=text,
                            stored_filename=payload.get("stored_filename"),
                            bbox=payload.get("bbox"),
                            page_width=payload.get("page_width"),
                            page_height=payload.get("page_height"),
                            score=float(score),
                            metadata=dict(payload),
                        ),
                    )
                )
        scored.sort(key=lambda item: item[0], reverse=True)
        return [result for _, result in scored[:max(1, int(top_k))]]

    def health(self) -> Dict[str, Any]:
        try:
            info = self.client.get_collection(self.collection)
            points_count = getattr(info, "points_count", 0) or 0
            vectors = getattr(info, "vectors_count", None)
            return {
                "status": "online",
                "collection": self.collection,
                "points_count": int(points_count),
                "vectors_count": int(vectors) if vectors is not None else 0,
            }
        except Exception as exc:  # pragma: no cover - environment dependent
            logger.warning("Qdrant health check failed: %s", exc)
            if getattr(ingestion_service, "_memory_chunks", None):
                return {
                    "status": "memory-fallback",
                    "collection": self.collection,
                    "points_count": len(ingestion_service._memory_chunks),
                    "vectors_count": len(ingestion_service._memory_chunks),
                }
            return {
                "status": "offline",
                "collection": self.collection,
                "points_count": 0,
                "vectors_count": 0,
            }

    def build_rag_context(
        self,
        query: str,
        user_clearance: Optional[Sequence[str]] = None,
        top_k: int = 5,
    ) -> Dict[str, Any]:
        route = query_router.route(query or "")
        query_text = route.get("expanded_query") or (query or "").strip()
        allowed_tags = self._normalize_clearance(user_clearance)
        retrieval_trace = [
            {
                "stage": "query_classified",
                "status": "completed",
                "detail": f"Intent '{route.get('intent', 'unknown')}' using {route.get('search_strategy', 'semantic')} search.",
            },
            {
                "stage": "identifier_expansion",
                "status": "completed",
                "detail": f"Detected {len(route.get('identifiers', []))} identifier(s); expanded query variants were {'used' if route.get('identifiers') else 'not required'}.",
            },
        ]
        if not query_text:
            return {
                "citations": [],
                "context_text": "",
                "result_count": 0,
                "query_route": route,
                "retrieval_trace": retrieval_trace,
            }

        # ----------------------------------------------------------------
        # Hybrid retrieval: Dense + Sparse (BM25) → RRF Fusion → Rerank
        # ----------------------------------------------------------------
        prefetch_k = getattr(settings, "TOP_K_PREFETCH", 20)
        results: List[RetrievalResult] = []
        try:
            # --- Lane 1: Dense semantic search ---
            embedder = self._get_embedder()
            if embedder is None:
                raise RuntimeError("Dense embedding model unavailable")

            embedding_output = embedder.embed([query_text])
            vector = self._coerce_embedding_vector(embedding_output)
            dense_hits = self._query_vector_collection(
                vector=vector, allowed_tags=allowed_tags, top_k=prefetch_k,
            )
            dense_results = self._hits_to_results(dense_hits)
            retrieval_trace.append({
                "stage": "dense_vector_search",
                "status": "completed",
                "detail": f"Dense lane retrieved {len(dense_results)} result(s).",
            })

            # --- Lane 2: Sparse BM25 keyword search ---
            sparse_results: List[RetrievalResult] = []
            sparse_embedder = self._get_sparse_embedder()
            if sparse_embedder is not None:
                try:
                    sparse_output = list(sparse_embedder.embed([query_text]))
                    if sparse_output:
                        sparse_hits = self._query_sparse_collection(
                            sparse_vector=sparse_output[0],
                            allowed_tags=allowed_tags,
                            top_k=prefetch_k,
                        )
                        sparse_results = self._hits_to_results(sparse_hits)
                        retrieval_trace.append({
                            "stage": "sparse_bm25_search",
                            "status": "completed",
                            "detail": f"Sparse BM25 lane retrieved {len(sparse_results)} result(s).",
                        })
                except Exception as sparse_exc:
                    logger.warning("Sparse search failed, continuing with dense only: %s", sparse_exc)
                    retrieval_trace.append({
                        "stage": "sparse_bm25_search",
                        "status": "skipped",
                        "detail": f"Sparse search unavailable: {sparse_exc}",
                    })
            else:
                retrieval_trace.append({
                    "stage": "sparse_bm25_search",
                    "status": "skipped",
                    "detail": "Sparse embedding model not available; single-lane dense retrieval.",
                })

            # --- Reciprocal Rank Fusion (RRF) ---
            if sparse_results:
                results = self.retrieval._rrf_fusion(dense_results, sparse_results)
                retrieval_trace.append({
                    "stage": "rrf_fusion",
                    "status": "completed",
                    "detail": (
                        f"Fused {len(dense_results)} dense + {len(sparse_results)} sparse "
                        f"→ {len(results)} unique result(s) via Reciprocal Rank Fusion."
                    ),
                })
            else:
                results = dense_results
                retrieval_trace.append({
                    "stage": "rrf_fusion",
                    "status": "skipped",
                    "detail": "Single-lane retrieval (dense only); fusion not required.",
                })

            # --- Cross-encoder reranking ---
            pre_rerank_count = len(results)
            results = self._rerank_results(query_text, results, top_k)
            reranker_available = self._reranker is not None
            retrieval_trace.append({
                "stage": "cross_encoder_rerank",
                "status": "completed" if reranker_available else "skipped",
                "detail": (
                    f"Reranked {pre_rerank_count} → top {len(results)} using {settings.RERANKER_MODEL}."
                    if reranker_available
                    else "Reranker model not available; returning fusion-ranked order."
                ),
            })

        except Exception as exc:  # pragma: no cover - environment dependent
            logger.warning("Retrieval failed for query '%s'; falling back to in-memory lexical matching: %s", query_text, exc)
            results = self._memory_search(query_text, allowed_tags, top_k)
            retrieval_trace.append({
                "stage": "memory_lexical_fallback",
                "status": "completed",
                "detail": f"Vector search unavailable; matched {len(results)} local indexed chunk(s).",
            })

        if not results:
            results = self._memory_search(query_text, allowed_tags, top_k)
            if not any(item["stage"] == "memory_lexical_fallback" for item in retrieval_trace):
                retrieval_trace.append({
                    "stage": "memory_lexical_fallback",
                    "status": "completed",
                    "detail": f"No vector results; matched {len(results)} local indexed chunk(s).",
                })

        query_identifiers = {item.upper() for item in route.get("identifiers", [])}
        citations = self.retrieval.to_citation_dicts(results)
        for citation in citations:
            result_tags = {
                str(item.get("tag") if isinstance(item, dict) else item).upper()
                for item in citation.get("engineering_tags", [])
            }
            text_tags = {item.upper() for item in extract_identifiers(str(citation.get("snippet") or ""))}
            if query_identifiers and query_identifiers.intersection(result_tags | text_tags):
                citation["retrieval_reason"] = "TAG_MATCH"
            elif citation.get("source_type") == "OCR":
                citation["retrieval_reason"] = "OCR_MATCH"
            elif citation.get("document_name") and str(citation["document_name"]).casefold() in query_text.casefold():
                citation["retrieval_reason"] = "DOCUMENT_MATCH"
        retrieval_trace.append({
            "stage": "citation_normalization",
            "status": "completed",
            "detail": f"Normalized {len(citations)} result(s) with page/sheet and asset metadata.",
        })
        filtered: List[Dict[str, Any]] = []
        for citation in citations:
            tag = str(citation.get("tag") or citation.get("classification_tag") or settings.CLASSIFICATION_TAG_DEFAULT).upper()
            if tag in allowed_tags:
                citation.setdefault("tag", tag)
                citation.setdefault("classification_tag", tag)
                filtered.append(citation)

        context_chunks: List[str] = []
        evidence_groups: Dict[str, Dict[str, Any]] = {}
        for citation in filtered:
            doc_name = citation.get("document_name") or "document"
            page_no = citation.get("page") or 1
            text = citation.get("snippet") or citation.get("document_name") or ""
            context_chunks.append(
                f"- {doc_name} (p.{page_no}, {citation.get('source_type', 'TEXT')}, "
                f"{citation.get('extraction_method', 'unknown')}, "
                f"reason={citation.get('retrieval_reason', 'not established')}): {text[:400]}"
            )
            tags = route.get("identifiers", []) or [
                item.get("tag") if isinstance(item, dict) else item
                for item in citation.get("engineering_tags", [])
            ]
            if tags:
                asset_tag = str(tags[0]).upper()
                group = evidence_groups.setdefault(asset_tag, {"asset_tag": asset_tag, "sources": []})
                group["sources"].append({
                    "document_id": citation.get("document_id"),
                    "document_name": doc_name,
                    "document_type": citation.get("source_type") or citation.get("document_type"),
                    "page": page_no,
                    "evidence_type": "OCR_EXTRACTED" if citation.get("source_type") == "OCR" else "TEXT_EXTRACTED",
                    "extraction_method": citation.get("extraction_method"),
                    "classification": citation.get("classification_tag"),
                    "retrieval_reason": citation.get("retrieval_reason"),
                })

        return {
            "citations": filtered,
            "context_text": "\n".join(context_chunks),
            "evidence_groups": list(evidence_groups.values()),
            "evidence_hierarchy": ["HUMAN_VERIFIED", "AUTHORITATIVE_DOCUMENT", "OCR_EXTRACTED", "TEXT_EXTRACTED", "VISION_INFERRED", "AI_INFERENCE"],
            "result_count": len(filtered),
            "query_route": route,
            "retrieval_trace": retrieval_trace + [{
                "stage": "clearance_filter",
                "status": "completed",
                "detail": f"Retained {len(filtered)} citation(s) for clearance {', '.join(sorted(allowed_tags))}.",
            }],
        }


rag_service = RAGService()
__all__ = ["RAGService", "rag_service"]
