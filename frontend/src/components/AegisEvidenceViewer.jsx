import React, { useMemo } from 'react';
import { FileText, FileType2, ExternalLink } from 'lucide-react';
import { getDocumentFileUrl } from '../services/api';

export default function AegisEvidenceViewer({ citation }) {
  const type = useMemo(() => {
    if (!citation) return 'technical_document';
    if (citation.document_type === 'engineering_drawing' || citation.drawing_type) return 'engineering_drawing';
    return 'technical_document';
  }, [citation]);

  if (!citation) {
    return (
      <div className="aegis-evidence-placeholder">
        <FileText size={18} />
        <span>Select a citation to open evidence</span>
      </div>
    );
  }

  const documentName = citation.document || citation.document_name;
  const objectTag = citation.object_tag || citation.target?.tag;
  const drawingType = citation.drawing_type || citation.asset_lineage?.drawing_type;
  const lineage = citation.asset_lineage || {
    equipment_tag: objectTag,
    equipment_tags: objectTag === '—' ? [] : [objectTag],
    related_tags: [],
    document_type: citation.document_type || type,
    drawing_type: drawingType,
    sheet: citation.sheet || citation.location?.sheet,
    page: citation.page,
    document_name: documentName,
    target_type: citation.target?.type,
    source_kind: type === 'engineering_drawing' ? 'drawing_sheet' : 'technical_excerpt',
  };
  const equipmentTags = lineage.equipment_tags || (objectTag === '—' ? [] : [objectTag]);
  const relatedTags = lineage.related_tags || [];
  const isUploadedSource = citation.source_mode === 'uploaded_document';
  const documentUrl = citation.stored_filename || citation.document
    ? getDocumentFileUrl(citation.stored_filename, citation.document || citation.document_name)
    : null;
  const sheetLabel = type === 'engineering_drawing'
    ? `Sheet ${lineage.sheet || citation.sheet || citation.location?.sheet || 'Not provided'}`
    : `Page ${lineage.page || citation.page || 'Not provided'}`;

  return (
    <div className="aegis-evidence-viewer">
      <div className="aegis-evidence-header">
        <div className="aegis-evidence-icon">
          {type === 'engineering_drawing' ? <FileType2 size={16} /> : <FileText size={16} />}
        </div>
        <div>
          <strong>{documentName}</strong>
          <small>
            {isUploadedSource
              ? `${citation.document_type || type}${objectTag ? ` • ${objectTag}` : ''}`
              : type === 'engineering_drawing'
                ? `${drawingType} • ${sheetLabel}`
                : `${sheetLabel} • ${citation.section_title || 'Technical excerpt'}`}
          </small>
        </div>
      </div>

      <div className="aegis-evidence-canvas">
        {type === 'engineering_drawing' ? (
          <div className="aegis-technical-excerpt">
            <p>No rendered page image was returned by the document service.</p>
            {documentUrl && <a href={documentUrl} target="_blank" rel="noreferrer"><ExternalLink size={14} /> Open indexed document</a>}
          </div>
        ) : (
          <div className="aegis-technical-excerpt">
            <div className="aegis-excerpt-heading">
              <span>{sheetLabel}</span>
              <span>{citation.section_title || 'Technical excerpt'}</span>
            </div>
            <p>{citation.snippet || citation.text || 'No text excerpt was returned for this source.'}</p>
          </div>
        )}
      </div>

      <div className="aegis-evidence-meta">
        <div>
          <label>Document type</label>
          <span>{citation.document_type || type}</span>
        </div>
        <div>
          <label>Drawing type</label>
          <span>{citation.drawing_type || lineage.drawing_type || 'Not provided'}</span>
        </div>
        <div>
          <label>{type === 'engineering_drawing' ? 'Sheet' : 'Page'}</label>
          <span>{lineage.sheet || citation.sheet || citation.page || 'Not provided'}</span>
        </div>
        <div>
          <label>Object tag</label>
          <span>{lineage.equipment_tag || objectTag}</span>
        </div>
        <div>
          <label>Asset lineage</label>
          <span>{lineage.target_type || 'Not provided'}{lineage.source_kind ? ` • ${lineage.source_kind}` : ''}</span>
        </div>
        <div>
          <label>{isUploadedSource ? 'Source state' : 'Revision'}</label>
          <span>{isUploadedSource ? 'Indexed document' : (citation.revision || 'Not provided')}</span>
        </div>
      </div>

      <div className="aegis-evidence-lineage">
        <div className="aegis-lineage-heading">Indexed equipment path</div>
        <div className="aegis-lineage-tags">
          {equipmentTags.length ? equipmentTags.map((tag) => (
            <span key={tag} className={tag === objectTag ? 'primary' : ''}>{tag}</span>
          )) : <span className="empty">No equipment tags extracted</span>}
        </div>
        {relatedTags.length > 0 && <small>Related identifiers: {relatedTags.join(' • ')}</small>}
      </div>
    </div>
  );
}
