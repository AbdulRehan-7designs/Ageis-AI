import React from 'react';
import {
  FileText,
  CheckCircle2,
  Clock,
  ChevronRight,
  Activity
} from 'lucide-react';

export default function RightDrawer({ response, activeTab, setActiveTab }) {
  const documents = [
    { name: 'SOP-017 - Pump Maintenance', page: 'Page 4 • Section 3.2', badge: 'Most relevant', type: 'pdf' },
    { name: 'P-204 Manual', page: 'Page 28 • Vibration Limits', type: 'pdf' },
    { name: 'Maintenance History', page: 'Page 6 • 12 Mar 2025', type: 'pdf' },
    { name: 'Plant_Piping_P204.pdf', page: 'Page 2 • P&ID', type: 'blue' },
    { name: 'Inspection_Report_P204.pdf', page: 'Page 3 • Last Inspection', type: 'green' }
  ];

  const agentTrace = [
    { step: 1, title: 'Understand Request', desc: 'Parsed equipment ID: P-204, intent: diagnosis', done: true },
    { step: 2, title: 'Retrieve Evidence', desc: 'Found 5 relevant documents (SOP, Manual, History)', done: true },
    { step: 3, title: 'Analyze & Reason', desc: 'Identified vibration as primary issue', done: true },
    { step: 4, title: 'Check Constraints', desc: 'Verified safety and policy constraints', done: true },
    { step: 5, title: 'Propose Action', desc: 'Generated maintenance plan (requires approval)', done: true },
    { step: 6, title: 'Awaiting Human Approval', desc: 'Action pending user confirmation', pending: true }
  ];

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
          Documents (5)
        </button>
        <button
          className={`drawer-tab ${activeTab === 'agent_trace' ? 'active' : ''}`}
          onClick={() => setActiveTab('agent_trace')}
        >
          Agent Trace
        </button>
        <button
          className={`drawer-tab ${activeTab === 'tools' ? 'active' : ''}`}
          onClick={() => setActiveTab('tools')}
        >
          Tools
        </button>
      </div>

      <div className="drawer-body">
        {/* Relevant Documents Section */}
        <div className="drawer-section">
          <div className="section-header">
            <h3>Relevant Documents</h3>
            <a href="#viewall" className="view-all-link">View all</a>
          </div>

          <div className="doc-item-list">
            {documents.map((doc, idx) => (
              <div key={idx} className="doc-card-item">
                <div className={`doc-icon ${doc.type}`}>
                  <FileText size={16} />
                </div>
                <div className="doc-info">
                  <div className="doc-name">{doc.name}</div>
                  <div className="doc-page">{doc.page}</div>
                </div>
                {doc.badge && <span className="doc-badge-relevant">{doc.badge}</span>}
                <ChevronRight size={14} className="doc-arrow" />
              </div>
            ))}
          </div>
        </div>

        <div className="drawer-divider" />

        {/* Agent Reasoning Trace */}
        <div className="drawer-section">
          <div className="section-header">
            <h3>Agent Reasoning Trace</h3>
            <a href="#viewtrace" className="view-all-link">View full trace</a>
          </div>

          <div className="trace-list">
            {agentTrace.map((item, idx) => (
              <div key={idx} className="trace-item-row">
                <div className="trace-left">
                  {item.done ? (
                    <div className="step-circle done">
                      <CheckCircle2 size={14} color="#10b981" />
                    </div>
                  ) : (
                    <div className="step-circle pending">
                      <Clock size={14} color="#f59e0b" />
                    </div>
                  )}
                  {idx < agentTrace.length - 1 && <div className="trace-line" />}
                </div>
                <div className="trace-content">
                  <div className="trace-title">
                    <span>{item.step}. {item.title}</span>
                  </div>
                  <div className="trace-desc">{item.desc}</div>
                </div>
                <ChevronRight size={14} className="doc-arrow" />
              </div>
            ))}
          </div>
        </div>

        <div className="drawer-divider" />

        {/* Equipment Details Card */}
        <div className="drawer-section">
          <div className="section-header">
            <h3>Equipment Details</h3>
            <a href="#knowledge" className="view-all-link">View in Knowledge Hub</a>
          </div>

          <div className="equipment-card">
            <div className="equipment-card-header">
              <div className="equipment-icon-bg">
                <Activity size={20} color="#3b82f6" />
              </div>
              <div className="equipment-tag-info">
                <h4>P-204</h4>
                <span className="running-pill">• Running</span>
              </div>
            </div>

            <div className="equipment-grid">
              <div className="eq-box">
                <span className="eq-label">Type</span>
                <span className="eq-val">Centrifugal Pump</span>
              </div>
              <div className="eq-box">
                <span className="eq-label">Location</span>
                <span className="eq-val">Process Line A</span>
              </div>
              <div className="eq-box">
                <span className="eq-label">Last Maintenance</span>
                <span className="eq-val">12 Mar 2025</span>
              </div>
              <div className="eq-box">
                <span className="eq-label">Next Service</span>
                <span className="eq-val">Due in 18 days</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </aside>
  );
}
