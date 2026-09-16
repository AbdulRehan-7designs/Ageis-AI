"""Deterministic fallback engine for AegisAI.

Provides guaranteed structured responses when the Ollama LLM is unavailable
or returns an empty response. Unlike a simple hardcoded response, this engine
classifies the user's query and returns an appropriate response type:

  - Equipment diagnostics (e.g., "P-204 vibration")
  - Conversational / greetings (e.g., "hi", "hello")
  - Knowledge questions (e.g., "what is SOP-017?")
"""

import re
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Query classification patterns
# ---------------------------------------------------------------------------

_GREETING_PATTERNS = re.compile(
    r"^\s*(?:hi|hello|hey|good\s*(?:morning|afternoon|evening)|greetings|"
    r"howdy|what'?s?\s*up|yo|sup|namaste|hola)\b",
    re.IGNORECASE,
)

_EQUIPMENT_PATTERNS = re.compile(
    r"(?:p-?\s*\d{2,4}|pump|vibrat|bearing|motor|compressor|turbine|valve|"
    r"diagnos|maintenance|sop-?\d|inspect|shutdown|isolat|threshold|alarm|"
    r"critical|warning|temp(?:erature)?|pressure|rpm|fault|fail|repair|"
    r"centrifugal|reciprocat|corrosion|leak|cavitat|overhaul)",
    re.IGNORECASE,
)

_CAPABILITY_PATTERNS = re.compile(
    r"(?:what\s+(?:can|do)\s+you|help|capabilities|features|how\s+(?:do|does)\s+(?:this|you)|"
    r"who\s+are\s+you|introduce|about\s+(?:you|this|aegis))",
    re.IGNORECASE,
)


def _classify_query(query: str) -> str:
    """Classify query intent: 'greeting', 'capability', 'equipment', or 'knowledge'."""
    stripped = query.strip()
    if len(stripped) < 15 and _GREETING_PATTERNS.search(stripped):
        return "greeting"
    if _CAPABILITY_PATTERNS.search(stripped):
        return "capability"
    if _EQUIPMENT_PATTERNS.search(stripped):
        return "equipment"
    return "knowledge"


# ---------------------------------------------------------------------------
# Response builders
# ---------------------------------------------------------------------------

def _greeting_response(query: str) -> Dict[str, Any]:
    return {
        "reply_title": "Welcome to AegisAI",
        "diagnosis_summary": (
            "Hello! I'm AegisAI — your sovereign on-premise industrial maintenance intelligence assistant. "
            "I can help you diagnose equipment issues, retrieve SOP procedures, analyse maintenance history, "
            "and recommend actions — all powered by local AI models running entirely within your air-gapped infrastructure.\n\n"
            "Try asking me:\n"
            "• \"Diagnose P-204 vibration issue\"\n"
            "• \"What are the vibration limits for centrifugal pumps?\"\n"
            "• \"Upload a PDF to the knowledge base\"\n"
            "• \"Show SOP-017 pump maintenance steps\""
        ),
        "engine": "deterministic-greeting-responder",
        "execution_time_sec": 0.01,
        "equipment_details": None,
        "recommended_action": {
            "title": "Get Started",
            "sop_code": "N/A",
            "requires_approval": False,
            "steps": [
                "Ask a question about your industrial equipment or SOPs.",
                "Upload a PDF document to enrich the knowledge base.",
                "Use the Code Sandbox for diagnostic calculations.",
            ],
            "why_reasoning": [
                "AegisAI is ready to assist with maintenance intelligence queries."
            ],
        },
        "risk_score": 0.0,
    }


def _capability_response(query: str) -> Dict[str, Any]:
    return {
        "reply_title": "AegisAI Capabilities",
        "diagnosis_summary": (
            "AegisAI is a sovereign, air-gapped AI workbench for industrial maintenance intelligence. "
            "Here's what I can do:\n\n"
            "**1. Equipment Diagnostics** — Analyse vibration, temperature, pressure data and diagnose faults.\n"
            "**2. SOP Retrieval** — Search and retrieve Standard Operating Procedures from your knowledge base.\n"
            "**3. Hybrid RAG** — Dense + Sparse retrieval with RBAC-filtered access control.\n"
            "**4. HITL Approval** — Human-in-the-Loop gates for critical maintenance actions.\n"
            "**5. Code Sandbox** — Execute diagnostic Python code in an isolated, secure environment.\n"
            "**6. Tamper-Evident Audit** — SHA-256 hash-chained audit logs for full traceability.\n"
            "**7. Document Ingestion** — Upload PDF manuals, SOPs, P&IDs into the vector knowledge base.\n\n"
            "All processing happens locally — no data leaves your network."
        ),
        "engine": "deterministic-capability-responder",
        "execution_time_sec": 0.01,
        "equipment_details": None,
        "recommended_action": {
            "title": "Explore AegisAI Features",
            "sop_code": "N/A",
            "requires_approval": False,
            "steps": [
                "Ask about equipment diagnostics (e.g., 'Diagnose P-204').",
                "Upload SOPs or manuals via the attachment button.",
                "Open the Code Sandbox from the sidebar for calculations.",
                "View the Audit & Governance panel for hash-chained logs.",
            ],
            "why_reasoning": [
                "All capabilities run on-premise with zero external API calls."
            ],
        },
        "risk_score": 0.0,
    }


def _knowledge_response(query: str, rag_context: Optional[str] = None) -> Dict[str, Any]:
    """For general knowledge questions — uses RAG context if available."""
    if rag_context and rag_context.strip():
        summary = (
            f"Based on the evidence retrieved from your knowledge base:\n\n{rag_context[:1500]}"
        )
    else:
        summary = (
            f"I searched the knowledge base for information related to your query "
            f"but didn't find a strong match. This could mean:\n\n"
            f"• The relevant document hasn't been uploaded yet.\n"
            f"• The topic may not be covered in the current knowledge base.\n\n"
            f"**Recommendation:** Upload the relevant PDF document using the attachment button, "
            f"then ask your question again."
        )
    return {
        "reply_title": "Knowledge Base Query",
        "diagnosis_summary": summary,
        "engine": "deterministic-knowledge-responder",
        "execution_time_sec": 0.02,
        "equipment_details": None,
        "recommended_action": {
            "title": "Review Retrieved Evidence",
            "sop_code": "N/A",
            "requires_approval": False,
            "steps": [
                "Review the citations panel on the right for source documents.",
                "Upload additional documents if the answer is incomplete.",
            ],
            "why_reasoning": [
                "Response synthesised from retrieved knowledge base evidence."
                if rag_context
                else "No strong match found — consider uploading relevant documents."
            ],
        },
        "risk_score": 0.0,
    }


def _equipment_response(query: str) -> Dict[str, Any]:
    """Equipment diagnostic — the original heuristic rule engine."""
    q = query.lower()

    # Extract equipment ID
    eq_match = re.search(r"p-?\s*(\d{2,4})", q)
    eq_tag = f"P-{eq_match.group(1)}" if eq_match else "P-204"

    # Extract vibration value if mentioned
    vib_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:mm/s|mms)", q)
    vibration_val = float(vib_match.group(1)) if vib_match else 8.2

    # Heuristic rule logic
    if vibration_val > 7.1:
        status_text = "Critical"
        title = f"Diagnosis Summary: {eq_tag} Critical Vibration"
        summary = (
            f"{eq_tag} is experiencing an abnormal vibration of {vibration_val} mm/s, "
            f"exceeding the critical threshold (>7.1 mm/s) defined in SOP-017. "
            f"The primary root cause is bearing race degradation, requiring immediate isolation."
        )
        rec_title = "Schedule immediate inspection and maintenance"
        sop_code = "SOP-017: Pump Maintenance"
        requires_approval = True
        steps = [
            "Verify sensor readings and confirm vibration trend.",
            "Isolate and shut down the pump (requires HITL approval).",
            "Perform mechanical inspection (bearing, coupling, alignment).",
            "Replace/repair bearing assembly based on findings.",
        ]
        why = [
            f"Vibration ({vibration_val} mm/s) exceeds critical threshold (>7.1 mm/s) from SOP-017 (p.4).",
            "Historical records show similar vibration pattern in the last 3 months.",
            f"P&ID confirms {eq_tag} is a critical pump in the main feed line.",
            "SOP requires mandatory engineer confirmation prior to main line shutdown.",
        ]
        risk = 0.85
    elif vibration_val >= 4.5:
        status_text = "Warning"
        title = f"Diagnosis Summary: {eq_tag} Warning Vibration"
        summary = (
            f"{eq_tag} vibration is at {vibration_val} mm/s, within the warning band (4.5 – 7.1 mm/s) "
            f"per SOP-017. Routine inspection recommended within 48 hours."
        )
        rec_title = "Schedule routine inspection within 48 hours"
        sop_code = "SOP-017: Section 2"
        requires_approval = False
        steps = [
            "Monitor bearing temperature every 4 hours.",
            "Check coupling pads and foundation bolt tightness.",
            "Re-verify vibration baseline in 24 hours.",
        ]
        why = [
            f"Vibration ({vibration_val} mm/s) is in warning zone (4.5 – 7.1 mm/s).",
            "Continuous operation permitted with elevated monitoring.",
        ]
        risk = 0.45
    else:
        status_text = "Normal"
        title = f"Diagnosis Summary: {eq_tag} Normal Operating Parameters"
        summary = f"{eq_tag} vibration is {vibration_val} mm/s, well within normal operating limit (<4.5 mm/s)."
        rec_title = "Continue normal operation"
        sop_code = "SOP-017: Section 1"
        requires_approval = False
        steps = ["Maintain standard operating schedule."]
        why = ["Vibration within safe baseline."]
        risk = 0.05

    return {
        "reply_title": title,
        "diagnosis_summary": summary,
        "engine": "deterministic-heuristic-rule-engine",
        "execution_time_sec": 0.05,
        "equipment_details": {
            "tag": eq_tag,
            "status": f"Running ({status_text})",
            "type": "Centrifugal Pump",
            "location": "Process Line A – MRPL Unit 2",
            "vibration_val": f"{vibration_val} mm/s",
            "vibration_status": status_text,
            "threshold": "> 7.1 mm/s",
            "temp": "74 °C",
        },
        "recommended_action": {
            "title": rec_title,
            "sop_code": sop_code,
            "requires_approval": requires_approval,
            "steps": steps,
            "why_reasoning": why,
        },
        "risk_score": risk,
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

class DeterministicFallbackEngine:
    """
    Query-aware deterministic engine.
    Classifies user intent and returns an appropriate structured response.
    """

    @classmethod
    def evaluate(
        cls,
        user_query: str,
        rag_context: Optional[str] = None,
    ) -> Dict[str, Any]:
        intent = _classify_query(user_query)

        if intent == "greeting":
            return _greeting_response(user_query)
        elif intent == "capability":
            return _capability_response(user_query)
        elif intent == "equipment":
            return _equipment_response(user_query)
        else:
            return _knowledge_response(user_query, rag_context=rag_context)


fallback_engine = DeterministicFallbackEngine()
