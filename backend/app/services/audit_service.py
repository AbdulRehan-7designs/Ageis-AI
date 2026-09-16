"""Tamper-Evident Audit Logging Service for AegisAI.

Provides cryptographic SHA-256 hash-chaining for audit trails of chat queries
and HITL approval events. Every record includes the hash of the preceding entry,
forming an immutable, verifiable chain anchored at a fixed genesis block.
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

logger = logging.getLogger(__name__)

GENESIS_HASH = "GENESIS_SOVEREIGN_ANCHOR_00000000000000000000000000000000"


class AuditRecord(BaseModel):
    id: str
    timestamp: str
    event_type: str  # "CHAT_QUERY" or "HITL_APPROVAL"
    username: str
    clearance_tags: List[str]
    query_or_action: str
    diagnosis_summary: str
    citations_count: int
    hitl_approval_required: bool
    equipment_tag: str
    status: str
    previous_hash: str
    entry_hash: str
    integrity_hash: Optional[str] = None


class AuditService:
    def __init__(self) -> None:
        self._store: List[Dict[str, Any]] = []

    def clear(self) -> None:
        """Reset the audit store (primarily for testing)."""
        self._store.clear()

    def get_logs(self) -> List[Dict[str, Any]]:
        """Return all logged audit records."""
        return list(self._store)

    @property
    def store(self) -> List[Dict[str, Any]]:
        """Direct reference to underlying storage list (for testing/tampering checks)."""
        return self._store

    def _compute_entry_hash(
        self,
        previous_hash: str,
        entry_payload: Dict[str, Any],
    ) -> str:
        """Compute SHA-256 hash chaining previous_hash with deterministic entry payload."""
        # Exclude hash fields from payload to prevent circular reference
        payload = {
            k: v
            for k, v in entry_payload.items()
            if k not in ("entry_hash", "integrity_hash")
        }
        serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        to_hash = f"{previous_hash}:{serialized}"
        return hashlib.sha256(to_hash.encode("utf-8")).hexdigest()

    def log_entry(
        self,
        event_type: str,
        username: str,
        clearance_tags: List[str],
        query_or_action: str,
        diagnosis_summary: str = "",
        citations_count: int = 0,
        hitl_approval_required: bool = False,
        equipment_tag: str = "N/A",
        status: str = "LOGGED",
    ) -> Dict[str, Any]:
        """Create, hash-chain, and store a new audit record."""
        entry_id = f"AUDIT-{len(self._store) + 1001}"
        timestamp_str = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())

        previous_hash = (
            self._store[-1]["entry_hash"] if self._store else GENESIS_HASH
        )

        entry_dict = {
            "id": entry_id,
            "timestamp": timestamp_str,
            "event_type": event_type,
            "username": username,
            "clearance_tags": clearance_tags,
            "query_or_action": query_or_action,
            "diagnosis_summary": diagnosis_summary,
            "citations_count": citations_count,
            "hitl_approval_required": hitl_approval_required,
            "equipment_tag": equipment_tag,
            "status": status,
            "previous_hash": previous_hash,
        }

        entry_hash = self._compute_entry_hash(previous_hash, entry_dict)
        entry_dict["entry_hash"] = entry_hash
        entry_dict["integrity_hash"] = entry_hash

        self._store.append(entry_dict)
        logger.info("Audit entry logged: id=%s hash=%s...", entry_id, entry_hash[:12])
        return entry_dict

    def verify_audit_chain(self) -> Dict[str, Any]:
        """Verify integrity of the audit log hash chain.

        Returns:
            {
                "is_valid": bool,
                "total_entries": int,
                "broken_index": Optional[int],
                "broken_entry_id": Optional[str],
                "reason": Optional[str],
            }
        """
        if not self._store:
            return {
                "is_valid": True,
                "total_entries": 0,
                "broken_index": None,
                "broken_entry_id": None,
                "reason": "Audit log is empty.",
            }

        expected_prev_hash = GENESIS_HASH

        for idx, entry in enumerate(self._store):
            entry_id = entry.get("id", f"INDEX-{idx}")

            # 1. Check previous_hash link
            stored_prev_hash = entry.get("previous_hash")
            if stored_prev_hash != expected_prev_hash:
                return {
                    "is_valid": False,
                    "total_entries": len(self._store),
                    "broken_index": idx,
                    "broken_entry_id": entry_id,
                    "reason": (
                        f"Chain break at index {idx} ({entry_id}): previous_hash mismatch. "
                        f"Expected '{expected_prev_hash}', got '{stored_prev_hash}'."
                    ),
                }

            # 2. Recompute entry_hash from content fields
            recomputed_hash = self._compute_entry_hash(stored_prev_hash, entry)
            stored_entry_hash = entry.get("entry_hash")

            if stored_entry_hash != recomputed_hash:
                return {
                    "is_valid": False,
                    "total_entries": len(self._store),
                    "broken_index": idx,
                    "broken_entry_id": entry_id,
                    "reason": (
                        f"Content tamper detected at index {idx} ({entry_id}): entry_hash mismatch. "
                        f"Computed '{recomputed_hash}', stored '{stored_entry_hash}'."
                    ),
                }

            expected_prev_hash = stored_entry_hash

        return {
            "is_valid": True,
            "total_entries": len(self._store),
            "broken_index": None,
            "broken_entry_id": None,
            "reason": f"All {len(self._store)} entries in the hash chain are valid and intact.",
        }


audit_service = AuditService()
