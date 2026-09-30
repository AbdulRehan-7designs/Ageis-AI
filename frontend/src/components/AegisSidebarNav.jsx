import React from 'react';
import {
  Wrench,
  FileCheck,
  Compass,
  Cpu,
  Database,
  Hammer,
  Shield,
  FileText,
  Lock,
  ChevronRight,
  Layers,
  Activity,
  PanelLeftClose,
  PanelLeftOpen,
} from 'lucide-react';

const workspaceItems = [
  { label: 'Maintenance Intelligence', sub: 'Diagnose • Plan • Execute', icon: Wrench, active: true },
  { label: 'SOP Assistant', sub: 'Find and follow procedures', icon: FileCheck },
  { label: 'Engineering Knowledge', sub: 'P&IDs • Manuals • Drawings', icon: Compass },
  { label: 'Custom Agent', sub: 'Create your own agent', icon: Cpu },
];

const secondaryItems = [
  { label: 'Model Hub', icon: Layers },
  { label: 'Knowledge Hub', icon: Database, accent: true, onClick: 'knowledge' },
  { label: 'Agent Builder', icon: Hammer },
  { label: 'Code Sandbox', icon: Wrench, accent: true, onClick: 'sandbox' },
  { label: 'Governance & Hashes', icon: Shield, accent: true, onClick: 'audit' },
  { label: 'Audit & Logs', icon: FileText },
  { label: 'Sovereignty Center', icon: Lock },
];

export default function AegisSidebarNav({ activeModel, setActiveModel, systemHealth, collapsed = false, onToggleCollapse, onOpenAudit, onOpenSandbox, onOpenKnowledgeHub }) {
  const handleNavAction = (action) => {
    if (action === 'audit' && onOpenAudit) onOpenAudit();
    if (action === 'sandbox' && onOpenSandbox) onOpenSandbox();
    if (action === 'knowledge' && onOpenKnowledgeHub) onOpenKnowledgeHub();
  };

  return (
    <aside className={`aegis-sidebar ${collapsed ? 'collapsed' : ''}`}>
      <div className="aegis-sidebar-toolbar">
        {!collapsed && <span>Control surface</span>}
        <button type="button" className="aegis-collapse-btn" onClick={onToggleCollapse} aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'} title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}>
          {collapsed ? <PanelLeftOpen size={16} /> : <PanelLeftClose size={16} />}
        </button>
      </div>
      <div className="aegis-sidebar-section">
        <div className="aegis-section-header">
          <span>Workspaces</span>
        </div>

        <nav className="aegis-nav-stack">
          {workspaceItems.map(({ label, sub, icon: Icon, active }) => (
            <button key={label} className={`aegis-nav-item ${active ? 'active' : ''}`} title={collapsed ? label : undefined}>
              <Icon size={18} />
              {!collapsed && <div>
                <strong>{label}</strong>
                <small>{sub}</small>
              </div>}
            </button>
          ))}
        </nav>
      </div>

      <div className="aegis-divider" />

      <div className="aegis-sidebar-section compact">
        <nav className="aegis-secondary-nav">
          {secondaryItems.map(({ label, icon: Icon, accent, onClick }) => (
            <button key={label} className={`aegis-secondary-item ${accent ? 'accent' : ''}`} onClick={() => handleNavAction(onClick)} title={collapsed ? label : undefined}>
              <Icon size={17} />
              {!collapsed && <><span>{label}</span><ChevronRight size={14} /></>}
            </button>
          ))}
        </nav>
      </div>

      <div className="aegis-divider" />

      <div className="aegis-sidebar-section">
        {!collapsed && <div className="aegis-section-header">
          <span>Recent Agents</span>
        </div>}

        <div className="aegis-agent-list">
          {[
            { name: 'Maintenance Intelligence', status: 'Active', tone: 'live' },
            { name: 'SOP Assistant', status: 'Idle', tone: 'idle' },
            { name: 'P&ID Analyzer', status: 'Idle', tone: 'idle' },
          ].map(({ name, status, tone }) => (
            <div key={name} className={`aegis-agent-row ${tone === 'live' ? 'active' : ''}`}>
              <span className={`aegis-agent-badge ${tone}`}>{name.charAt(0)}</span>
              {!collapsed && <><span className="aegis-agent-name">{name}</span><span className={`aegis-agent-state ${tone}`}>{status}</span></>}
            </div>
          ))}
        </div>
      </div>

      <div className="aegis-sidebar-footer">
        <div className="aegis-health-card">
          <Activity size={16} color="#10b981" />
          {!collapsed && <div>
            <strong>System Health</strong>
            <small>
              {systemHealth?.services?.ollama?.status
                ? `Ollama ${systemHealth.services.ollama.status}`
                : 'Waiting for local services'}
            </small>
          </div>}
        </div>
      </div>
    </aside>
  );
}
