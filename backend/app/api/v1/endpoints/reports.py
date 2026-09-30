from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from fastapi import Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from app.core.auth import User, get_current_user, require_role
from app.core.config import settings
from app.db.repository import find_artifact, save_artifact, update_artifact_status
from app.db.session import SessionLocal
from app.services.audit_service import audit_service
from app.services.report_service import CLASSIFICATION_RANK, report_service

router = APIRouter()


class MaintenanceReportRequest(BaseModel):
    asset: str = "N/A"
    issue_summary: str = ""
    diagnosis: str = ""
    findings: List[str] = Field(default_factory=list)
    recommended_action: Optional[Dict[str, Any]] = None
    evidence_blocks: List[Dict[str, Any]] = Field(default_factory=list)
    classification_level: str = "INTERNAL"
    hitl_approval_required: bool = False
    human_review_status: str = "PENDING"
    generated_by: str = "sovereign_operator"


class ReportSpecRequest(BaseModel):
    format: str
    title: str = "Aegis Engineering Report"
    report_type: str = "ENGINEERING_REPORT"
    asset: str | None = None
    executive_summary: str | None = None
    findings: list[Any] = Field(default_factory=list)
    evidence: list[dict[str, Any]] = Field(default_factory=list)
    possible_interpretation: str | None = None
    recommended_verification: str | None = None
    calculations: list[Any] = Field(default_factory=list)
    classification: str = "INTERNAL"
    agent_run_id: str | None = None
    operational_recommendation: str | None = None
    recommended_action: dict[str, Any] | None = None


@router.post("/reports/generate")
async def generate_report(request: ReportSpecRequest, current_user: User = Depends(get_current_user)):
    try:
        spec = request.model_dump()
        audit_started = audit_service.log_entry(
            event_type="REPORT_GENERATION_STARTED",
            username=current_user.username,
            clearance_tags=current_user.clearance_tags,
            query_or_action="Generate local engineering artifact",
            diagnosis_summary="Structured report generation started.",
            citations_count=len(spec["evidence"]),
            hitl_approval_required=bool(spec.get("recommended_verification") or spec.get("operational_recommendation") or spec.get("recommended_action")),
            equipment_tag=spec.get("asset") or "N/A",
            status="STARTED",
            run_id=spec.get("agent_run_id"),
        )
        result = report_service.generate(spec, current_user.username, current_user.clearance_tags, spec.get("agent_run_id"))
        completed = audit_service.log_entry(
            event_type="REPORT_GENERATION_COMPLETED",
            username=current_user.username,
            clearance_tags=current_user.clearance_tags,
            query_or_action=f"Generated artifact {result['artifact_id']}",
            diagnosis_summary="Local artifact generated from authorized structured evidence.",
            citations_count=result["source_count"],
            hitl_approval_required=result["status"] == "REVIEW_REQUIRED",
            equipment_tag=spec.get("asset") or "N/A",
            status=result["status"],
            run_id=spec.get("agent_run_id"),
            metadata={"artifact_id": result["artifact_id"], "content_hash": result["content_hash"], "format": result["format"]},
        )
        if result["status"] == "REVIEW_REQUIRED":
            audit_service.log_entry(
                event_type="REPORT_REVIEW_REQUIRED",
                username=current_user.username,
                clearance_tags=current_user.clearance_tags,
                query_or_action=f"Review artifact {result['artifact_id']}",
                diagnosis_summary="Operational recommendation requires human review.",
                citations_count=result["source_count"],
                hitl_approval_required=True,
                equipment_tag=spec.get("asset") or "N/A",
                status="REVIEW_REQUIRED",
                run_id=spec.get("agent_run_id"),
                metadata={"artifact_id": result["artifact_id"]},
            )
        result["audit_reference"] = completed["id"]
        with SessionLocal() as db:
            return save_artifact(db, result)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except Exception as exc:
        audit_service.log_entry(
            event_type="REPORT_GENERATION_FAILED",
            username=current_user.username,
            clearance_tags=current_user.clearance_tags,
            query_or_action="Generate local engineering artifact",
            diagnosis_summary=str(exc)[:200],
            status="FAILED",
        )
        raise HTTPException(status_code=400, detail="Report generation failed.") from exc


@router.get("/reports/{artifact_id}/download")
async def download_report(artifact_id: str, current_user: User = Depends(get_current_user)):
    with SessionLocal() as db:
        record = find_artifact(db, artifact_id)
        if record is None:
            raise HTTPException(status_code=404, detail="Artifact not found.")
        if not report_service.classification_allowed(record.classification, current_user.clearance_tags):
            raise HTTPException(status_code=403, detail="Artifact classification exceeds the user's clearance.")
        target = (report_service.root / record.storage_name).resolve()
        try:
            target.relative_to(report_service.root)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail="Artifact not found.") from exc
        if not target.is_file():
            raise HTTPException(status_code=404, detail="Artifact content is unavailable.")
        media = {"DOCX": "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "PDF": "application/pdf", "XLSX": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "PPTX": "application/vnd.openxmlformats-officedocument.presentationml.presentation"}[record.format]
        return FileResponse(target, media_type=media, filename=f"{artifact_id}.{record.format.lower()}")


@router.post("/reports/{artifact_id}/approve")
async def approve_report(artifact_id: str, current_user: User = Depends(require_role(["ADMIN", "ENGINEER"]))):
    with SessionLocal() as db:
        record = find_artifact(db, artifact_id)
        if record is None:
            raise HTTPException(status_code=404, detail="Artifact not found.")
        if not report_service.classification_allowed(record.classification, current_user.clearance_tags):
            raise HTTPException(status_code=403, detail="Artifact classification exceeds the reviewer's clearance.")
        if record.status not in {"DRAFT", "REVIEW_REQUIRED"}:
            raise HTTPException(status_code=409, detail="Artifact is not awaiting approval.")
        try:
            result = update_artifact_status(db, artifact_id, "APPROVED", {"reviewer": current_user.username, "reviewed_at": datetime.now(timezone.utc).isoformat()})
        except LookupError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
    audit_service.log_entry(
        event_type="REPORT_APPROVED",
        username=current_user.username,
        clearance_tags=current_user.clearance_tags,
        query_or_action=f"Approve artifact {artifact_id}",
        diagnosis_summary="Authorized reviewer approved the report artifact.",
        status="APPROVED",
        metadata={"artifact_id": artifact_id, "reviewer": current_user.username},
    )
    return result


@router.post("/reports/maintenance")
async def generate_maintenance_report(request: MaintenanceReportRequest, current_user: User = Depends(get_current_user)):
    """Deprecated compatibility endpoint; identity and classification come from the session."""
    report_id = f"REPORT-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"
    action = request.recommended_action or {}
    report_classification = max(
        (str(block.get("classification") or "INTERNAL").upper() for block in request.evidence_blocks),
        key=lambda value: CLASSIFICATION_RANK.get(value, 1),
        default="INTERNAL",
    )
    evidence_lines = []
    for index, block in enumerate(request.evidence_blocks, start=1):
        block_classification = str(block.get("classification") or "INTERNAL").upper()
        if not report_service.classification_allowed(block_classification, current_user.clearance_tags):
            raise HTTPException(status_code=403, detail="Report contains evidence above the user's clearance.")
        location = block.get("location") or {}
        location_label = f"Sheet {location.get('sheet')}" if location.get("sheet") else f"Page {location.get('page', 1)}"
        evidence_lines.append(
            f"{index}. {block.get('document', 'Source Document')} ({location_label}) "
            f"[{block_classification}] - {block.get('snippet', '')}"
        )

    report_text = "\n".join([
        "# AegisAI Maintenance Investigation Report",
        "",
        f"Report ID: {report_id}",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        f"Asset: {request.asset}",
        f"Classification: {report_classification}",
        "Human review status: REVIEW_REQUIRED",
        "",
        "## Issue Summary",
        request.issue_summary or "Not provided.",
        "",
        "## Diagnosis / Findings",
        request.diagnosis or "Not provided.",
        *[f"- {finding}" for finding in request.findings],
        "",
        "## Evidence Reviewed",
        *(evidence_lines or ["No evidence blocks were supplied."]),
        "",
        "## Recommended Actions",
        f"Title: {action.get('title', 'No action proposed')}",
        *[f"- {step}" for step in action.get("steps", [])],
        f"Approval required: {'Yes' if request.hitl_approval_required else 'No'}",
        "",
        "## Execution Control",
        "No operational command executed. This report is a recommendation artifact only.",
    ])

    audit_entry = audit_service.log_entry(
        event_type="REPORT_GENERATED",
        username=current_user.username,
        clearance_tags=current_user.clearance_tags,
        query_or_action=f"Generated maintenance report {report_id}",
        diagnosis_summary=request.diagnosis[:200],
        citations_count=len(request.evidence_blocks),
        hitl_approval_required=True,
        equipment_tag=request.asset,
        status="REVIEW_REQUIRED",
    )

    return {
        "report_id": report_id,
        "audit_id": audit_entry["id"],
        "filename": f"{report_id}.md",
        "content_type": "text/markdown",
        "classification_level": report_classification,
        "content": report_text,
    }
