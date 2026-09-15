"""Ingestion pipeline for the hybrid RAG stack.

The pipeline parses PDF documents with PyMuPDF (fitz), groups page content into
layout-aware chunks, enriches them with section metadata, embeds them with the
configured dense/sparse models, and writes them into Qdrant.
"""

import hashlib
import logging
import os
import re
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import pymupdf as fitz
from fastembed import TextEmbedding
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, SparseVector, VectorParams

from app.core.config import settings

logger = logging.getLogger(__name__)


class IngestionService:
    """Build a layout-aware document index in Qdrant."""

    DENSE_MODEL = settings.DENSE_EMBEDDING_MODEL
    SPARSE_MODEL = settings.SPARSE_EMBEDDING_MODEL
    COLLECTION_NAME = settings.QDRANT_COLLECTION
    DENSE_DIM = 384
    CHUNK_SIZE = settings.CHUNK_SIZE_TOKENS
    CHUNK_OVERLAP = settings.CHUNK_OVERLAP_TOKENS

    def __init__(self) -> None:
        self.qdrant_client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT, check_compatibility=False)
        self.dense_embedder: Optional[TextEmbedding] = None
        self.sparse_embedder: Optional[TextEmbedding] = None
        self.dense_model_name = self.DENSE_MODEL

    def _load_supported_dense_model(self) -> Optional[TextEmbedding]:
        try:
            return TextEmbedding(model_name=self.DENSE_MODEL)
        except Exception as exc:
            logger.warning("Failed to load dense embedding model '%s': %s", self.DENSE_MODEL, exc)
            return None

    def _load_supported_sparse_model(self) -> Optional[TextEmbedding]:
        return None

    def _ensure_ready(self) -> bool:
        if self.dense_embedder is None:
            dense_model = self._load_supported_dense_model()
            if dense_model is None:
                logger.warning("Dense embedding model could not be initialized for the configured environment.")
                return False
            self.dense_embedder = dense_model

        if self.sparse_embedder is None:
            try:
                self.sparse_embedder = self._load_supported_sparse_model()
            except Exception as exc:  # pragma: no cover
                logger.warning("Sparse embedding model could not be initialized: %s", exc)
                self.sparse_embedder = None

        return self.dense_embedder is not None

    def _ensure_collection_exists(self) -> None:
        try:
            info = self.qdrant_client.get_collection(self.COLLECTION_NAME)
            dense_cfg = info.config.params.vectors
            if isinstance(dense_cfg, dict) and "dense" in dense_cfg:
                current_dim = dense_cfg["dense"].size
                if current_dim != self.DENSE_DIM:
                    logger.warning("Recreating collection '%s': dimension mismatch (%d vs %d)", self.COLLECTION_NAME, current_dim, self.DENSE_DIM)
                    self.qdrant_client.delete_collection(self.COLLECTION_NAME)
                else:
                    logger.info("Collection '%s' already exists with matching dimension %d.", self.COLLECTION_NAME, self.DENSE_DIM)
                    return
            else:
                logger.info("Collection '%s' already exists.", self.COLLECTION_NAME)
                return
        except Exception:
            pass

        try:
            logger.info("Creating collection '%s'...", self.COLLECTION_NAME)
            self.qdrant_client.create_collection(
                collection_name=self.COLLECTION_NAME,
                vectors_config={
                    "dense": VectorParams(size=self.DENSE_DIM, distance=Distance.COSINE),
                },
                on_disk_payload=True,
            )
            logger.info("Collection '%s' created successfully.", self.COLLECTION_NAME)
        except Exception as exc:  # pragma: no cover
            logger.warning("Qdrant collection '%s' was not created: %s", self.COLLECTION_NAME, exc)

    def ingest_pdf(
        self,
        pdf_path: str,
        doc_name: str,
        classification_tag: str = "INTERNAL",
        section_context: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        logger.info("Starting ingestion for %s from %s", doc_name, pdf_path)
        doc = fitz.open(pdf_path)
        stats: Dict[str, Any] = {
            "total_chunks": 0,
            "total_tables": 0,
            "total_tokens": 0,
            "upserted_ids": [],
        }

        try:
            current_section = section_context.get("default", "Introduction") if section_context else "Introduction"
            chunks: List[Dict[str, Any]] = []
            header_font_size = self._detect_header_font_size(doc)

            for page_num, page in enumerate(doc, start=1):
                tables = page.find_tables()
                for table in tables:
                    table_text = self._format_table_text(table.extract())
                    if table_text:
                        chunks.append({
                            "page": page_num,
                            "text": table_text,
                            "section_title": current_section,
                            "is_table": True,
                        })
                        stats["total_tables"] += 1

                page_blocks = self._extract_layout_blocks(page)
                for kind, block_text, block_font_size, block_title in page_blocks:
                    if not block_text or not block_text.strip():
                        continue

                    candidate_section = current_section
                    if block_font_size and block_font_size >= max(header_font_size * 1.3, 12.0):
                        candidate_section = self._normalize_section_title(block_text)
                        if candidate_section:
                            current_section = candidate_section

                    if kind == "table":
                        chunks.append({
                            "page": page_num,
                            "text": self._clean_text(block_text),
                            "section_title": current_section,
                            "is_table": True,
                        })
                        stats["total_tables"] += 1
                        continue

                    chunk_texts = self._chunk_text(block_text)
                    for chunk in chunk_texts:
                        chunks.append({
                            "page": page_num,
                            "text": chunk,
                            "section_title": current_section,
                            "is_table": False,
                        })

            self._ensure_collection_exists()
            upserted_ids = self._embed_and_upsert(chunks, doc_name, classification_tag)
            stats["total_chunks"] = len(chunks)
            stats["upserted_ids"] = upserted_ids
            logger.info("Ingestion complete for %s: %d chunks, %d tables, %d upserted", doc_name, len(chunks), stats["total_tables"], len(upserted_ids))
            return stats
        finally:
            doc.close()

    def _detect_header_font_size(self, doc: fitz.Document) -> float:
        font_sizes: List[float] = []
        sample_pages = list(doc[: min(3, len(doc))])
        for page in sample_pages:
            for _, text, font_size, _ in self._extract_layout_blocks(page):
                if font_size:
                    font_sizes.append(font_size)

        if not font_sizes:
            return 12.0
        font_sizes.sort()
        median = font_sizes[len(font_sizes) // 2]
        return float(median)

    def _extract_layout_blocks(self, page: fitz.Page) -> List[Tuple[str, str, Optional[float], Optional[str]]]:
        blocks: List[Tuple[str, str, Optional[float], Optional[str]]] = []
        page_dict = page.get_text("dict")
        for block in page_dict.get("blocks", []):
            if "lines" not in block:
                continue

            texts: List[str] = []
            max_font_size: Optional[float] = None
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    text = span.get("text", "").strip()
                    if text:
                        texts.append(text)
                    size = float(span.get("size", 0) or 0)
                    if size > 0 and (max_font_size is None or size > max_font_size):
                        max_font_size = size

            text = " ".join(texts).strip()
            if not text:
                continue
            blocks.append(("text", text, max_font_size, None))
        return blocks

    def _normalize_section_title(self, text: str) -> str:
        cleaned = re.sub(r"\s+", " ", text or "").strip()
        cleaned = re.sub(r"[^A-Za-z0-9\s\-_.:/]", "", cleaned)
        return cleaned[:120] if cleaned else "Introduction"

    def _clean_text(self, text: str) -> str:
        return re.sub(r"\s+", " ", text or "").strip()

    def _chunk_text(self, text: str) -> List[str]:
        cleaned = self._clean_text(text)
        if not cleaned:
            return []

        chunk_chars = max(600, self.CHUNK_SIZE * 4)
        overlap_chars = max(120, self.CHUNK_OVERLAP * 4)
        chunks: List[str] = []
        start = 0

        while start < len(cleaned):
            end = min(start + chunk_chars, len(cleaned))
            chunk = cleaned[start:end].strip()
            if chunk:
                chunks.append(chunk)
            if end >= len(cleaned):
                break
            start = max(start + chunk_chars - overlap_chars, 0)

        return chunks

    def _format_table_text(self, table_data: Sequence[Sequence[Any]]) -> str:
        lines: List[str] = []
        for row in table_data:
            lines.append(" | ".join(str(cell or "").strip() for cell in row))
        return "\n".join(line for line in lines if line)

    def _build_sparse_vector(self, raw_sparse: Any) -> Optional[SparseVector]:
        if raw_sparse is None:
            return None

        if isinstance(raw_sparse, dict):
            indices = list(raw_sparse.get("indices", []))
            values = list(raw_sparse.get("values", []))
        elif hasattr(raw_sparse, "indices") and hasattr(raw_sparse, "values"):
            indices = list(raw_sparse.indices)
            values = list(raw_sparse.values)
        elif isinstance(raw_sparse, (list, tuple)) and raw_sparse and isinstance(raw_sparse[0], (list, tuple)) and len(raw_sparse[0]) == 2:
            indices = [int(item[0]) for item in raw_sparse]
            values = [float(item[1]) for item in raw_sparse]
        else:
            arr = list(raw_sparse)
            non_zero = [(idx, float(value)) for idx, value in enumerate(arr) if abs(float(value)) > 1e-8]
            if not non_zero:
                return None
            indices = [idx for idx, _ in non_zero]
            values = [value for _, value in non_zero]

        if not indices:
            return None
        return SparseVector(indices=[int(i) for i in indices], values=[float(v) for v in values])

    def _embed_and_upsert(
        self,
        chunks: List[Dict[str, Any]],
        doc_name: str,
        classification_tag: str,
    ) -> List[str]:
        if not chunks:
            return []

        if not self._ensure_ready():
            raise RuntimeError("Dense embedding model is unavailable. Please verify the embedding installation and configuration.")

        texts = [chunk["text"] for chunk in chunks if chunk.get("text")]
        if not texts:
            return []

        logger.info("Embedding %d chunks with dense model...", len(texts))
        dense_embeddings = list(self.dense_embedder.embed(texts))

        sparse_embeddings: List[Any] = []
        if self.sparse_embedder is not None:
            logger.info("Embedding %d chunks with sparse model...", len(texts))
            sparse_embeddings = list(self.sparse_embedder.embed(texts))

        points: List[PointStruct] = []
        upserted_ids: List[str] = []

        for idx, chunk in enumerate(chunks):
            if not chunk.get("text"):
                continue

            chunk_id = self._generate_chunk_id(doc_name, chunk["page"], idx)
            upserted_ids.append(chunk_id)

            dense_vec = dense_embeddings[len(upserted_ids) - 1]
            dense_vector = dense_vec.tolist() if hasattr(dense_vec, "tolist") else list(dense_vec)

            sparse_vector = None
            if self.sparse_embedder is not None and idx < len(sparse_embeddings):
                sparse_vector = self._build_sparse_vector(sparse_embeddings[idx])

            payload = {
                "chunk_id": chunk_id,
                "doc_name": doc_name,
                "page": int(chunk["page"]),
                "section_title": chunk.get("section_title", "Introduction"),
                "classification_tag": classification_tag,
                "text": chunk["text"],
                "is_table": bool(chunk.get("is_table", False)),
                "ingested_at": datetime.now(timezone.utc).isoformat(),
            }

            vector_payload: Dict[str, Any] = {"dense": dense_vector}
            if sparse_vector is not None:
                vector_payload["sparse"] = sparse_vector

            points.append(
                PointStruct(
                    id=self._hash_to_int(chunk_id),
                    vector=vector_payload,
                    payload=payload,
                )
            )

        logger.info("Upserting %d points to Qdrant...", len(points))
        self.qdrant_client.upsert(collection_name=self.COLLECTION_NAME, points=points)
        logger.info("Successfully upserted %d points.", len(points))
        return upserted_ids

    def _generate_chunk_id(self, doc_name: str, page: int, chunk_idx: int) -> str:
        return f"{doc_name}__page_{page}__chunk_{chunk_idx}"

    def _hash_to_int(self, text: str) -> int:
        return int(hashlib.md5(text.encode("utf-8")).hexdigest(), 16) & 0x7FFFFFFF


ingestion_service = IngestionService()
