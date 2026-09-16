import React from 'react';
import {
  FileText,
  CheckCircle2,
  Clock,
  ChevronRight,
  Activity,
  ShieldCheck
} from 'lucide-react';

export default function RightDrawer({ response, activeTab, setActiveTab, onSelectCitation }) {
  const citations = response?.citations || [];
  const trace = response?.reasoning_trace || [];
  const equipment = response?.equipment_details;

  return (
    <aside className="right-drawer">
      {/* Tab Navigation */}
      <div className="drawer-tabs">
        <button
          className={`drawer-tab ${activeTab === 'context' ? 'active' : ''}`}
          onClick={() => setActiveTab('context')}
        >
          Context
        </button>
        <button
          className={`drawer-tab ${activeTab === 'documents' ? 'active' : ''}`}
          onClick={() => setActiveTab('documents')}
        >
          Citations ({citations.length})
        </button>
        <button
          className={`drawer-tab ${activeTab === 'agent_trace' ? 'active' : ''}`}
          onClick={() => setActiveTab('agent_trace')}
        >
          Agent Trace ({trace.length})
        </button>
      </div>

      <div className="drawer-body">
        {/* Classification Level Banner */}
        {response?.classification_level && (
          <div className="classification-level-banner">
            <ShieldCheck size={16} color="#10b981" />
            <span>Max Sensitivity Tag: <strong>{response.classification_level}</strong></span>
          </div>
        )}

        {/* TAB 1: CONTEXT */}
        {activeTab === 'context' && (
          <>
            {equipment ? (
              <div className="drawer-section">
                <div className="section-header">
                  <h3>Equipment Telemetry & Context</h3>
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
                      <span className="eq-label">SOP Threshold</span>
                      <span className="eq-val">{equipment.threshold}</span>
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="drawer-section" style={{ padding: '20px 0', textAlign: 'center', color: '#64748b' }}>
                <p>No specific equipment telemetry linked to current query.</p>
              </div>
            )}
          </>
        )}

        {/* TAB 2: CITATIONS */}
        {activeTab === 'documents' && (
          <div className="drawer-section">
            <div className="section-header">
              <h3>Retrieved Knowledge Base Evidence</h3>
              <span className="count-badge">{citations.length} sources</span>
            </div>

            {citations.length === 0 ? (
              <div style={{ color: '#64748b', textAlign: 'center', padding: '20px 0', fontSize: '0.85rem' }}>
                No document citations retrieved yet.
              </div>
            ) : (
              <div className="doc-item-list">
                {citations.map((doc, idx) => (
                  <div key={idx} className="doc-card-item clickable" onClick={() => onSelectCitation && onSelectCitation(doc)}>
                    <div className="doc-icon pdf">
                      <FileText size={16} />
                    </div>
                    <div className="doc-info">
                      <div className="doc-name">{doc.document || doc.name}</div>
                      <div className="doc-page">
                        Page {doc.page} {doc.section_title ? `• ${doc.section_title}` : ''}
                      </div>
                      {doc.snippet && <div className="doc-snippet">{doc.snippet.substring(0, 100)}...</div>}
                    </div>
                    <span className={`doc-tag-badge ${doc.tag}`}>{doc.tag}</span>
                    <ChevronRight size={14} className="doc-arrow" />
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* TAB 3: AGENT TRACE */}
        {activeTab === 'agent_trace' && (
          <div className="drawer-section">
            <div className="section-header">
              <h3>Agent Execution Trace</h3>
              {response?.execution_time_sec && (
                <span className="time-badge">{response.execution_time_sec}s</span>
              )}
            </div>

            {trace.length === 0 ? (
              <div style={{ color: '#64748b', textAlign: 'center', padding: '20px 0', fontSize: '0.85rem' }}>
                No agent trace steps logged yet.
              </div>
            ) : (
              <div className="trace-list">
                {trace.map((item, idx) => {
                  const isDone = item.status === 'completed';
                  return (
                    <div key={idx} className="trace-item-row">
                      <div className="trace-left">
                        {isDone ? (
                          <div className="step-circle done">
                            <CheckCircle2 size={14} color="#10b981" />
                          </div>
                        ) : (
                          <div className="step-circle pending">
                            <Clock size={14} color="#f59e0b" />
                          </div>
                        )}
                        {idx < trace.length - 1 && <div className="trace-line" />}
                      </div>
                      <div className="trace-content">
                        <div className="trace-title">
                          <span>{item.step_number || idx + 1}. {item.title}</span>
                          {item.timestamp && <span style={{ fontSize: '0.65rem', color: '#64748b', marginLeft: 'auto' }}>{new Date(item.timestamp).toLocaleTimeString()}</span>}
                        </div>
                        <div className="trace-desc">{item.description || item.desc}</div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}
      </div>
    </aside>
  );
}
