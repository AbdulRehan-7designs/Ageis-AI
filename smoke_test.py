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

FIXTURES = [
    ("sample_public.pdf", "Public SOP Directive", "PUBLIC"),
    ("sample_internal.pdf", "Internal Operations Manual", "INTERNAL"),
    ("sample_restricted.pdf", "Restricted Defense Directive", "RESTRICTED"),
    ("sample_secret.pdf", "Secret Sovereign Protocol", "SECRET"),
]

print("=== 1. INGESTING 4-TIER CLEARANCE FIXTURES ===")
for filename, doc_name, tag in FIXTURES:
    pdf_path = os.path.join(BASE_DIR, "test_data", filename)
    stats = ingestion_service.ingest_pdf(
        pdf_path=pdf_path,
        doc_name=doc_name,
        classification_tag=tag,
    )
    print(f"Ingested [{tag}] '{doc_name}': {stats['total_chunks']} chunks upserted.")

query = "defense clearance guidelines and operational workflow"

# Tier 1: PUBLIC clearance user
print("\n=== 2. TESTING PUBLIC CLEARANCE RETRIEVAL ===")
pub_res = retrieval_service.retrieve(query=query, user_clearance=["PUBLIC"], top_k=10)
pub_tags = {r.classification_tag for r in pub_res}
print(f"PUBLIC User Results Count: {len(pub_res)} | Tags returned: {pub_tags}")
if pub_tags.issubset({"PUBLIC"}):
    print("[PASS] PUBLIC CLEARANCE PASSED: Only PUBLIC documents retrieved.")
else:
    print(f"[FAIL] SECURITY VIOLATION: Unauthorized tags {pub_tags - {'PUBLIC'}} leaked to PUBLIC user!")
    sys.exit(1)

# Tier 2: INTERNAL clearance user
print("\n=== 3. TESTING INTERNAL CLEARANCE RETRIEVAL ===")
int_res = retrieval_service.retrieve(query=query, user_clearance=["PUBLIC", "INTERNAL"], top_k=10)
int_tags = {r.classification_tag for r in int_res}
print(f"INTERNAL User Results Count: {len(int_res)} | Tags returned: {int_tags}")
if int_tags.issubset({"PUBLIC", "INTERNAL"}):
    print("[PASS] INTERNAL CLEARANCE PASSED: Only PUBLIC & INTERNAL documents retrieved.")
else:
    print(f"[FAIL] SECURITY VIOLATION: Unauthorized tags {int_tags - {'PUBLIC', 'INTERNAL'}} leaked to INTERNAL user!")
    sys.exit(1)

# Tier 3: RESTRICTED clearance user
print("\n=== 4. TESTING RESTRICTED CLEARANCE RETRIEVAL ===")
res_res = retrieval_service.retrieve(query=query, user_clearance=["PUBLIC", "INTERNAL", "RESTRICTED"], top_k=10)
res_tags = {r.classification_tag for r in res_res}
print(f"RESTRICTED User Results Count: {len(res_res)} | Tags returned: {res_tags}")
if res_tags.issubset({"PUBLIC", "INTERNAL", "RESTRICTED"}):
    print("[PASS] RESTRICTED CLEARANCE PASSED: Only PUBLIC, INTERNAL, & RESTRICTED documents retrieved.")
else:
    print(f"[FAIL] SECURITY VIOLATION: Unauthorized tags {res_tags - {'PUBLIC', 'INTERNAL', 'RESTRICTED'}} leaked to RESTRICTED user!")
    sys.exit(1)

# Tier 4: SECRET clearance user
print("\n=== 5. TESTING SECRET CLEARANCE RETRIEVAL ===")
sec_res = retrieval_service.retrieve(query=query, user_clearance=["PUBLIC", "INTERNAL", "RESTRICTED", "SECRET"], top_k=10)
sec_tags = {r.classification_tag for r in sec_res}
print(f"SECRET User Results Count: {len(sec_res)} | Tags returned: {sec_tags}")
if "SECRET" in sec_tags and len(sec_tags) == 4:
    print("[PASS] SECRET CLEARANCE PASSED: All 4 clearance tiers accessible to SECRET user.")
else:
    print(f"[FAIL] RETRIEVAL FAILURE: SECRET user missing expected documents! Tags found: {sec_tags}")
    sys.exit(1)

print("\n🎉 ALL 4-TIER RAG RBAC CLEARANCE TESTS PASSED CLEANLY!")
