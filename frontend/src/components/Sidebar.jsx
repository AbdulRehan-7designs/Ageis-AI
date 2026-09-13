import React from 'react';
import {
  Wrench,
  FileCheck,
  Compass,
  Cpu,
  Layers,
  Database,
  Hammer,
  Wrench as ToolIcon,
  Shield,
  FileText,
  Lock,
  ChevronDown,
  ChevronRight,
  Activity
} from 'lucide-react';

export default function Sidebar({ activeModel, setActiveModel }) {
  return (
    <aside className="sidebar">
      {/* Workspaces Section */}
      <div className="sidebar-group">
        <div className="sidebar-group-header">
          <span>Workspaces</span>
          <ChevronDown size={14} />
        </div>

        <nav className="nav-list">
          <div className="nav-item active">
            <Wrench size={18} />
            <div className="nav-text">
              <span className="nav-title">Maintenance Intelligence</span>
              <span className="nav-sub">Diagnose • Plan • Execute</span>
            </div>
          </div>

          <div className="nav-item">
            <FileCheck size={18} />
            <div className="nav-text">
              <span className="nav-title">SOP Assistant</span>
              <span className="nav-sub">Find and follow procedures</span>
            </div>
          </div>

          <div className="nav-item">
            <Compass size={18} />
            <div className="nav-text">
              <span className="nav-title">Engineering Knowledge</span>
              <span className="nav-sub">P&IDs • Manuals • Drawings</span>
            </div>
          </div>

          <div className="nav-item">
            <Cpu size={18} />
            <div className="nav-text">
              <span className="nav-title">Custom Agent</span>
              <span className="nav-sub">Create your own agent</span>
            </div>
          </div>
        </nav>
      </div>

      <div className="sidebar-divider" />

      {/* Tools & Modules Nav */}
      <nav className="nav-list secondary-nav">
        <div className="nav-item-simple">
          <Layers size={18} />
          <span>Model Hub</span>
        </div>

        <div className="nav-item-simple">
          <Database size={18} />
          <span>Knowledge Hub</span>
          <ChevronRight size={14} className="nav-arrow" />
        </div>

        <div className="nav-item-simple">
          <Hammer size={18} />
          <span>Agent Builder</span>
          <ChevronRight size={14} className="nav-arrow" />
        </div>

        <div className="nav-item-simple">
          <ToolIcon size={18} />
          <span>Tool Hub</span>
          <ChevronRight size={14} className="nav-arrow" />
        </div>

        <div className="nav-item-simple">
          <Shield size={18} />
          <span>Governance</span>
          <ChevronRight size={14} className="nav-arrow" />
        </div>

        <div className="nav-item-simple">
          <FileText size={18} />
          <span>Audit & Logs</span>
          <ChevronRight size={14} className="nav-arrow" />
        </div>

        <div className="nav-item-simple">
          <Lock size={18} />
          <span>Sovereignty Center</span>
          <ChevronRight size={14} className="nav-arrow" />
        </div>
      </nav>

      <div className="sidebar-divider" />

      {/* Recent Agents */}
      <div className="sidebar-group">
        <div className="sidebar-group-header">
          <span>Recent Agents</span>
        </div>
        <div className="recent-agent-list">
          <div className="recent-agent-item active">
            <div className="agent-icon-badge">M</div>
            <span>Maintenance Intelligence</span>
            <span className="active-dot-text">Active</span>
          </div>

          <div className="recent-agent-item">
            <div className="agent-icon-badge idle">S</div>
            <span>SOP Assistant</span>
            <span className="idle-text">Idle</span>
          </div>

          <div className="recent-agent-item">
            <div className="agent-icon-badge idle">P</div>
            <span>P&ID Analyzer</span>
            <span className="idle-text">Idle</span>
          </div>
        </div>
      </div>

      <div className="sidebar-footer">
        <div className="system-health-card">
          <Activity size={16} color="#10b981" />
          <div>
            <div className="health-title">System Health</div>
            <div className="health-sub">All systems operational</div>
          </div>
        </div>
      </div>
    </aside>
  );
}
