import React from 'react';
import { FileText, ChevronRight, ShieldCheck, Activity, CheckCircle2, Clock } from 'lucide-react';

export default function RightDrawer({ response, activeTab, setActiveTab, onOpenItem, onSendToChat }) {
  const citations = response?.citations || [];
  const trace = response?.reasoning_trace || [];
  const equipment = response?.equipment_details || {
    tag: 'C-204',
    status: 'Warning',
    type: 'Compressor',
    location: 'Sector 4',
    vibration_val: '4.2g',
    threshold: '5.0g',
  };

  return (
    <aside className="right-drawer">
      <div className="drawer-tabs">
        <button className={`drawer-tab ${activeTab === 'context' ? 'active' : ''}`} onClick={() => setActiveTab('context')}>Context</button>
        <button className={`drawer-tab ${activeTab === 'documents' ? 'active' : ''}`} onClick={() => setActiveTab('documents')}>Sources ({citations.length})</button>
        <button className={`drawer-tab ${activeTab === 'agent_trace' ? 'active' : ''}`} onClick={() => setActiveTab('agent_trace')}>Trace ({trace.length})</button>
      </div>

      <div className="drawer-body">
        {activeTab === 'context' && (
          <div className="drawer-section">
            <div className="section-header">
              <h3>Equipment Context</h3>
            </div>

            <div className="equipment-card">
              <div className="equipment-card-header">
                <div className="equipment-icon-bg">
                  <Activity size={20} color="#3b82f6" />
                </div>
                <div className="equipment-tag-info">
                  <h4>{equipment.tag}</h4>
                  <span className="running-pill">• {equipment.status}</span>
                </div>
              </div>

              <div className="equipment-grid">
                <div className="eq-box">
                  <span className="eq-label">Type</span>
                  <span className="eq-val">{equipment.type}</span>
                </div>
                <div className="eq-box">
                  <span className="eq-label">Location</span>
                  <span className="eq-val">{equipment.location}</span>
                </div>
                <div className="eq-box">
                  <span className="eq-label">Vibration</span>
                  <span className="eq-val critical">{equipment.vibration_val}</span>
                </div>
                <div className="eq-box">
                  <span className="eq-label">Threshold</span>
                  <span className="eq-val">{equipment.threshold}</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'documents' && (
          <div className="drawer-section">
            <div className="section-header">
              <h3>Retrieved Sources</h3>
              <span className="count-badge">{citations.length}</span>
            </div>

            {citations.length === 0 ? (
              <div style={{ color: '#64748b', padding: '20px 0' }}>No citations yet.</div>
            ) : (
              <div className="doc-item-list">
                {citations.map((doc, idx) => (
                  <div key={`${doc.doc || 'citation'}-${idx}`} className="doc-card-item clickable" onClick={() => onOpenItem?.(doc)}>
                    <div className="doc-icon pdf"><FileText size={16} /></div>
                    <div className="doc-info">
                      <div className="doc-name">{doc.doc || doc.document || 'Source'}</div>
                      <div className="doc-page">Page {doc.page || 1}</div>
                    </div>
                    <ChevronRight size={14} className="doc-arrow" />
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === 'agent_trace' && (
          <div className="drawer-section">
            <div className="section-header">
              <h3>Agent Trace</h3>
            </div>

            {trace.length === 0 ? (
              <div style={{ color: '#64748b', padding: '20px 0' }}>No trace steps available.</div>
            ) : (
              <div className="trace-list">
                {trace.map((item, idx) => (
                  <div key={`${item.title || 'trace'}-${idx}`} className="trace-item-row">
                    <div className="trace-left">
                      <div className="step-circle done">
                        {item.status === 'pending' ? <Clock size={14} color="#f59e0b" /> : <CheckCircle2 size={14} color="#10b981" />}
                      </div>
                      {idx < trace.length - 1 && <div className="trace-line" />}
                    </div>
                    <div className="trace-content">
                      <div className="trace-title">{item.title || `Step ${idx + 1}`}</div>
                      <div className="trace-desc">{item.description || item.desc || 'Executed successfully.'}</div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        <div className="drawer-section compact">
          <div className="classification-level-banner">
            <ShieldCheck size={16} color="#10b981" />
            <span>Max sensitivity: <strong>INTERNAL</strong></span>
          </div>
          <button
            className="drawer-action"
            onClick={() => onSendToChat?.({ query: 'Summarize current risk and next recommended maintenance actions.' })}
          >
            Refresh insight summary
          </button>
        </div>
      </div>
    </aside>
  );
}
