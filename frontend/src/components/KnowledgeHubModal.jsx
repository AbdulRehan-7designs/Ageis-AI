import React, { useState, useEffect } from 'react';
import { Database, X, RefreshCw, UploadCloud, FileText } from 'lucide-react';
import { fetchDocumentList, uploadDocuments } from '../services/api';
import API from '../services/api';

export default function KnowledgeHubModal({ isOpen, onClose, onDocumentsChanged, onOpenDocument }) {
  const [stats, setStats] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [uploadSummary, setUploadSummary] = useState(null);

  const fetchStats = async () => {
    setLoading(true);
    try {
      const [health, docs] = await Promise.all([
        API.get('/health').then((res) => res.data).catch(() => null),
        fetchDocumentList(),
      ]);
      setStats(health?.services?.qdrant || null);
      setDocuments(docs);
      if (onDocumentsChanged) onDocumentsChanged(docs);
      return docs;
    } catch (err) {
      console.error(err);
      return [];
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) fetchStats();
  }, [isOpen]);

  const handleUpload = async () => {
    if (!selectedFiles.length) return;
    setUploading(true);
    try {
      const result = await uploadDocuments(selectedFiles, 'INTERNAL');
      setUploadSummary(result);
      setSelectedFiles([]);
      await fetchStats();
    } catch (error) {
      console.error('Upload failed:', error);
      setUploadSummary({ status: 'ERROR', message: 'Upload failed. Check backend availability and PDF format.' });
    } finally {
      setUploading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay">
      <div className="modal-content audit-modal">
        <div className="modal-header">
          <div className="modal-title-group">
            <Database size={20} color="#3b82f6" />
            <h2>Sovereign Knowledge Hub & Qdrant Index</h2>
          </div>
          <button className="close-btn" onClick={onClose}>
            <X size={18} />
          </button>
        </div>

        <div className="modal-controls" style={{ display: 'flex', flexWrap: 'wrap', gap: '12px', alignItems: 'center' }}>
          <button className="action-btn-primary" onClick={fetchStats} disabled={loading}>
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
            Refresh Index Stats
          </button>
          <label className="action-btn-primary" style={{ cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: '8px' }}>
            <UploadCloud size={14} />
            Select PDF(s)
            <input
              type="file"
              accept=".pdf"
              multiple
              onChange={(event) => setSelectedFiles(Array.from(event.target.files || []))}
              style={{ display: 'none' }}
            />
          </label>
          <button className="action-btn-primary" onClick={handleUpload} disabled={uploading || selectedFiles.length === 0}>
            {uploading ? 'Uploading...' : 'Ingest Selected'}
          </button>
          <span className="entries-count">
            {documents.length} document(s) in {stats?.collection || 'industrial_docs'}
          </span>
        </div>

        {uploadSummary && (
          <div className="metrics-grid" style={{ padding: '0 20px 12px' }}>
            <div className="metric-box" style={{ gridColumn: '1 / -1' }}>
              <div className="metric-label">Last upload summary</div>
              <div className="metric-value" style={{ fontSize: '0.85rem', textAlign: 'left', fontWeight: 500 }}>
                {uploadSummary.status === 'ERROR' ? uploadSummary.message : (
                  <>
                    {uploadSummary.documents?.map((doc) => (
                      <div key={doc.filename} style={{ marginBottom: '4px' }}>
                        <strong>{doc.filename}</strong> · {doc.document_type || 'technical_document'} · {doc.object_tag || '—'} · {doc.page_count || 0} pages · {doc.chunks_indexed} chunks · {doc.evidence_ready ? 'evidence ready' : 'not indexed'}
                        {doc.equipment_tags?.length > 0 && <span> · tags: {doc.equipment_tags.join(', ')}</span>}
                      </div>
                    )) || uploadSummary.message}
                  </>
                )}
              </div>
            </div>
          </div>
        )}

        <div className="metrics-grid" style={{ padding: '0 20px 16px' }}>
          <div className="metric-box">
            <div className="metric-label">Indexed chunks</div>
            <div className="metric-value">{stats?.points_count || stats?.vectors_count || 0}</div>
          </div>
          <div className="metric-box">
            <div className="metric-label">Vector Store Status</div>
            <div className="status-running-row">
              <span className="running-dot" />
              <span>{stats?.status || 'Online'}</span>
            </div>
          </div>
          <div className="metric-box">
            <div className="metric-label">Storage Backend</div>
            <div className="metric-value">Qdrant (local)</div>
          </div>
        </div>

        <div className="audit-log-table-container">
          <table className="audit-table">
            <thead>
              <tr>
                <th>Ingested Document</th>
                <th>Type</th>
                <th>Object Tag</th>
                <th>Indexed Tags</th>
                <th>Classification Tag</th>
                <th>Status</th>
                <th>Stored file</th>
              </tr>
            </thead>
            <tbody>
              {documents.length === 0 && (
                <tr>
                  <td className="query-cell" colSpan={7}>No PDFs in the index yet. Upload one or more files to begin evidence ingestion.</td>
                </tr>
              )}
              {documents.map((doc) => (
                <tr
                  key={doc.document_name}
                  onClick={() => onOpenDocument && onOpenDocument(doc)}
                  style={{ cursor: onOpenDocument ? 'pointer' : 'default' }}
                  title={onOpenDocument ? 'Open source in evidence viewer' : undefined}
                >
                  <td className="query-cell">{doc.document_name}</td>
                  <td>{doc.document_type || 'technical_document'}</td>
                  <td>{doc.object_tag || '—'}</td>
                  <td>{doc.equipment_tags?.length ? doc.equipment_tags.join(', ') : '—'}</td>
                  <td><span className={`clearance-badge ${doc.classification_tag}`}>{doc.classification_tag}</span></td>
                  <td><span className="status-badge SUCCESS">{doc.status}</span></td>
                  <td>{doc.stored_filename || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
