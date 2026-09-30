import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.ingestion import IngestionService
from app.services.retrieval import RetrievalService, RetrievalResult


class TestCitationMetadata(unittest.TestCase):
    def test_engineering_drawing_citation_has_unified_metadata(self):
        service = RetrievalService()
        result = RetrievalResult(
            chunk_id="drawing_chunk_1",
            doc_name="P204_PandID_RevC.pdf",
            page=2,
            section_title="Process Area",
            classification_tag="INTERNAL",
            text="PSV-204 discharges to flare header",
            stored_filename="doc_123.pdf",
            bbox=[4832, 2170, 5012, 2290],
            page_width=6000,
            page_height=4200,
        )

        citations = service.to_citation_dicts([result])
        self.assertEqual(len(citations), 1)
        citation = citations[0]

        self.assertEqual(citation["document_type"], "engineering_drawing")
        self.assertEqual(citation["drawing_type"], "P&ID")
        self.assertEqual(citation["sheet"], 2)
        self.assertEqual(citation["object_tag"], "PSV-204")
        self.assertEqual(citation["target"]["type"], "equipment")
        self.assertEqual(citation["target"]["tag"], "PSV-204")
        self.assertEqual(citation["geometry"]["type"], "bbox")
        self.assertEqual(citation["location"]["sheet"], 2)

    def test_technical_document_citation_remains_pdf_compatible(self):
        service = RetrievalService()
        result = RetrievalResult(
            chunk_id="doc_chunk_1",
            doc_name="SOP-017_Pump_Maintenance.pdf",
            page=4,
            section_title="Maintenance Limits",
            classification_tag="CONFIDENTIAL",
            text="Pump vibration threshold is 7.1 mm/s",
            stored_filename="doc_456.pdf",
            bbox=[120, 200, 450, 300],
            page_width=612,
            page_height=792,
        )

        citations = service.to_citation_dicts([result])
        self.assertEqual(len(citations), 1)
        citation = citations[0]
        self.assertEqual(citation["document_type"], "technical_document")
        self.assertEqual(citation["location"]["page"], 4)
        self.assertEqual(citation["geometry"]["type"], "bbox")

    def test_ingestion_infers_drawing_metadata_for_pid_files(self):
        service = IngestionService()
        meta = service._infer_document_metadata("P204_PandID_RevC.pdf", "PSV-204 discharges to flare header")
        self.assertEqual(meta["document_type"], "engineering_drawing")
        self.assertEqual(meta["drawing_type"], "P&ID")
        self.assertEqual(meta["sheet"], 1)
        self.assertEqual(meta["object_tag"], "PSV-204")
        self.assertEqual(meta["target"]["tag"], "PSV-204")

    def test_ingestion_does_not_misclassify_general_docs_that_mention_drawings(self):
        service = IngestionService()
        meta = service._infer_document_metadata(
            "SIH26117.pdf",
            "The system processes engineering drawings and maintenance records on-premise.",
        )
        self.assertEqual(meta["document_type"], "technical_document")

        pid_reference = service._infer_document_metadata(
            "generic_manual.pdf",
            "This manual references P&ID diagrams twice but is not a drawing package.",
        )
        self.assertEqual(pid_reference["document_type"], "technical_document")

    def test_ingestion_result_exposes_document_metadata_summary(self):
        service = IngestionService()
        path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "test_data", "sample_internal.pdf")
        stats = service.ingest_pdf(
            pdf_path=path,
            doc_name="P204_PandID_RevC.pdf",
            classification_tag="INTERNAL",
        )

        self.assertIn("metadata", stats)
        self.assertEqual(stats["metadata"]["document_type"], "engineering_drawing")
        self.assertEqual(stats["metadata"]["drawing_type"], "P&ID")
        self.assertEqual(stats["metadata"]["source_kind"], "drawing_sheet")
        self.assertGreater(stats["page_count"], 0)
        self.assertGreater(stats["metadata"]["chunk_count"], 0)
        self.assertTrue(stats["metadata"]["evidence_ready"])

    def test_document_listing_exposes_document_metadata(self):
        service = IngestionService()
        path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "test_data", "sample_internal.pdf")
        service.ingest_pdf(
            pdf_path=path,
            doc_name="P204_PandID_RevC.pdf",
            classification_tag="INTERNAL",
        )
        docs = service.list_documents()
        self.assertTrue(any(doc.get("document_name") == "P204_PandID_RevC.pdf" for doc in docs))
        match = next(doc for doc in docs if doc.get("document_name") == "P204_PandID_RevC.pdf")
        self.assertEqual(match.get("document_type"), "engineering_drawing")
        self.assertEqual(match.get("drawing_type"), "P&ID")
        self.assertEqual(match.get("source_kind"), "drawing_sheet")
        self.assertNotIn("PSV-204", match.get("equipment_tags", []))

    def test_citation_exposes_canonical_document_alias_for_frontend(self):
        service = RetrievalService()
        result = RetrievalResult(
            chunk_id="drawing_chunk_2",
            doc_name="P204_PandID_RevC.pdf",
            page=3,
            section_title="Relief Device",
            classification_tag="INTERNAL",
            text="PSV-204 relief valve is on the flare header",
            stored_filename="doc_789.pdf",
            bbox=[100, 120, 240, 200],
            page_width=500,
            page_height=700,
        )

        citations = service.to_citation_dicts([result])
        self.assertEqual(len(citations), 1)
        citation = citations[0]
        self.assertEqual(citation["document"], "P204_PandID_RevC.pdf")
        self.assertEqual(citation["document_name"], "P204_PandID_RevC.pdf")
        self.assertEqual(citation["tag"], "INTERNAL")
        self.assertEqual(citation["object_tag"], "PSV-204")

    def test_citation_exposes_asset_lineage_metadata(self):
        service = RetrievalService()
        result = RetrievalResult(
            chunk_id="drawing_chunk_3",
            doc_name="P204_PandID_RevC.pdf",
            page=5,
            section_title="Relief Device",
            classification_tag="INTERNAL",
            text="PSV-204 relief valve discharges to flare header",
            stored_filename="doc_999.pdf",
            bbox=[150, 200, 260, 260],
            page_width=600,
            page_height=800,
            metadata={"equipment_tags": ["PSV204", "P-204"]},
        )

        citations = service.to_citation_dicts([result])
        self.assertEqual(len(citations), 1)
        citation = citations[0]
        self.assertEqual(citation["asset_lineage"]["equipment_tag"], "PSV-204")
        self.assertEqual(citation["asset_lineage"]["document_type"], "engineering_drawing")
        self.assertEqual(citation["asset_lineage"]["drawing_type"], "P&ID")
        self.assertEqual(citation["asset_lineage"]["sheet"], 5)
        self.assertEqual(citation["asset_lineage"]["equipment_tags"], ["PSV-204", "P-204"])
        self.assertEqual(citation["asset_lineage"]["related_tags"], ["P-204"])
        self.assertEqual(citation["asset_lineage"]["source_kind"], "drawing_sheet")


if __name__ == "__main__":
    unittest.main()
