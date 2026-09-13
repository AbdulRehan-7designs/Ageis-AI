import React from 'react';
import {
  ShieldCheck,
  Search,
  Bell,
  Sun,
  User,
  ChevronDown
} from 'lucide-react';

export default function Header({ systemHealth }) {
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

        <div className="user-profile">
          <div className="avatar">RJ</div>
          <div className="user-info">
            <span className="user-name">Rehan</span>
            <span className="user-role">Maintenance Engineer</span>
          </div>
          <ChevronDown size={14} color="#64748b" />
        </div>
      </div>
    </header>
  );
}
