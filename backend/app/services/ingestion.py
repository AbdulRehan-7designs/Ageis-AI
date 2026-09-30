"""Ingestion pipeline for the hybrid RAG stack.

The pipeline parses PDF documents with PyMuPDF (fitz), groups page content into
layout-aware chunks, enriches them with section metadata, embeds them with the
configured dense/sparse models, and writes them into Qdrant.
"""

import hashlib
import io
import logging
import os
import re
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import pymupdf as fitz
try:
    import pytesseract
    from PIL import Image
except ImportError:  # pragma: no cover - optional local OCR runtime
    pytesseract = None
    Image = None
from fastembed import TextEmbedding
try:
    from fastembed import SparseTextEmbedding
except ImportError:  # pragma: no cover
    SparseTextEmbedding = None

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, SparseVector, VectorParams
try:
    from qdrant_client.models import PayloadSchemaType, SparseVectorParams
except ImportError:  # pragma: no cover
    PayloadSchemaType = None
    SparseVectorParams = None

from app.core.config import settings
from app.services.identifiers import extract_identifiers, tags_from_chunks_text

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
        self.sparse_embedder = None
        self.dense_model_name = self.DENSE_MODEL
        self._memory_chunks: List[Dict[str, Any]] = []

    def _load_supported_dense_model(self) -> Optional[TextEmbedding]:
        try:
            return TextEmbedding(model_name=self.DENSE_MODEL)
        except Exception as exc:
            logger.warning("Failed to load dense embedding model '%s': %s", self.DENSE_MODEL, exc)
            return None

    def _load_supported_sparse_model(self):
        if SparseTextEmbedding is None:
            logger.warning("fastembed.SparseTextEmbedding is not installed; BM25 hybrid search is disabled.")
            return None
        try:
            return SparseTextEmbedding(model_name=self.SPARSE_MODEL)
        except Exception as exc:
            logger.warning("Failed to load sparse embedding model '%s': %s", self.SPARSE_MODEL, exc)
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

    def _sparse_vector_names(self, info: Any) -> List[str]:
        sparse_cfg = getattr(getattr(info.config, "params", None), "sparse_vectors", None)
        if not sparse_cfg:
            return []
        if isinstance(sparse_cfg, dict):
            return list(sparse_cfg.keys())
        try:
            return list(sparse_cfg)
        except TypeError:
            return ["sparse"] if sparse_cfg else []

    def _collection_has_sparse(self) -> bool:
        try:
            info = self.qdrant_client.get_collection(self.COLLECTION_NAME)
            names = self._sparse_vector_names(info)
            return "sparse" in names or bool(names)
        except Exception:
            return False

    def _points_count(self, info: Any) -> int:
        value = getattr(info, "points_count", None)
        return int(value) if value is not None else 0

    def _ensure_payload_indexes(self) -> None:
        if PayloadSchemaType is None:
            return
        for field in ("classification_tag", "equipment_tags", "doc_name"):
            try:
                self.qdrant_client.create_payload_index(
                    collection_name=self.COLLECTION_NAME,
                    field_name=field,
                    field_schema=PayloadSchemaType.KEYWORD,
                )
            except Exception:
                pass

    def _create_collection(self) -> None:
        logger.info("Creating collection '%s' with dense + sparse vectors...", self.COLLECTION_NAME)
        kwargs: Dict[str, Any] = {
            "collection_name": self.COLLECTION_NAME,
            "vectors_config": {
                "dense": VectorParams(size=self.DENSE_DIM, distance=Distance.COSINE),
            },
            "on_disk_payload": True,
        }
        if SparseVectorParams is not None:
            kwargs["sparse_vectors_config"] = {"sparse": SparseVectorParams()}
        self.qdrant_client.create_collection(**kwargs)
        self._ensure_payload_indexes()
        logger.info("Collection '%s' created successfully.", self.COLLECTION_NAME)

    def _ensure_collection_exists(self) -> None:
        try:
            info = self.qdrant_client.get_collection(self.COLLECTION_NAME)
            dense_cfg = info.config.params.vectors
            dim_ok = True
            if isinstance(dense_cfg, dict) and "dense" in dense_cfg:
                current_dim = dense_cfg["dense"].size
                dim_ok = current_dim == self.DENSE_DIM
            points = self._points_count(info)
            sparse_ok = bool(self._sparse_vector_names(info)) or SparseVectorParams is None

            if dim_ok:
                if not sparse_ok:
                    logger.warning(
                        "Collection '%s' has no sparse vectors; keeping %d existing document(s). "
                        "BM25 is skipped until the collection is empty and recreated.",
                        self.COLLECTION_NAME,
                        points,
                    )
                self._ensure_payload_indexes()
                return

            if points > 0:
                logger.warning(
                    "Collection '%s' dense dimension mismatch but %d points exist — not deleting.",
                    self.COLLECTION_NAME,
                    points,
                )
                return

            logger.warning("Recreating empty collection '%s' due to dimension mismatch.", self.COLLECTION_NAME)
            self.qdrant_client.delete_collection(self.COLLECTION_NAME)
        except Exception:
            pass

        try:
            self._create_collection()
        except Exception as exc:  # pragma: no cover
            logger.warning("Qdrant collection '%s' was not created: %s", self.COLLECTION_NAME, exc)

    def list_documents(
        self,
        allowed_tags: Optional[Sequence[str]] = None,
        query: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        allowed = {str(tag).upper() for tag in (allowed_tags or []) if str(tag).strip()}
        normalized_query = (query or "").strip().casefold()

        def include(document: Dict[str, Any]) -> bool:
            classification = str(document.get("classification_tag") or "INTERNAL").upper()
            if allowed and classification not in allowed:
                return False
            if normalized_query:
                searchable = " ".join(
                    str(document.get(field) or "")
                    for field in (
                        "document_name",
                        "document_type",
                        "drawing_type",
                        "object_tag",
                        "source_kind",
                        "equipment_tags",
                        "related_tags",
                    )
                ).casefold()
                if normalized_query not in searchable:
                    return False
            return True

        documents: Dict[str, Dict[str, Any]] = {}
        offset = None
        try:
            while True:
                points, offset = self.qdrant_client.scroll(
                    collection_name=self.COLLECTION_NAME,
                    with_payload=True,
                    with_vectors=False,
                    limit=128,
                    offset=offset,
                )
                for point in points or []:
                    payload = point.payload or {}
                    name = payload.get("doc_name")
                    if not name:
                        continue
                    document = documents.setdefault(name, {
                        "document_name": name,
                        "document_id": payload.get("document_id"),
                        "stored_filename": payload.get("stored_filename"),
                        "classification_tag": payload.get("classification_tag", "INTERNAL"),
                        "document_type": payload.get("document_type", "technical_document"),
                        "drawing_type": payload.get("drawing_type"),
                        "object_tag": payload.get("object_tag"),
                        "equipment_tags": [],
                        "related_tags": [],
                        "source_kind": payload.get("source_kind", "technical_excerpt"),
                        "source_type": payload.get("source_type", "TEXT"),
                        "extraction_method": payload.get("extraction_method", "pymupdf"),
                        "status": "INDEXED",
                    })
                    document["equipment_tags"] = sorted(set(document["equipment_tags"] + payload.get("equipment_tags", [])))
                    document["related_tags"] = sorted(set(document["related_tags"] + payload.get("related_tags", [])))
                    if not document.get("object_tag") and payload.get("object_tag"):
                        document["object_tag"] = payload["object_tag"]
                    if payload.get("source_type") == "OCR":
                        document["source_type"] = "OCR"
                        document["extraction_method"] = payload.get("extraction_method", "local_tesseract")
                    if payload.get("engineering_tags"):
                        document.setdefault("engineering_tags", [])
                        document["engineering_tags"] = sorted(set(
                            document["engineering_tags"]
                            + [
                                item.get("tag", "") if isinstance(item, dict) else str(item)
                                for item in payload["engineering_tags"]
                            ]
                        ))
                        document.setdefault("engineering_evidence", []).extend(payload["engineering_tags"])
                if offset is None:
                    break
        except Exception as exc:
            logger.warning("Could not list documents from Qdrant: %s", exc)

        for payload in self._memory_chunks:
            name = payload.get("doc_name")
            if not name:
                continue
            document = documents.setdefault(name, {
                "document_name": name,
                "document_id": payload.get("document_id"),
                "stored_filename": payload.get("stored_filename"),
                "classification_tag": payload.get("classification_tag", "INTERNAL"),
                "document_type": payload.get("document_type", "technical_document"),
                "drawing_type": payload.get("drawing_type"),
                "object_tag": payload.get("object_tag"),
                "equipment_tags": [],
                "related_tags": [],
                "source_kind": payload.get("source_kind", "technical_excerpt"),
                "source_type": payload.get("source_type", "TEXT"),
                "extraction_method": payload.get("extraction_method", "pymupdf"),
                "status": "MEMORY_INDEXED",
            })
            document["equipment_tags"] = sorted(set(document["equipment_tags"] + payload.get("equipment_tags", [])))
            document["related_tags"] = sorted(set(document["related_tags"] + payload.get("related_tags", [])))
            if payload.get("engineering_tags"):
                document.setdefault("engineering_tags", [])
                document["engineering_tags"] = sorted(set(
                    document["engineering_tags"]
                    + [
                        item.get("tag", "") if isinstance(item, dict) else str(item)
                        for item in payload["engineering_tags"]
                    ]
                ))
                document.setdefault("engineering_evidence", []).extend(payload["engineering_tags"])
            if not document.get("object_tag") and payload.get("object_tag"):
                document["object_tag"] = payload["object_tag"]
            if document.get("status") == "INDEXED" and payload.get("source_kind"):
                document["source_kind"] = payload["source_kind"]
        return [document for document in documents.values() if include(document)]

    def ingest_pdf(
        self,
        pdf_path: str,
        doc_name: str,
        classification_tag: str = "INTERNAL",
        section_context: Optional[Dict[str, str]] = None,
        stored_filename: Optional[str] = None,
    ) -> Dict[str, Any]:
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        logger.info("Starting ingestion for %s from %s", doc_name, pdf_path)
        doc = fitz.open(pdf_path)
        with open(pdf_path, "rb") as source_file:
            content_hash = hashlib.sha256(source_file.read()).hexdigest()
        stats: Dict[str, Any] = {
            "total_chunks": 0,
            "total_tables": 0,
            "total_tokens": 0,
            "page_count": len(doc),
            "upserted_ids": [],
            "metadata": {},
        }

        try:
            current_section = section_context.get("default", "Introduction") if section_context else "Introduction"
            chunks: List[Dict[str, Any]] = []
            header_font_size = self._detect_header_font_size(doc)
            doc_text_parts: List[str] = []

            for page_num, page in enumerate(doc, start=1):
                tables = page.find_tables()
                for table in tables:
                    table_text = self._format_table_text(table.extract())
                    if table_text:
                        bbox = list(getattr(table, "bbox", []) or []) or None
                        chunks.append({
                            "page": page_num,
                            "text": table_text,
                            "section_title": current_section,
                            "is_table": True,
                            "bbox": bbox,
                            "page_width": page.rect.width,
                            "page_height": page.rect.height,
                        })
                        stats["total_tables"] += 1

                page_blocks = self._extract_layout_blocks(page)
                page_rect = page.rect
                page_text = page.get_text("text") or ""
                if self._needs_ocr(page_text):
                    ocr_text = self._ocr_page(page)
                    if ocr_text:
                        chunks.append({
                            "page": page_num,
                            "text": ocr_text,
                            "section_title": current_section,
                            "is_table": False,
                            "bbox": None,
                            "page_width": page_rect.width,
                            "page_height": page_rect.height,
                            "source_type": "OCR",
                            "extraction_method": "local_tesseract",
                        })
                        doc_text_parts.append(ocr_text)
                        stats.setdefault("ocr_pages", []).append(page_num)
                for kind, block_text, block_font_size, block_title, block_bbox in page_blocks:
                    if not block_text or not block_text.strip():
                        continue
                    doc_text_parts.append(block_text)

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
                            "bbox": block_bbox,
                            "page_width": page_rect.width,
                            "page_height": page_rect.height,
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
                            "bbox": block_bbox,
                            "page_width": page_rect.width,
                            "page_height": page_rect.height,
                        })

            self._ensure_collection_exists()
            doc_text = "\n".join(doc_text_parts)
            stats["metadata"] = self._infer_document_metadata(doc_name, doc_text)
            stats["metadata"].update({
                "page_count": len(doc),
                "chunk_count": len(chunks),
                "table_count": stats["total_tables"],
                "identifier_count": len(stats["metadata"].get("equipment_tags", [])),
                "evidence_ready": bool(chunks),
                "content_hash": content_hash,
                "ocr_pages": stats.get("ocr_pages", []),
            })
            for chunk in chunks:
                chunk.setdefault("source_type", "TEXT")
                chunk.setdefault("extraction_method", "pymupdf")
                chunk["content_hash"] = content_hash
                chunk["document_name"] = doc_name
                chunk["classification_tag"] = classification_tag
                chunk["document_equipment_tags"] = stats["metadata"].get("equipment_tags", [])
            upserted_ids = self._embed_and_upsert(
                chunks, doc_name, classification_tag, stored_filename=stored_filename,
                content_hash=content_hash,
            )
            stats["total_chunks"] = len(chunks)
            stats["upserted_ids"] = upserted_ids
            stats["evidence_ready"] = bool(upserted_ids)
            logger.info("Ingestion complete for %s: %d chunks, %d tables, %d upserted", doc_name, len(chunks), stats["total_tables"], len(upserted_ids))
            return stats
        finally:
            doc.close()

    @staticmethod
    def _needs_ocr(text: str) -> bool:
        normalized = " ".join((text or "").split())
        if len(normalized) < 24:
            return True
        alphanumeric = sum(char.isalnum() for char in normalized)
        return alphanumeric < 20 or alphanumeric / max(len(normalized), 1) < 0.25

    @staticmethod
    def _ocr_page(page: fitz.Page) -> str:
        if pytesseract is None or Image is None:
            logger.warning("Local OCR unavailable; scanned page was not indexed.")
            return ""
        try:
            pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
            image = Image.open(io.BytesIO(pixmap.tobytes("png")))
            return " ".join((pytesseract.image_to_string(image) or "").split())
        except Exception as exc:  # pragma: no cover
            logger.warning("Local OCR failed for page %s: %s", page.number + 1, exc)
            return ""

    def ingest_image(
        self,
        image_path: str,
        doc_name: str,
        classification_tag: str = "INTERNAL",
        stored_filename: Optional[str] = None,
    ) -> Dict[str, Any]:
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")
        if pytesseract is None or Image is None:
            raise RuntimeError("Local OCR is unavailable; install Tesseract and pytesseract.")
        try:
            with Image.open(image_path) as image:
                text = " ".join((pytesseract.image_to_string(image) or "").split())
                width, height = image.size
        except Exception as exc:
            raise RuntimeError(f"Unable to process image '{doc_name}'.") from exc
        if not text:
            raise RuntimeError(f"Local OCR returned no text for '{doc_name}'.")
        with open(image_path, "rb") as source_file:
            content_hash = hashlib.sha256(source_file.read()).hexdigest()
        chunks = [{
            "page": 1, "text": text, "section_title": "Image",
            "is_table": False, "bbox": None, "page_width": width,
            "page_height": height, "source_type": "OCR",
            "extraction_method": "local_tesseract", "content_hash": content_hash,
            "document_name": doc_name, "classification_tag": classification_tag,
        }]
        self._ensure_collection_exists()
        upserted_ids = self._embed_and_upsert(
            chunks, doc_name, classification_tag, stored_filename=stored_filename,
            content_hash=content_hash,
        )
        return {
            "page_count": 1, "total_chunks": len(chunks), "total_tables": 0,
            "ocr_pages": [1], "upserted_ids": upserted_ids,
            "evidence_ready": bool(upserted_ids),
            "metadata": {"source_type": "OCR", "extraction_method": "local_tesseract", "content_hash": content_hash},
        }

    def _detect_header_font_size(self, doc: fitz.Document) -> float:
        font_sizes: List[float] = []
        sample_pages = list(doc[: min(3, len(doc))])
        for page in sample_pages:
            for _, text, font_size, _, _ in self._extract_layout_blocks(page):
                if font_size:
                    font_sizes.append(font_size)

        if not font_sizes:
            return 12.0
        font_sizes.sort()
        median = font_sizes[len(font_sizes) // 2]
        return float(median)

    def _extract_layout_blocks(self, page: fitz.Page) -> List[Tuple[str, str, Optional[float], Optional[str], Optional[List[float]]]]:
        blocks: List[Tuple[str, str, Optional[float], Optional[str], Optional[List[float]]]] = []
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
            bbox = list(block.get("bbox", [])) or None
            blocks.append(("text", text, max_font_size, None, bbox))
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
        stored_filename: Optional[str] = None,
        content_hash: Optional[str] = None,
    ) -> List[str]:
        if not chunks:
            return []

        try:
            if not self._ensure_ready():
                raise RuntimeError("Dense embedding model is unavailable. Please verify the embedding installation and configuration.")

            texts = [chunk["text"] for chunk in chunks if chunk.get("text")]
            if not texts:
                return []

            logger.info("Embedding %d chunks with dense model...", len(texts))
            dense_embeddings = list(self.dense_embedder.embed(texts))

            sparse_embeddings: List[Any] = []
            if self.sparse_embedder is not None:
                logger.info("Embedding %d chunks with sparse model '%s'...", len(texts), self.SPARSE_MODEL)
                embed_fn = getattr(self.sparse_embedder, "embed", None)
                sparse_embeddings = list(embed_fn(texts)) if embed_fn else []

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
                emb_i = len(upserted_ids) - 1
                if self.sparse_embedder is not None and emb_i < len(sparse_embeddings):
                    sparse_vector = self._build_sparse_vector(sparse_embeddings[emb_i])

                doc_metadata = self._infer_document_metadata(doc_name, chunk["text"])
                engineering_tags = extract_identifiers(chunk["text"])
                payload = {
                    "chunk_id": chunk_id,
                    "doc_name": doc_name,
                    "page": int(chunk["page"]),
                    "section_title": chunk.get("section_title", "Introduction"),
                    "classification_tag": classification_tag,
                    "text": chunk["text"],
                    "is_table": bool(chunk.get("is_table", False)),
                    "ingested_at": datetime.now(timezone.utc).isoformat(),
                    "stored_filename": stored_filename,
                    "bbox": chunk.get("bbox"),
                    "page_width": chunk.get("page_width"),
                    "page_height": chunk.get("page_height"),
                    "equipment_tags": doc_metadata.get("equipment_tags") or chunk.get("document_equipment_tags") or tags_from_chunks_text(chunk["text"]),
                    "related_tags": doc_metadata.get("related_tags", []),
                    "source_kind": doc_metadata.get("source_kind"),
                    "document_type": doc_metadata.get("document_type"),
                    "drawing_type": doc_metadata.get("drawing_type"),
                    "object_tag": doc_metadata.get("object_tag"),
                    "target": doc_metadata.get("target"),
                    "source_type": doc_metadata.get("source_type") or chunk.get("source_type", "TEXT"),
                    "extraction_method": chunk.get("extraction_method", "pymupdf"),
                    "content_hash": chunk.get("content_hash") or content_hash,
                    "document_name": doc_name,
                    "document_id": chunk.get("document_id") or content_hash,
                    "engineering_tags": [
                        {
                            "tag": tag,
                            "document_id": chunk.get("document_id") or content_hash,
                            "page": int(chunk["page"]),
                            "source_type": doc_metadata.get("source_type") or "TEXT",
                            "extraction_method": "OCR" if chunk.get("source_type") == "OCR" else "TEXT",
                            "classification": classification_tag,
                        }
                        for tag in engineering_tags
                    ],
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
        except Exception as exc:  # pragma: no cover - guarded for offline/local demo environments
            logger.warning("Qdrant/vector storage is unavailable; falling back to in-memory index for %s: %s", doc_name, exc)
            memory_payloads: List[Dict[str, Any]] = []
            for idx, chunk in enumerate(chunks):
                if not chunk.get("text"):
                    continue
                chunk_id = self._generate_chunk_id(doc_name, chunk["page"], idx)
                doc_metadata = self._infer_document_metadata(doc_name, chunk["text"])
                engineering_tags = extract_identifiers(chunk["text"])
                payload = {
                    "chunk_id": chunk_id,
                    "doc_name": doc_name,
                    "page": int(chunk["page"]),
                    "section_title": chunk.get("section_title", "Introduction"),
                    "classification_tag": classification_tag,
                    "text": chunk["text"],
                    "is_table": bool(chunk.get("is_table", False)),
                    "ingested_at": datetime.now(timezone.utc).isoformat(),
                    "stored_filename": stored_filename,
                    "bbox": chunk.get("bbox"),
                    "page_width": chunk.get("page_width"),
                    "page_height": chunk.get("page_height"),
                    "equipment_tags": doc_metadata.get("equipment_tags") or chunk.get("document_equipment_tags") or tags_from_chunks_text(chunk["text"]),
                    "related_tags": doc_metadata.get("related_tags", []),
                    "source_kind": doc_metadata.get("source_kind"),
                    "document_type": doc_metadata.get("document_type"),
                    "drawing_type": doc_metadata.get("drawing_type"),
                    "object_tag": doc_metadata.get("object_tag"),
                    "target": doc_metadata.get("target"),
                    "source_type": doc_metadata.get("source_type") or chunk.get("source_type", "TEXT"),
                    "extraction_method": chunk.get("extraction_method", "pymupdf"),
                    "content_hash": chunk.get("content_hash") or content_hash,
                    "document_name": doc_name,
                    "document_id": chunk.get("document_id") or content_hash,
                    "engineering_tags": [
                        {
                            "tag": tag,
                            "document_id": chunk.get("document_id") or content_hash,
                            "page": int(chunk["page"]),
                            "source_type": doc_metadata.get("source_type") or "TEXT",
                            "extraction_method": "OCR" if chunk.get("source_type") == "OCR" else "TEXT",
                            "classification": classification_tag,
                        }
                        for tag in engineering_tags
                    ],
                }
                memory_payloads.append(payload)
            self._memory_chunks.extend(memory_payloads)
            return [p["chunk_id"] for p in memory_payloads]

    def _generate_chunk_id(self, doc_name: str, page: int, chunk_idx: int) -> str:
        return f"{doc_name}__page_{page}__chunk_{chunk_idx}"

    def _hash_to_int(self, text: str) -> int:
        return int(hashlib.md5(text.encode("utf-8")).hexdigest(), 16) & 0x7FFFFFFF

    def _infer_document_metadata(self, doc_name: str, text: str) -> Dict[str, Any]:
        name_lowered = (doc_name or "").lower()
        text_lowered = (text or "").lower()
        drawing_name_markers = ("pid", "p&id", "pandid", "isometric", "line_list", "line-list")
        drawing_text_markers = ("process and instrumentation", "isometric drawing", "line list", "sheet no")
        repeated_pid_signal = text_lowered.count("p&id") >= 3 and "sheet" in text_lowered
        is_drawing = any(marker in name_lowered for marker in drawing_name_markers) or any(marker in text_lowered for marker in drawing_text_markers) or repeated_pid_signal
        identifiers = extract_identifiers(text or "")
        object_tag = identifiers[0] if identifiers else ""
        if not object_tag:
            match = re.search(r"\b[A-Z]{1,8}-?\d{2,6}[A-Z0-9]*\b", text or "")
            if match:
                object_tag = match.group(0)
        if is_drawing:
            source_type = "P_AND_ID" if any(marker in name_lowered or marker in text_lowered for marker in ("p&id", "pid", "pandid")) else "ENGINEERING_DRAWING"
            return {
                "document_type": "engineering_drawing",
                "drawing_type": "P&ID" if source_type == "P_AND_ID" else "TECHNICAL_DRAWING",
                "source_type": source_type,
                "sheet": 1,
                "object_tag": object_tag,
                "equipment_tags": identifiers,
                "related_tags": [tag for tag in identifiers if tag != object_tag],
                "engineering_tags": [
                    {"tag": tag, "page": 1, "source_type": source_type, "extraction_method": "OCR"}
                    for tag in identifiers
                ],
                "source_kind": "drawing_sheet",
                "target": {"type": "equipment", "tag": object_tag or "SOURCE"},
            }
        return {
            "document_type": "technical_document",
            "drawing_type": None,
            "sheet": None,
            "object_tag": object_tag,
            "equipment_tags": identifiers,
            "engineering_tags": [],
            "related_tags": [tag for tag in identifiers if tag != object_tag],
            "source_kind": "technical_excerpt",
            "target": {"type": "text", "tag": object_tag or "SOURCE"},
        }


ingestion_service = IngestionService()
