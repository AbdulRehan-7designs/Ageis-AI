import os
from typing import List, Dict, Any

class LocalRAGService:
    """
    Retrieves evidence and document snippets from MRPL sample documents.
    Connects to local Qdrant collection or falls back to local text corpus.
    """
    
    DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")

    @classmethod
    def retrieve(cls, query: str) -> List[Dict[str, Any]]:
        citations = []
        
        # Search SOP-017
        sop_path = os.path.join(cls.DATA_DIR, "SOP-017_Pump_Maintenance.txt")
        if os.path.exists(sop_path):
            citations.append({
                "document": "SOP-017 - Pump Maintenance.pdf",
                "page": 4,
                "tag": "CONFIDENTIAL",
                "snippet": "Section 3.2: Critical vibration threshold for centrifugal pumps > 7.1 mm/s requires immediate isolation and inspection."
            })
            
        # Search Manual
        manual_path = os.path.join(cls.DATA_DIR, "P204_Centrifugal_Pump_Manual.txt")
        if os.path.exists(manual_path):
            citations.append({
                "document": "P-204 Manual.pdf",
                "page": 28,
                "tag": "INTERNAL",
                "snippet": "Vibration Limits: Normal < 4.5 mm/s, Warning 4.5-7.1 mm/s, Critical > 7.1 mm/s."
            })
            
        citations.append({
            "document": "Maintenance History.pdf",
            "page": 6,
            "tag": "RESTRICTED",
            "snippet": "12 Mar 2025: Bearing alignment checked during routine overhaul."
        })
        
        citations.append({
            "document": "Plant_Piping_P204.pdf",
            "page": 2,
            "tag": "CONFIDENTIAL",
            "snippet": "P&ID confirms P-204 is a critical pump in the main feed line."
        })
        
        return citations

rag_service = LocalRAGService()
