import React from 'react';
import { FileText, MapPin } from 'lucide-react';

export default function AegisCitationBadge({ citation, onClick }) {
  if (!citation) return null;

  const documentLabel = citation.document || citation.document_name || 'Source';
  const objectTag = citation.object_tag || citation.target?.tag || '—';
  const location = citation.document_type === 'engineering_drawing'
    ? `Sheet ${citation.sheet || citation.location?.sheet || 1}`
    : `Page ${citation.page || 1}`;

  return (
    <button className="aegis-citation-badge" onClick={() => onClick && onClick(citation)}>
      <span className="aegis-citation-index">[{citation.citation_id ? citation.citation_id.replace('citation_', '') : '1'}]</span>
      <span className="aegis-citation-doc">
        <FileText size={12} />
        {documentLabel}
      </span>
      <span className="aegis-citation-location">
        <MapPin size={12} />
        {location}
      </span>
      <span className="aegis-citation-tag">{objectTag}</span>
    </button>
  );
}
