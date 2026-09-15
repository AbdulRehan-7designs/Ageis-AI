# Hybrid RAG System Architecture

This document describes the production-grade hybrid RAG (Retrieval-Augmented Generation) system implemented in AegisAI for industrial document retrieval.

## System Stack (Final)

### Embedding & Retrieval Components

| Component | Model | Purpose |
|-----------|-------|---------|
| **Dense Embedding** | BAAI/bge-m3 | Dense vectors (1024-dim), multilingual, 8192 token context |
| **Sparse Embedding** | Qdrant/bm25 | Sparse vectors via FastEmbed, native to Qdrant |
| **Vector Database** | Qdrant | Single collection with dual named vectors (dense + sparse) |
| **Fusion Strategy** | RRF (Reciprocal Rank Fusion) | Server-side prefetch + fusion, no client-side code |
| **Reranker** | BAAI/bge-reranker-v2-m3 | Local reranking, top-20 → top-5, CPU-only |
| **PDF Parser** | PyMuPDF (fitz) | Native page numbers, font-size metadata, table detection |

## How It Works

### 1. Ingestion Pipeline (`backend/app/services/ingestion.py`)

**Input:** PDF documents (e.g., SOP-017, P204 Manual)

**Process:**
```
PDF → fitz parsing (with font-size analysis)
  ├─ Detect header font sizes (document median + 30%)
  ├─ Extract atomic tables (never split mid-table)
  └─ Chunk body text: 400 tokens, 50-token overlap
    ├─ Dense embedding (bge-m3)
    └─ Sparse embedding (BM25)
      └─ Upsert to Qdrant with metadata
```

**Output:** Qdrant collection `industrial_docs` with:
- Dense vectors (1024-dim, cosine)
- Sparse vectors (BM25, dot product)
- Payload: `chunk_id`, `doc_name`, `page`, `section_title`, `classification_tag`, `text`

### 2. Retrieval Pipeline (`backend/app/services/retrieval.py`)

**Input:** User query + clearance level (RBAC)

**Process:**
```
Query text
  ├─ Embed with bge-m3 (dense)
  ├─ Embed with BM25 (sparse)
  └─ Single Qdrant call:
      ├─ Prefetch top-20 dense
      ├─ Prefetch top-20 sparse
      └─ RRF fusion → top-20 fused results
          └─ RBAC pre-filter (verify clearance)
              └─ Rerank with bge-reranker-v2-m3
                  └─ Top-5 final results
```

**Output:** Ranked list of chunks with:
- `chunk_id`, `doc_name`, `page`, `section_title`
- `classification_tag`, `text`, `rerank_score`

### 3. Why This Design Wins

| Problem | Solution |
|---------|----------|
| **Semantic gaps** (dense alone misses keywords) | Hybrid (dense + sparse) captures both semantic & lexical match |
| **Client-side fusion overhead** | RRF fusion server-side in Qdrant; one API call |
| **Wrong chunks from hybrid alone** | Reranker (bge-reranker-v2-m3) catches semantic mismatch |
| **Table destruction** | fitz + native table detection → atomic chunks |
| **Section loss** | Font-size headers stored as `section_title` metadata |
| **Unauthorized access** | RBAC filter at query time + post-rerank verification |
| **GPU pressure on LLM** | Embedding & reranking on CPU (FastEmbed, FlagEmbedding) |

## Collection Schema

**Collection Name:** `industrial_docs`

**Vectors:**
```python
"dense": VectorParams(size=1024, distance=Distance.COSINE)
"sparse": VectorParams(size=1, distance=Distance.DOT)  # Variable-size sparse
```

**Payload Fields:**
```python
{
    "chunk_id": "P204_Manual.pdf__page_28__chunk_0",
    "doc_name": "P-204_Centrifugal_Pump_Manual.pdf",
    "page": 28,
    "section_title": "Vibration Limits and Monitoring",
    "classification_tag": "INTERNAL",  # CONFIDENTIAL, RESTRICTED, INTERNAL
    "text": "Vibration Limits: Normal < 4.5 mm/s, Warning 4.5-7.1 mm/s, Critical > 7.1 mm/s.",
    "is_table": false,
    "ingested_at": "2025-09-13T10:30:00"
}
```

## Integration Points

### Document Upload

**Endpoint:** `POST /api/v1/document/upload`

```bash
curl -F "file=@P204_Manual.pdf" \
     -F "classification_tag=INTERNAL" \
     http://localhost:8000/api/v1/document/upload
```

**Response:**
```json
{
    "filename": "P204_Manual.pdf",
    "chunks_indexed": 145,
    "classification_tag": "INTERNAL",
    "status": "SUCCESS_INDEXED_HYBRID_RAG",
    "message": "Ingested 145 chunks with 3 tables detected"
}
```

### Chat Query with Retrieval

**Endpoint:** `POST /api/v1/chat`

**Request:**
```json
{
    "message": "What are the vibration limits for P-204?",
    "history": [],
    "classification_filter": "INTERNAL"
}
```

**Response includes:**
```json
{
    "citations": [
        {
            "document": "P-204_Centrifugal_Pump_Manual.pdf",
            "page": 28,
            "tag": "INTERNAL",
            "snippet": "Vibration Limits: Normal < 4.5 mm/s, Warning 4.5-7.1 mm/s, Critical > 7.1 mm/s."
        },
        ...
    ],
    "reasoning_trace": [
        {
            "step_number": 2,
            "title": "Retrieve Evidence (Hybrid RAG)",
            "description": "Dense+Sparse hybrid search with RRF fusion, reranked with bge-reranker. Retrieved 5 results.",
            "status": "completed"
        },
        ...
    ]
}
```

## Configuration

**File:** `backend/app/core/config.py`

```python
# Embedding & Retrieval
DENSE_EMBEDDING_MODEL: str = "BAAI/bge-m3"
SPARSE_EMBEDDING_MODEL: str = "Qdrant/bm25"
RERANKER_MODEL: str = "BAAI/bge-reranker-v2-m3"

# RAG Configuration
CHUNK_SIZE_TOKENS: int = 400
CHUNK_OVERLAP_TOKENS: int = 50
TOP_K_RETRIEVE: int = 5  # Final top-k after reranking
TOP_K_PREFETCH: int = 20  # Prefetch before fusion/reranking

# Qdrant
QDRANT_HOST: str = "localhost"
QDRANT_PORT: int = 6333
QDRANT_COLLECTION: str = "industrial_docs"
```

## Dependencies

**Added to `requirements.txt`:**
```
fastembed>=0.2.0      # Dense + sparse embeddings (CPU-fast)
pymupdf>=1.23.0       # fitz: PDF parsing with font-size & table detection
FlagEmbedding>=1.2.0  # bge-reranker-v2-m3 (local reranking)
```

**Existing (unchanged):**
- qdrant-client >= 1.8.0 (vector DB client)
- fastapi, uvicorn (API framework)

## Chunking Rules (Exact)

1. **Parse PDF** with `fitz.open(pdf_path)` page by page
2. **Detect headers:** Calculate median font size, mark blocks > 1.3× median as headers
3. **Extract tables:** Use `page.find_tables()` → one atomic chunk per table (no splitting)
4. **Chunk body text:** 400 tokens, 50-token overlap (approximated as ~4 chars/token)
5. **Store metadata:**
   - `chunk_id`: Unique by doc + page + chunk_idx
   - `section_title`: Propagate current header to all subsequent chunks until next header
   - `classification_tag`: User-provided (CONFIDENTIAL/RESTRICTED/INTERNAL)
   - `page`: 1-indexed
   - `text`: Raw chunk text
   - `is_table`: Boolean flag (true if this chunk is an extracted table)

## Performance Characteristics

| Step | Model | Compute | Batch Size | Time est. |
|------|-------|---------|------------|-----------|
| Query embedding (dense) | bge-m3 | CPU | 1 | ~10ms |
| Query embedding (sparse) | BM25 | CPU | 1 | ~5ms |
| Qdrant prefetch + RRF fusion | — | GPU/CPU | — | ~50ms |
| Reranking top-20 | bge-reranker-v2-m3 | CPU | 20 | ~100ms |
| **Total retrieval** | — | — | — | **~165ms** |

## Troubleshooting

### Issue: "Collection not found"
- **Fix:** Ensure Qdrant is running (`docker-compose up`)
- **Check:** `python -c "from app.services.ingestion import ingestion_service"`

### Issue: "Reranker download timeout"
- **Fix:** Pre-download manually:
  ```bash
  python -c "from FlagEmbedding import FlagReranker; FlagReranker('BAAI/bge-reranker-v2-m3')"
  ```

### Issue: "Out of memory on sparse embedding"
- **Note:** Sparse embedding is very memory-efficient; if it fails, check overall system RAM
- **Fix:** Use smaller batch sizes or stream embeddings

### Issue: "No results despite documents uploaded"
- **Check:** Document classification_tag matches user_clearance
- **Check:** Qdrant query logs for filter rejections
- **Test:** Upload with `classification_tag="INTERNAL"`, query with same clearance

## Future Enhancements

1. **Batch Re-indexing:** Add endpoint to re-ingest all documents with updated models
2. **Query Expansion:** Pre-process queries (e.g., expand "P-204" → "Pump P-204" + "Centrifugal pump")
3. **Adaptive Chunking:** Use sentence boundaries + semantic similarity to avoid mid-clause splits
4. **Sparse Model Tuning:** Train custom sparse encoder on domain-specific vocabulary
5. **Cached Embeddings:** Store embeddings in Qdrant-native format + periodic snapshots
6. **Multi-Vector Ensembles:** Add keyword, semantic, and domain-specific vector types

---

**Last Updated:** 2025-09-13  
**System:** AegisAI Sovereign Workbench v1.0
