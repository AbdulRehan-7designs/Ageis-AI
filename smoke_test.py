import os
import sys

# Set standard output encoding for windows console compatibility
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# Support relative import when running locally or in container
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from app.services.ingestion import ingestion_service
from app.services.retrieval import retrieval_service

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PUBLIC_PDF = os.path.join(BASE_DIR, "test_data", "sample_public.pdf")
RESTRICTED_PDF = os.path.join(BASE_DIR, "test_data", "sample_restricted.pdf")

print("=== 1. INGESTING TEST FIXTURES ===")
pub_stats = ingestion_service.ingest_pdf(
    pdf_path=PUBLIC_PDF,
    doc_name="Public Standard Operating Procedure",
    classification_tag="PUBLIC",
)
print(f"Public Doc Ingestion: {pub_stats['total_chunks']} chunks upserted.")

res_stats = ingestion_service.ingest_pdf(
    pdf_path=RESTRICTED_PDF,
    doc_name="Restricted Defense Directive",
    classification_tag="RESTRICTED",
)
print(f"Restricted Doc Ingestion: {res_stats['total_chunks']} chunks upserted.")

print("\n=== 2. TESTING PUBLIC CLEARANCE RETRIEVAL (Must Exclude RESTRICTED Docs) ===")
public_query = "tactical defense clearance guidelines"
public_results = retrieval_service.retrieve(
    query=public_query,
    user_clearance=["PUBLIC"],
    top_k=5,
)

print(f"Query: '{public_query}' | User Clearance: ['PUBLIC']")
print(f"Results Count: {len(public_results)}")
for r in public_results:
    print(f" - [{r.classification_tag}] {r.doc_name} (Page {r.page}): {r.text[:100]}")

# Strict assertion: No RESTRICTED doc should leak into a PUBLIC query
restricted_leaks = [r for r in public_results if r.classification_tag == "RESTRICTED"]
if restricted_leaks:
    print(f"[FAIL] SECURITY FAILURE: {len(restricted_leaks)} restricted document(s) leaked to PUBLIC user!")
    sys.exit(1)
else:
    print("[PASS] SECURITY PASSED: 0 Restricted documents leaked to PUBLIC user.")

print("\n=== 3. TESTING RESTRICTED CLEARANCE RETRIEVAL (Must Include RESTRICTED Docs) ===")
authorized_results = retrieval_service.retrieve(
    query=public_query,
    user_clearance=["PUBLIC", "INTERNAL", "RESTRICTED"],
    top_k=5,
)

print(f"Query: '{public_query}' | User Clearance: ['PUBLIC', 'INTERNAL', 'RESTRICTED']")
print(f"Results Count: {len(authorized_results)}")
for r in authorized_results:
    print(f" - [{r.classification_tag}] {r.doc_name} (Page {r.page}): {r.text[:100]}")

found_restricted = any(r.classification_tag == "RESTRICTED" for r in authorized_results)
if found_restricted:
    print("[PASS] AUTHORIZED RETRIEVAL PASSED: Restricted document successfully retrieved for authorized user.")
else:
    print("[FAIL] RETRIEVAL FAILURE: Authorized user failed to retrieve restricted document.")
    sys.exit(1)

print("\nALL RAG RBAC SMOKE TESTS PASSED CLEANLY!")
