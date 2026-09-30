import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.identifiers import (
    expand_identifier_query,
    extract_identifiers,
    normalize_identifier,
    tags_from_chunks_text,
)
from app.services.query_router import query_router

try:
    from app.services.rag_service import RAGService
except ImportError:
    RAGService = None

try:
    from app.services.ingestion import IngestionService
except ImportError:
    IngestionService = None

try:
    from app.services.retrieval import RetrievalResult, RetrievalService
except ImportError:
    RetrievalResult = None
    RetrievalService = None


class TestIdentifiers(unittest.TestCase):
    def test_normalizes_compact_and_spaced_tags(self):
        self.assertEqual(normalize_identifier("p204"), "P-204")
        self.assertEqual(normalize_identifier("PSV 204"), "PSV-204")
        self.assertEqual(normalize_identifier("sop-017"), "SOP-017")

    def test_extracts_multiple_tags(self):
        tags = extract_identifiers("Where is PSV-204 on the line from P-204?")
        self.assertEqual(tags, ["PSV-204", "P-204"])

    def test_chunk_payload_stores_variants(self):
        variants = tags_from_chunks_text("Isolate P-204 before opening PSV-204.")
        self.assertIn("P-204", variants)
        self.assertIn("P204", variants)
        self.assertIn("PSV-204", variants)

    def test_expand_query_includes_variants(self):
        expanded = expand_identifier_query("diagnose p-204 vibration")
        self.assertIn("P-204", expanded)
        self.assertIn("P204", expanded)


class TestQueryRouterIdentifiers(unittest.TestCase):
    def test_route_exposes_identifiers(self):
        route = query_router.route("Where is PSV-204 on the P&ID drawing?")
        self.assertEqual(route["identifiers"], ["PSV-204"])
        self.assertIn("identifier", route["strategy"])

    def test_asset_maintenance_query_keeps_maintenance_intent(self):
        route = query_router.route("What is the vibration limit of P-204?")
        self.assertEqual(route["intent"], "maintenance")
        self.assertEqual(route["strategy"], "identifier")
        self.assertEqual(route["identifiers"], ["P-204"])
        self.assertEqual(route["asset"], "P-204")
        self.assertEqual(route["related_identifiers"], [])
        self.assertEqual(route["search_strategy"], "exact_identifier_plus_semantic")

    def test_identifier_only_query_is_asset_lookup(self):
        route = query_router.route("Show me everything related to PSV-204")
        self.assertEqual(route["intent"], "asset_lookup")
        self.assertEqual(route["strategy"], "identifier")


@unittest.skipUnless(RetrievalService and RetrievalResult, "retrieval stack not installed")
class TestHybridFusion(unittest.TestCase):
    def test_identifier_hits_outrank_dense_only(self):
        service = RetrievalService()
        ident = RetrievalResult("id-1", "a.pdf", 1, "s", "INTERNAL", "P-204 vibration log")
        dense = RetrievalResult("id-2", "b.pdf", 1, "s", "INTERNAL", "general pump notes")
        fused = service._rrf_fusion(
            [{"chunk_id": "id-2", "result": dense}],
            [],
            [{"chunk_id": "id-1", "result": ident}],
        )
        self.assertEqual(fused[0].chunk_id, "id-1")

    def test_object_tag_prefers_first_real_identifier(self):
        tag = RetrievalService._extract_object_tag("Pump P-204 tripped; PSV-204 lifted.")
        self.assertEqual(tag, "P-204")

    @unittest.skipUnless(RAGService, "rag service not installed")
    def test_build_rag_context_accepts_generator_embedding_output(self):
        class FakeEmbedder:
            def embed(self, texts):
                yield (value for value in [0.11, 0.22, 0.33])

        service = RAGService.__new__(RAGService)
        service.collection = "industrial_docs"
        service.client = object()
        service.retrieval = RetrievalService()
        service._embedder = FakeEmbedder()
        service._query_vector_collection = lambda *, vector, allowed_tags, top_k: []

        result = service.build_rag_context("diagnose P-204 vibration", ["INTERNAL"], top_k=2)
        self.assertIn("citations", result)
        self.assertIn("context_text", result)
        self.assertIn("retrieval_trace", result)
        self.assertTrue(any(item["stage"] == "query_classified" for item in result["retrieval_trace"]))
        self.assertEqual(service._coerce_embedding_vector(service._embedder.embed(["probe"])), [0.11, 0.22, 0.33])


@unittest.skipUnless(IngestionService, "ingestion stack not installed")
class TestSparseVectorBuilder(unittest.TestCase):
    def test_sparse_vector_builder_accepts_indices_values(self):
        class FakeSparse:
            indices = [1, 7, 9]
            values = [0.2, 0.8, 0.1]

        vec = IngestionService._build_sparse_vector(IngestionService, FakeSparse())
        self.assertEqual(list(vec.indices), [1, 7, 9])
        self.assertEqual(list(vec.values), [0.2, 0.8, 0.1])


if __name__ == "__main__":
    unittest.main()
