import React, { useState, useEffect } from 'react';
import { ShieldCheck, ShieldAlert, RefreshCw, X, CheckCircle2, Lock, FileText } from 'lucide-react';
import { fetchAuditLogs, verifyAuditChain } from '../services/api';

export default function AuditModal({ isOpen, onClose }) {
  const [logs, setLogs] = useState([]);
  const [verification, setVerification] = useState(null);
  const [loading, setLoading] = useState(false);
  const [verifying, setVerifying] = useState(false);

  const loadLogs = async () => {
    setLoading(true);
    try {
      const data = await fetchAuditLogs();
      setLogs(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleVerify = async () => {
    setVerifying(true);
    try {
      const res = await verifyAuditChain();
      setVerification(res);
    } catch (err) {
      console.error(err);
    } finally {
      setVerifying(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      loadLogs();
      setVerification(null);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="modal-overlay">
      <div className="modal-content audit-modal">
        <div className="modal-header">
          <div className="modal-title-group">
            <Lock size={20} color="#10b981" />
            <h2>Tamper-Evident SHA-256 Audit Log Chain</h2>
          </div>
          <button className="close-btn" onClick={onClose}>
            <X size={18} />
          </button>
        </div>

        <div className="modal-controls">
          <button className="action-btn-primary" onClick={handleVerify} disabled={verifying}>
            <RefreshCw size={14} className={verifying ? 'animate-spin' : ''} />
            {verifying ? 'Verifying Hashes...' : 'Verify Cryptographic Chain'}
          </button>
          <span className="entries-count">{logs.length} Entries Logged</span>
        </div>

        {verification && (
          <div className={`verification-banner ${verification.is_valid ? 'valid' : 'invalid'}`}>
            {verification.is_valid ? (
              <>
                <ShieldCheck size={20} color="#10b981" />
                <div>
                  <strong>Cryptographic Chain Verification PASSED</strong>
                  <p>{verification.reason}</p>
                </div>
              </>
            ) : (
              <>
                <ShieldAlert size={20} color="#ef4444" />
                <div>
                  <strong>TAMPERING DETECTED IN AUDIT LOG</strong>
                  <p>{verification.reason}</p>
                </div>
              </>
            )}
          </div>
        )}

        <div className="audit-log-table-container">
          <table className="audit-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Timestamp</th>
                <th>Event Type</th>
                <th>User / Clearance</th>
                <th>Query / Action</th>
                <th>Entry SHA-256 Hash</th>
              </tr>
            </thead>
            <tbody>
              {logs.length === 0 ? (
                <tr>
                  <td colSpan={6} className="empty-text">No audit entries recorded yet. Perform a chat query to generate records.</td>
                </tr>
              ) : (
                logs.map((entry, idx) => (
                  <tr key={idx}>
                    <td className="entry-id">{entry.id}</td>
                    <td className="entry-time">{entry.timestamp}</td>
                    <td>
                      <span className={`event-tag ${entry.event_type}`}>
                        {entry.event_type || 'CHAT_QUERY'}
                      </span>
                    </td>
                    <td>
                      <div className="user-cell">
                        <span>{entry.username || 'operator'}</span>
                        <div className="tags-row">
                          {(entry.clearance_tags || ['INTERNAL']).map((tag, tIdx) => (
                            <span key={tIdx} className={`clearance-badge ${tag}`}>{tag}</span>
                          ))}
                        </div>
                      </div>
                    </td>
                    <td className="query-cell">{entry.query_or_action || entry.action}</td>
                    <td className="hash-cell" title={`Previous: ${entry.previous_hash}`}>
                      <code>{entry.entry_hash ? entry.entry_hash.substring(0, 16) + '...' : 'N/A'}</code>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
