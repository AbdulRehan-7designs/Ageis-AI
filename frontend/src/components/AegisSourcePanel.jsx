import React, { useEffect, useState } from 'react';
import { FileText, ChevronRight, FileType2, Search, Eye, Activity, ShieldCheck, PanelRightClose, PanelRightOpen } from 'lucide-react';
import AegisAgentTrace from './AegisAgentTrace';
import AegisEvidenceViewer from './AegisEvidenceViewer';
import AegisDrawingNavigator from './AegisDrawingNavigator';
import { analyzeDocumentPage, generateMaintenanceReport, generateReportArtifact, reportArtifactUrl, submitHitlDecision } from '../services/api';

export default function AegisSourcePanel({ currentResponse, currentUser, systemHealth, egressSnapshot, citations = [], uploadedDocuments = [], selectedCitation, onSelectCitation, onSelectDocument }) {
  const trace = currentResponse?.reasoning_trace || [];
  const retrievalTrace = (currentResponse?.retrieval_trace || []).map((step, index) => ({
    step_number: index + 1,
    title: step.stage.replaceAll('_', ' '),
    description: step.detail,
    status: step.status,
  }));
  const uploadedSourceMap = (uploadedDocuments || []).map((document, index) => ({
    document: document.document_name || document.filename || `Document ${index + 1}`,
    document_name: document.document_name || document.filename || `Document ${index + 1}`,
    document_id: document.document_id,
    document_type: document.document_type || 'technical_document',
    drawing_type: document.drawing_type || null,
    object_tag: document.object_tag || '—',
    sheet: document.sheet || 1,
    page: document.page || 1,
    asset_lineage: {
      equipment_tag: document.object_tag || '—',
      equipment_tags: document.object_tag && document.object_tag !== '—' ? [document.object_tag] : [],
      related_tags: [],
      document_type: document.document_type || 'technical_document',
      drawing_type: document.drawing_type || null,
      sheet: document.sheet || 1,
      page: document.page || 1,
      document_name: document.document_name || document.filename || `Document ${index + 1}`,
      target_type: 'equipment',
      source_kind: document.document_type === 'engineering_drawing' ? 'drawing_sheet' : 'technical_excerpt',
    },
    source_mode: 'uploaded_document',
    metadata: document.metadata || {},
  }));
  const sourceItems = citations.length ? citations : uploadedSourceMap;
  const activeCitation = selectedCitation || sourceItems[0] || null;
  const isEngineeringEvidence = ['ENGINEERING_DRAWING', 'P_AND_ID', 'TECHNICAL_DRAWING', 'engineering_drawing'].includes(
    activeCitation?.source_type || activeCitation?.document_type
  );
  const [viewerSheet, setViewerSheet] = useState(1);
  const [decisionState, setDecisionState] = useState(null);
  const [reportState, setReportState] = useState(null);
  const [activeTab, setActiveTab] = useState('sources');
  const [collapsed, setCollapsed] = useState(false);
  const [visionState, setVisionState] = useState('READY');
  const [visionResult, setVisionResult] = useState(null);
  const [reportFormat, setReportFormat] = useState('DOCX');

  useEffect(() => {
    setViewerSheet(activeCitation?.sheet || activeCitation?.location?.sheet || 1);
  }, [activeCitation]);

  const handleSheetChange = (sheet) => {
    setViewerSheet(sheet);
    if (!activeCitation || !onSelectCitation) return;
    onSelectCitation({
      ...activeCitation,
      sheet,
      location: { ...(activeCitation.location || {}), sheet },
      asset_lineage: {
        ...(activeCitation.asset_lineage || {}),
        sheet,
      },
    });
  };

  const handleVisualAnalysis = async () => {
    const documentId = activeCitation?.document_id || activeCitation?.metadata?.document_id;
    if (!documentId) return;
    setVisionState('ANALYZING');
    setVisionResult(null);
    try {
      const result = await analyzeDocumentPage(documentId, viewerSheet, 'Describe visible symbols, text, and layout. Do not invent tags, coordinates, relationships, or engineering facts.');
      setVisionResult(result);
      setVisionState('COMPLETED');
    } catch (error) {
      setVisionState('FAILED');
    }
  };

  const handleHitlDecision = async (decision) => {
    const plan = currentResponse?.task_plan;
    if (!plan?.action_id) return;
    try {
      await submitHitlDecision({
        action_id: plan.action_id,
        equipment_tag: currentResponse?.equipment_details?.tag || plan.asset || 'N/A',
        decided_by: currentResponse?.username || 'sovereign_operator',
        decision,
      });
      setDecisionState(decision);
    } catch (error) {
      setDecisionState('ERROR');
    }
  };

  const handleGenerateReport = async () => {
    if (!currentResponse?.task_plan) return;
    try {
      const report = await generateMaintenanceReport({
        asset: currentResponse.equipment_details?.tag || currentResponse.query_route?.asset || 'N/A',
        issue_summary: currentResponse.reply_title || '',
        diagnosis: currentResponse.diagnosis_summary || '',
        findings: currentResponse.task_plan.steps || [],
        recommended_action: currentResponse.recommended_action || null,
        evidence_blocks: currentResponse.evidence_blocks || [],
        classification_level: currentResponse.classification_level || 'INTERNAL',
        hitl_approval_required: Boolean(currentResponse.hitl_approval_required),
        human_review_status: decisionState || (currentResponse.hitl_approval_required ? 'PENDING' : 'NOT_REQUIRED'),
      });
      const blob = new Blob([report.content], { type: 'text/markdown' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = report.filename;
      link.click();
      URL.revokeObjectURL(url);
      setReportState(report.report_id);
    } catch (error) {
      setReportState('ERROR');
    }
  };

  const handleGenerateArtifact = async () => {
    if (!currentResponse) return;
    setReportState('GENERATING');
    try {
      const artifact = await generateReportArtifact({
        format: reportFormat,
        title: currentResponse.reply_title || 'Aegis Engineering Report',
        asset: currentResponse.equipment_details?.tag || currentResponse.query_route?.asset || null,
        executive_summary: currentResponse.diagnosis_summary || null,
        findings: currentResponse.task_plan?.steps || [],
        evidence: currentResponse.evidence_blocks || currentResponse.citations || [],
        possible_interpretation: currentResponse.possible_interpretation || null,
        recommended_verification: currentResponse.recommended_verification || null,
        classification: currentResponse.classification_level || 'INTERNAL',
        operational_recommendation: currentResponse.recommended_action ? 'Human review required.' : null,
      });
      setReportState(artifact);
    } catch (error) {
      setReportState('ERROR');
    }
  };

  return (
    <aside className={`aegis-source-panel ${collapsed ? 'collapsed' : ''}`}>
      <div className="aegis-panel-header">
        <span>Evidence context</span>
        <button type="button" className="aegis-panel-toggle" onClick={() => setCollapsed((value) => !value)} aria-label={collapsed ? 'Expand evidence context' : 'Collapse evidence context'}>
          {collapsed ? <PanelRightOpen size={14} /> : <PanelRightClose size={14} />}
          <span>{collapsed ? 'Open' : 'Collapse'}</span>
        </button>
      </div>

      {!collapsed && <div className="aegis-context-tabs" role="tablist" aria-label="Evidence context">
        {[
          ['sources', 'Sources', FileText],
          ['viewer', 'Viewer', Eye],
          ['trace', 'Trace', Activity],
          ['security', 'Security', ShieldCheck],
        ].map(([id, label, Icon]) => (
          <button type="button" role="tab" aria-selected={activeTab === id} className={activeTab === id ? 'active' : ''} key={id} onClick={() => setActiveTab(id)}>
            <Icon size={13} /> {label}
          </button>
        ))}
      </div>}

      {!collapsed && activeTab === 'sources' && <div className="aegis-panel-section source-section">
        <div className="aegis-source-header row">
          <div><strong>References</strong><small className="aegis-section-description">{citations.length ? `${citations.length} source${citations.length === 1 ? '' : 's'} found` : 'Ask a question to retrieve authorized evidence.'}</small></div>
          {currentResponse?.evidence_state && <span className={`aegis-evidence-state ${currentResponse.evidence_state}`}>{currentResponse.evidence_state.replaceAll('_', ' ')}</span>}
        </div>

        <div className="aegis-source-list">
          {sourceItems.length === 0 ? (
            <div className="aegis-empty-panel">
              <Search size={16} />
              <span>No evidence selected</span>
            </div>
          ) : (
            sourceItems.map((citation, index) => {
              const documentLabel = citation.document || citation.document_name || 'Source';
              const tagLabel = citation.object_tag || citation.asset_lineage?.equipment_tag || citation.target?.tag || '—';
              const lineage = citation.asset_lineage || {
                equipment_tag: tagLabel,
                document_type: citation.document_type,
                drawing_type: citation.drawing_type,
                sheet: citation.sheet || citation.location?.sheet || 1,
                page: citation.page || 1,
              };
              const locationText = citation.document_type === 'engineering_drawing'
                ? `Sheet ${lineage.sheet || citation.sheet || citation.location?.sheet || 1}`
                : `Page ${lineage.page || citation.page || 1}`;

              return (
                <button
                  key={`${documentLabel}-${index}`}
                  className={`aegis-source-item ${activeCitation === citation ? 'active' : ''}`}
                  onClick={() => {
                    if (citation.source_mode === 'uploaded_document' && onSelectDocument) {
                      onSelectDocument(uploadedDocuments[index] || citation);
                      return;
                    }
                    if (onSelectCitation) onSelectCitation(citation);
                  }}
                >
                  <div className="aegis-source-bullet">{citation.document_type === 'engineering_drawing' ? <FileType2 size={12} /> : <FileText size={12} />}</div>
                  <div className="aegis-source-copy">
                    <strong>{documentLabel}</strong>
                    <small>{locationText}</small>
                    <span className="aegis-source-tag">{tagLabel}</span>
                  </div>
                  <ChevronRight size={12} />
                </button>
              );
            })
          )}
        </div>
      </div>}

      {!collapsed && activeTab === 'viewer' && <div className="aegis-panel-section">
        <div className="aegis-source-header row">
          <strong>Viewer</strong>
          {(activeCitation?.document_type === 'engineering_drawing' || activeCitation?.drawing_type) && (
            <AegisDrawingNavigator sheet={viewerSheet} onSheetChange={handleSheetChange} />
          )}
        </div>

        <AegisEvidenceViewer citation={activeCitation} />
        <div className="aegis-vision-analysis">
          <button type="button" className="aegis-report-button" disabled={visionState === 'ANALYZING' || !activeCitation?.document_id} onClick={handleVisualAnalysis}>
            {visionState === 'ANALYZING' ? 'Analyzing page…' : 'Analyze Page'}
          </button>
          <span className={`aegis-evidence-state ${visionState}`}>{visionState}</span>
          {visionState === 'FAILED' && <small>Local visual analysis failed or is unavailable.</small>}
          {visionResult && (
            <div className="aegis-vision-result">
              <div><label>Source</label><span>{visionResult.source_type}</span></div>
              <div><label>Page</label><span>{visionResult.page}</span></div>
              <div><label>Classification</label><span>{visionResult.classification_tag}</span></div>
              <div><label>Model</label><span>{visionResult.model_id}</span></div>
              {(visionResult.evidence || []).map((item, index) => <p key={`${item.evidence_type}-${index}`}><strong>{item.evidence_type}</strong> {item.text}</p>)}
            </div>
          )}
          {isEngineeringEvidence && (
            <div className="aegis-engineering-evidence">
              <div className="aegis-source-header row"><strong>Engineering evidence</strong><span>Page {viewerSheet}</span></div>
              <label>Tags found</label>
              <div className="aegis-lineage-tags">
                {(activeCitation?.engineering_tags || []).map((item) => (
                  <span key={item.tag || item}>{item.tag || item}</span>
                ))}
                {!(activeCitation?.engineering_tags || []).length && <span className="empty">No tags extracted</span>}
              </div>
              <label>OCR evidence</label>
              <p>{activeCitation?.extraction_method === 'local_tesseract' || activeCitation?.source_type === 'OCR' ? `Page ${viewerSheet}` : 'Not available'}</p>
              <label>Visual observations</label>
              <p>{visionResult?.analysis?.length || 0} observations</p>
              <label>Verification</label>
              <p>AI-derived • Not human verified</p>
            </div>
          )}
        </div>
      </div>}

      {!collapsed && activeTab === 'trace' && <div className="aegis-panel-section">
        <div className="aegis-source-header row">
          <strong>Agent Trace</strong>
          <span>{trace.length}</span>
        </div>
        <AegisAgentTrace trace={trace} />
        {retrievalTrace.length > 0 && <div className="aegis-trace-subsection"><div className="aegis-source-header row"><strong>Retrieval path</strong><span>{retrievalTrace.length}</span></div><AegisAgentTrace trace={retrievalTrace} /></div>}
      </div>}

      {!collapsed && activeTab === 'trace' && currentResponse?.task_plan && (
        <div className="aegis-panel-section">
          <div className="aegis-source-header row">
            <strong>Task Plan</strong>
            <span>{currentResponse.task_plan.status.replaceAll('_', ' ')}</span>
          </div>
          <div className="aegis-task-plan">
            <strong>{currentResponse.task_plan.title || 'Evidence-backed recommendation'}</strong>
            <ol>
              {(currentResponse.task_plan.steps || []).map((step, index) => <li key={`${step}-${index}`}>{step}</li>)}
            </ol>
            <small>{currentResponse.task_plan.execution_guarantee}</small>
            <div className="aegis-report-actions">
              <select value={reportFormat} onChange={(event) => setReportFormat(event.target.value)} aria-label="Report format">
                {['DOCX', 'PDF', 'XLSX', 'PPTX'].map((format) => <option key={format}>{format}</option>)}
              </select>
              <button type="button" className="aegis-report-button" onClick={handleGenerateArtifact}>
                {reportState === 'GENERATING' ? 'Generating…' : 'Generate Report'}
              </button>
            </div>
            {reportState && reportState !== 'GENERATING' && <div className="aegis-task-decision-status">
              {reportState === 'ERROR' ? 'Report generation failed' : typeof reportState === 'object' ? <>{reportState.format} · {reportState.status} · {reportState.source_count} sources · HUMAN REVIEW {reportState.status === 'REVIEW_REQUIRED' ? 'REQUIRED' : 'NOT REQUIRED'} · <a href={reportArtifactUrl(reportState.artifact_id)} target="_blank" rel="noreferrer">Download artifact</a></> : `Report generated: ${reportState}`}
            </div>}
            {currentResponse.task_plan.requires_approval && !decisionState && (
              <div className="aegis-task-decision-actions">
                <button type="button" onClick={() => handleHitlDecision('APPROVED')}>Approve recommendation</button>
                <button type="button" onClick={() => handleHitlDecision('MODIFIED')}>Modify / hold</button>
                <button type="button" onClick={() => handleHitlDecision('REJECTED')}>Reject</button>
              </div>
            )}
            {decisionState && <div className="aegis-task-decision-status">Decision recorded: {decisionState}</div>}
          </div>
        </div>
      )}

      {!collapsed && activeTab === 'security' && <div className="aegis-panel-section">
        <div className="aegis-source-header row">
          <strong>Governance</strong>
          <span className="aegis-governance-live">LOCAL</span>
        </div>
        <div className="aegis-governance-grid">
          <div><label>Inference</label><span>{currentResponse?.model_used || 'Local fallback'}</span></div>
          <div><label>Classification</label><span>{currentResponse?.classification_level || 'INTERNAL'}</span></div>
          <div><label>Egress</label><span>{egressSnapshot?.sovereign_status || systemHealth?.egress_monitor?.sovereign_status || 'Protected'}</span></div>
          <div><label>Operator</label><span>{currentUser?.username || 'sovereign_operator'}</span></div>
          <div><label>Audit</label><span>{currentResponse?.safe_refusal ? 'Refusal logged' : 'Query logged'}</span></div>
          <div><label>Commands</label><span>None executed</span></div>
        </div>
      </div>}
    </aside>
  );
}
