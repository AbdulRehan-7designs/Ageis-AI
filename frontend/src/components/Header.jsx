import React from 'react';
import {
  ShieldCheck,
  Search,
  Bell,
  Sun,
  User,
  ChevronDown
} from 'lucide-react';

export default function Header({ systemHealth, currentUser, onSelectRole }) {
  return (
    <header className="header">
      <div className="brand">
        <div className="brand-logo">A</div>
        <div className="brand-text">
          <h1>Ageis AI</h1>
          <span>Sovereign Agentic AI Workbench</span>
        </div>
      </div>

      <div className="search-bar-container">
        <Search size={16} className="search-icon" />
        <input
          type="text"
          placeholder='Ask anything... (e.g., "Diagnose P-204 vibration issue")'
          className="header-search-input"
        />
        <span className="kbd-badge">Ctrl + K</span>
      </div>

      <div className="header-actions">
        <div className="sovereign-badge">
          <ShieldCheck size={16} color="#10b981" />
          <div className="sovereign-info">
            <span className="sovereign-title">Sovereign Mode</span>
            <span className="sovereign-sub">No external API calls</span>
          </div>
        </div>

        <button className="icon-btn notification-btn">
          <Bell size={18} />
          <span className="notification-dot">3</span>
        </button>

        <button className="icon-btn">
          <Sun size={18} />
        </button>

        <div className="user-profile" style={{ gap: '8px' }}>
          <div className="avatar">
            {currentUser?.username ? currentUser.username.substring(0, 2).toUpperCase() : 'US'}
          </div>
          <div className="user-info">
            <span className="user-name">{currentUser?.username || 'Operator'}</span>
            <span className="user-role" style={{ fontSize: '11px', color: '#10b981', fontWeight: '600' }}>
              {currentUser?.role || 'ENGINEER'} [{(currentUser?.clearance_tags || ['INTERNAL']).join(', ')}]
            </span>
          </div>
          {onSelectRole && (
            <select
              value={currentUser?.role || 'ENGINEER'}
              onChange={(e) => onSelectRole(e.target.value)}
              style={{
                background: '#1e293b',
                color: '#94a3b8',
                border: '1px solid #334155',
                borderRadius: '4px',
                padding: '2px 4px',
                fontSize: '11px',
                cursor: 'pointer'
              }}
            >
              <option value="ADMIN">ADMIN (All Tiers)</option>
              <option value="ENGINEER">ENGINEER (Conf/Rest/Int/Pub)</option>
              <option value="OPERATOR">OPERATOR (Rest/Int/Pub)</option>
              <option value="AUDITOR">AUDITOR (Int/Pub)</option>
              <option value="PUBLIC">PUBLIC (Public Only)</option>
            </select>
          )}
        </div>
      </div>
    </header>
  );
}
