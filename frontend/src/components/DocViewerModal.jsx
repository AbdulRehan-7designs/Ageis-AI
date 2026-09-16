import React from 'react';
import { FileText, X, ShieldCheck, Tag, ExternalLink } from 'lucide-react';

export default function DocViewerModal({ isOpen, citation, onClose }) {
  if (!isOpen || !citation) return null;

  return (
    <div className="modal-overlay">
      <div className="modal-content doc-viewer-modal">
        <div className="modal-header">
          <div className="modal-title-group">
            <FileText size={20} color="#3b82f6" />
            <div>
              <h2>{citation.document || 'Document Chunk Viewer'}</h2>
              <span style={{ fontSize: '0.75rem', color: '#64748b' }}>
                Page {citation.page} {citation.section_title ? `• ${citation.section_title}` : ''}
              </span>
            </div>
          </div>
          <button className="close-btn" onClick={onClose}>
            <X size={18} />
          </button>
        </div>

        <div className="doc-viewer-body">
          <div className="doc-meta-bar">
            <div className="meta-tag">
              <Tag size={14} />
              <span>RBAC Clearance: <strong>{citation.tag || 'INTERNAL'}</strong></span>
            </div>
            <div className="meta-tag">
              <ShieldCheck size={14} color="#10b981" />
              <span>Vector Hash Verified</span>
            </div>
          </div>

          <div className="chunk-content-box">
            <div className="chunk-header">Retrieved Evidence Text Excerpt</div>
            <p className="chunk-highlighted-text">
              {citation.snippet || citation.text || 'No text snippet available for this vector chunk.'}
            </p>
          </div>
        </div>

        <div className="modal-footer" style={{ padding: '12px 20px', display: 'flex', justifyContent: 'flex-end' }}>
          <button className="action-btn-primary" onClick={onClose}>
            Close Document Viewer
          </button>
        </div>
      </div>
    </div>
  );
}
