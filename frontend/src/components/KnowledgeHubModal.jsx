import React, { useState, useEffect } from 'react';
import { Database, X, FileText, RefreshCw, ShieldCheck, HardDrive } from 'lucide-react';
import API from '../services/api';

export default function KnowledgeHubModal({ isOpen, onClose }) {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);

  const fetchStats = async () => {
    setLoading(true);
    try {
      const res = await API.get('/rag/stats');
      setStats(res.data);
    } catch (err) {
      console.error(err);
      setStats({ status: 'offline', collection: 'industrial_docs', vectors_count: 0, points_count: 0 });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) fetchStats();
  }, [isOpen]);

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

        <div className="modal-controls">
          <button className="action-btn-primary" onClick={fetchStats} disabled={loading}>
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
            Refresh Index Stats
          </button>
          <span className="entries-count">
            Collection: {stats?.collection || 'industrial_docs'}
          </span>
        </div>

        <div className="metrics-grid" style={{ padding: '0 20px 16px' }}>
          <div className="metric-box">
            <div className="metric-label">Total Vector Embeddings</div>
            <div className="metric-value">{stats?.vectors_count || stats?.points_count || 0}</div>
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
            <div className="metric-value">Qdrant v1.11.0</div>
          </div>
        </div>

        <div className="audit-log-table-container">
          <table className="audit-table">
            <thead>
              <tr>
                <th>Ingested Document</th>
                <th>Classification Tag</th>
                <th>Status</th>
                <th>Storage Location</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td className="query-cell">SOP-017 - Pump Maintenance.pdf</td>
                <td><span className="clearance-badge CONFIDENTIAL">CONFIDENTIAL</span></td>
                <td><span className="status-badge SUCCESS">INDEXED</span></td>
                <td>Qdrant Local Volume</td>
              </tr>
              <tr>
                <td className="query-cell">P-204 Manual.pdf</td>
                <td><span className="clearance-badge INTERNAL">INTERNAL</span></td>
                <td><span className="status-badge SUCCESS">INDEXED</span></td>
                <td>Qdrant Local Volume</td>
              </tr>
              <tr>
                <td className="query-cell">Plant_Piping_P204.pdf</td>
                <td><span className="clearance-badge RESTRICTED">RESTRICTED</span></td>
                <td><span className="status-badge SUCCESS">INDEXED</span></td>
                <td>Qdrant Local Volume</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
