# Hybrid RAG design

Full reference: [`HYBRID_RAG_DESIGN.md`](../HYBRID_RAG_DESIGN.md). Summary below.

## Why hybrid

Dense vectors capture meaning but can miss exact identifiers such as `P-204`. Sparse BM25 captures those exact terms. Fusing both, then reranking, gives relevance and precision.

```mermaid
flowchart TB
    Q[Question] --> D[Dense: BGE-M3, 1024-d]
    Q --> S[Sparse: BM25]
    D --> F[RRF fusion in Qdrant, top 20]
    S --> F
    F --> C[Clearance filter]
    C --> R[Rerank: bge-reranker-v2-m3]
    R --> T[Top 5 with citations]
```

## Ingestion

1. Parse each PDF page with PyMuPDF.
2. Mark blocks above 1.3x the median font size as headers and store them as `section_title`.
3. Extract each table as one atomic chunk.
4. Chunk body text at 400 tokens with 50 overlap (about 4 characters per token).
5. Embed dense and sparse, upsert to Qdrant with metadata.

## Chunk payload

`chunk_id`, `doc_name`, `page`, `section_title`, `classification_tag`, `text`, `is_table`, `ingested_at`.

## Design-estimate latency

| Step | Estimate |
| --- | --- |
| Query embeddings (CPU) | ~15 ms |
| Prefetch + RRF in Qdrant | ~50 ms |
| Rerank top 20 (CPU) | ~100 ms |
| Total retrieval | ~165 ms |

These are design targets, not benchmarks. Measure on your hardware.
