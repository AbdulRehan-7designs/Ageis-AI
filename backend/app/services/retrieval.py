"""Hybrid retrieval + citation normalization for engineering evidence."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Sequence

from app.services.identifiers import extract_identifiers


@dataclass
class RetrievalResult:
    chunk_id: str
    doc_name: str
    page: int
    section_title: str
    classification_tag: str
    text: str
    stored_filename: Optional[str] = None
    bbox: Optional[List[float]] = None
    page_width: Optional[int] = None
    page_height: Optional[int] = None
    score: float = 0.0
    rerank_score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class RetrievalService:
    """Thin utility service that fuses retrieval lanes and normalizes citations."""

    @staticmethod
    def _extract_object_tag(text: str) -> str:
        identifiers = extract_identifiers(text or "")
        if not identifiers:
            match = re.search(r"\b[A-Z]{1,8}-?\d{2,6}[A-Z0-9]*\b", text or "")
            if match:
                return match.group(0)
            return ""
        return identifiers[0]

    @staticmethod
    def _is_drawing_document(doc_name: str, text: str = "") -> bool:
        name_lowered = (doc_name or "").lower()
        text_lowered = (text or "").lower()
        name_markers = ("pid", "p&id", "pandid", "isometric", "line_list", "line-list")
        text_markers = ("process and instrumentation", "isometric drawing", "line list", "sheet no")
        repeated_pid_signal = text_lowered.count("p&id") >= 3 and "sheet" in text_lowered
        if any(marker in name_lowered for marker in name_markers) or any(marker in text_lowered for marker in text_markers) or repeated_pid_signal:
            return True
        return bool(
            re.search(
                r"(?:^|[\_/\-])(?:pid|p&id|pandid)[^\n]*\.(?:pdf|png|jpg)",
                name_lowered,
            )
        )

    @staticmethod
    def _rrf_fusion(dense_results: Sequence[Any], sparse_results: Sequence[Any], recent_results: Optional[Sequence[Any]] = None) -> List[RetrievalResult]:
        ranked: Dict[str, Dict[str, Any]] = {}

        def add_ranked(items: Iterable[Any], k: float = 60.0) -> None:
            for idx, item in enumerate(items or []):
                if isinstance(item, dict):
                    result = item.get("result")
                    chunk_id = str(item.get("chunk_id") or getattr(result, "chunk_id", ""))
                else:
                    result = item
                    chunk_id = getattr(result, "chunk_id", "")
                if not chunk_id:
                    continue
                entry = ranked.setdefault(chunk_id, {"result": result, "score": 0.0})
                entry["score"] += 1.0 / (k + idx + 1)

        add_ranked(dense_results, 60.0)
        add_ranked(sparse_results, 60.0)
        add_ranked(recent_results or [], 10.0)

        ordered = sorted(ranked.values(), key=lambda item: item["score"], reverse=True)
        return [entry["result"] for entry in ordered]

    def retrieve(self, query: str, user_clearance: Optional[Sequence[str]] = None, top_k: int = 5) -> List[RetrievalResult]:
        """Compatibility adapter for container smoke tests and local callers."""
        from app.services.rag_service import rag_service

        context = rag_service.build_rag_context(
            query=query,
            user_clearance=user_clearance,
            top_k=top_k,
        )
        results: List[RetrievalResult] = []
        for index, citation in enumerate(context.get("citations", [])):
            location = citation.get("location") or {}
            results.append(
                RetrievalResult(
                    chunk_id=str(citation.get("chunk_id") or f"citation_{index + 1}"),
                    doc_name=str(citation.get("document_name") or citation.get("document") or "unknown.pdf"),
                    page=int(citation.get("page") or location.get("page") or 1),
                    section_title=str(citation.get("section_title") or "Introduction"),
                    classification_tag=str(citation.get("classification_tag") or citation.get("tag") or "INTERNAL"),
                    text=str(citation.get("snippet") or ""),
                    stored_filename=citation.get("stored_filename"),
                    bbox=citation.get("bbox"),
                    page_width=citation.get("page_width"),
                    page_height=citation.get("page_height"),
                    score=float(max(0.0, 1.0 - (index * 0.05))),
                    rerank_score=float(max(0.0, 1.0 - (index * 0.05))),
                    metadata=dict(citation),
                )
            )
        return results

    def to_citation_dicts(self, results: Sequence[RetrievalResult]) -> List[Dict[str, Any]]:
        citations: List[Dict[str, Any]] = []
        for result in results or []:
            doc_name = result.doc_name or ""
            text = result.text or ""
            drawing = self._is_drawing_document(doc_name, text)
            text_tags = extract_identifiers(text)
            metadata_tags = result.metadata.get("equipment_tags", []) if result.metadata else []
            all_tags: List[str] = []
            for tag in [*text_tags, *metadata_tags]:
                normalized_tag = self._extract_object_tag(str(tag))
                if normalized_tag and normalized_tag not in all_tags:
                    all_tags.append(normalized_tag)
            object_tag = all_tags[0] if all_tags else self._extract_object_tag(doc_name)
            sheet = result.page if drawing else None
            location = {"page": result.page}
            if drawing:
                location = {"page": result.page, "sheet": sheet or 1}
            geometry = {"type": "bbox"}
            if result.bbox and len(result.bbox) >= 4:
                x0, y0, x1, y1 = result.bbox
                geometry = {
                    "type": "bbox",
                    "x": float(x0),
                    "y": float(y0),
                    "width": float(max(0.0, x1 - x0)),
                    "height": float(max(0.0, y1 - y0)),
                }

            citation = {
                "chunk_id": result.chunk_id,
                "document": doc_name,
                "document_name": doc_name,
                "document_type": "engineering_drawing" if drawing else "technical_document",
                "drawing_type": "P&ID" if drawing else None,
                "sheet": sheet,
                "object_tag": object_tag,
                "target": {"type": "equipment", "tag": object_tag},
                "geometry": geometry,
                "location": location,
                "classification_tag": result.classification_tag,
                "tag": result.classification_tag,
                "page": result.page,
                "section_title": result.section_title,
                "snippet": text,
                "stored_filename": result.stored_filename,
                "document_id": result.metadata.get("document_id"),
                "bbox": result.bbox,
                "page_width": result.page_width,
                "page_height": result.page_height,
                "asset_lineage": {
                    "equipment_tag": object_tag,
                    "equipment_tags": all_tags or ([object_tag] if object_tag else []),
                    "related_tags": [tag for tag in all_tags if tag != object_tag],
                    "document_type": "engineering_drawing" if drawing else "technical_document",
                    "drawing_type": "P&ID" if drawing else None,
                    "sheet": sheet,
                    "page": result.page,
                    "document_name": doc_name,
                    "target_type": "equipment" if drawing else "text",
                    "source_kind": "drawing_sheet" if drawing else "technical_excerpt",
                },
                "source": {
                    "document_name": doc_name,
                    "page": result.page,
                    "section_title": result.section_title,
                    "source_type": result.metadata.get("source_type", "TEXT"),
                    "extraction_method": result.metadata.get("extraction_method", "pymupdf"),
                    "content_hash": result.metadata.get("content_hash"),
                },
                "source_type": result.metadata.get("source_type", "TEXT"),
                "extraction_method": result.metadata.get("extraction_method", "pymupdf"),
                "engineering_tags": result.metadata.get("engineering_tags", []),
            }

            if not drawing:
                citation["sheet"] = None
                citation["drawing_type"] = None
                citation["target"] = {"type": "text", "tag": object_tag or "SOURCE"}
                citation["location"] = {"page": result.page}

            citations.append(citation)

        return citations


retrieval_service = RetrievalService()

__all__ = ["RetrievalResult", "RetrievalService", "retrieval_service"]
