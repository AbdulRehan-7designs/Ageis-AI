# Aegis AI — RAG Evaluation Plan

> **Status:** Evaluation protocol only. No benchmark scores are reported in this document. Run the protocol and record measured results before publishing quality claims.

## Goal

Measure whether Aegis AI retrieves the right engineering evidence and produces answers that are supported by that evidence. A working RAG pipeline is not, by itself, evidence of retrieval quality or answer correctness.

## 1. Build a small, safe evaluation set

Start with 30–50 questions over public, synthetic, or explicitly approved test documents. Do not upload confidential plant documents or personal data into a public benchmark.

Store one row per query in a CSV/JSONL file with these fields:

| Field | Meaning |
|---|---|
| `case_id` | Stable test-case identifier |
| `query` | User question |
| `user_role` | Test role/clearance |
| `expected_document` | Expected source document |
| `expected_pages` | Relevant page number(s) |
| `relevant_chunk_ids` | Relevant chunk IDs, if known |
| `expected_facts` | Facts a correct answer must contain |
| `must_refuse` | Whether the request should be denied or answered as unknown |

Include a balanced mix:

- Exact equipment-tag lookup
- Specification/value lookup
- Questions requiring evidence from more than one page
- Drawing/P&ID label lookup
- OCR-heavy or table-heavy pages
- Ambiguous questions
- Questions with no answer in the indexed documents
- Requests for documents outside the user's clearance

## 2. Compare retrieval configurations

Use the same documents, queries, filters, and top-K value for each run.

| Run | Retrieval configuration |
|---|---|
| A | Dense retrieval only |
| B | Sparse/BM25 retrieval only |
| C | Hybrid dense + sparse retrieval with reciprocal-rank fusion |
| D | Hybrid retrieval + cross-encoder reranking |

Record the model/version, embedding model, chunk size/overlap, top-K, filters, and reranker configuration for every run.

## 3. Retrieval metrics

For each query, manually label the relevant retrieved chunks before calculating metrics.

- **Recall@K:** relevant chunks retrieved in the top K divided by all known relevant chunks.
- **Precision@K:** relevant chunks retrieved in the top K divided by K.
- **MRR:** reciprocal rank of the first relevant result, averaged over queries.
- **Citation source accuracy:** proportion of answer citations that point to the correct source document and page.

Report macro averages across the full evaluation set and break results down by query type. Do not calculate metrics from unlabelled or guessed relevance.

## 4. Answer-quality review

Review each generated answer against the source documents. Score each dimension as Pass / Partial / Fail:

1. **Evidence support:** every material factual claim is supported by retrieved source evidence.
2. **Citation correctness:** cited document and page actually support the nearby claim.
3. **Completeness:** all required facts are included without adding unsupported details.
4. **Uncertainty handling:** the assistant says when evidence is missing or ambiguous.
5. **Access control:** restricted documents are not exposed to a user without the required clearance.

A citation being present does not automatically mean the answer is grounded.

## 5. Performance and reliability

For each configuration, record:

- End-to-end latency (p50 and p95)
- Retrieval latency
- Generation latency
- Failed requests / timeouts
- Model and embedding versions
- Hardware/runtime configuration
- Memory use where practical

Run repeated trials and keep the environment consistent. Report the number of queries and trials alongside every metric.

## 6. Results table — fill only after running

| Configuration | Recall@5 | Precision@5 | MRR | Citation accuracy | p50 latency | p95 latency |
|---|---:|---:|---:|---:|---:|---:|
| Dense only | Not measured | Not measured | Not measured | Not measured | Not measured | Not measured |
| Sparse only | Not measured | Not measured | Not measured | Not measured | Not measured | Not measured |
| Hybrid | Not measured | Not measured | Not measured | Not measured | Not measured | Not measured |
| Hybrid + reranker | Not measured | Not measured | Not measured | Not measured | Not measured | Not measured |

## 7. Release gate

Before presenting a benchmark or using a quality claim in a resume/demo:

- [ ] Evaluation questions and expected evidence are reviewed by a human.
- [ ] The dataset uses safe, shareable documents.
- [ ] All four retrieval configurations have been run under documented settings.
- [ ] Scores are calculated from labelled relevance judgments.
- [ ] Citation correctness and access-control cases are manually checked.
- [ ] Failures and limitations are documented.
- [ ] Results can be reproduced from the documented commands/configuration.

## Interpretation

Treat this as a repeatable engineering evaluation, not a marketing exercise. If the current application does not expose a stable way to capture retrieved chunks and citations, add that instrumentation before calculating retrieval metrics.
