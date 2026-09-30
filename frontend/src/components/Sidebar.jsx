import React, { useState } from 'react';
import {
  Home, MessageSquare, FileText, Compass, Cpu, Shield, Settings,
  Clock, Bookmark, Folder, HelpCircle, ShieldCheck, ChevronRight
} from 'lucide-react';

const MAIN_LINKS = [
  { id: 'home', label: 'Home', icon: Home },
  { id: 'chat', label: 'Chat', icon: MessageSquare },
  { id: 'docs', label: 'Documents', icon: FileText },
  { id: 'explorer', label: 'Workspace Explorer', icon: Compass },
  { id: 'models', label: 'Models', icon: Cpu },
  { id: 'audit', label: 'Audit Logs', icon: Shield },
  { id: 'settings', label: 'Settings', icon: Settings },
];

const QUICK_ACCESS = [
  { id: 'recent', label: 'Recent Searches', icon: Clock },
  { id: 'saved', label: 'Saved Queries', icon: Bookmark },
  { id: 'mydocs', label: 'My Documents', icon: Folder },
  { id: 'help', label: 'Help & Support', icon: HelpCircle },
];

export default function Sidebar({ currentUser, activeWorkspace, setActiveWorkspace, activeModel, setActiveModel, onNavigateTab }) {
  const [activeTab, setActiveTab] = useState('home');

  return (
    <aside className="wb-sidebar" style={{ display: 'flex', flexDirection: 'column', height: '100%', background: '#0a0809', width: '260px', flexShrink: 0, borderRight: '1px solid rgba(189,112,53,0.15)' }}>
      
      {/* Brand / Logo */}
      <div className="wb-sidebar-brand" style={{ padding: '24px', display: 'flex', alignItems: 'center', gap: '12px' }}>
        <div className="wb-header-logo" style={{ width: '36px', height: '36px' }}>
          <ShieldCheck size={20} />
        </div>
        <div className="wb-header-name" style={{ fontSize: '1.4rem', color: '#F0F0F0', fontWeight: 800 }}>Aegis<span style={{ color: '#BD7035', fontWeight: 400 }}> AI</span></div>
      </div>

      {/* Main Links */}
      <div className="wb-sidebar-list" style={{ padding: '0 16px', flex: 1, overflowY: 'auto' }}>
        {MAIN_LINKS.map(link => {
          const Icon = link.icon;
          const active = activeTab === link.id;
          return (
            <button
              key={link.id}
              className={`wb-sidebar-item${active ? ' active' : ''}`}
              onClick={() => setActiveTab(link.id)}
              style={{
                display: 'flex', alignItems: 'center', gap: '14px', width: '100%',
                padding: '12px 16px', borderRadius: '10px', background: active ? 'rgba(189,112,53,0.1)' : 'transparent',
                color: active ? '#F3B250' : '#A8A8A8', border: 'none', cursor: 'pointer',
                marginBottom: '4px', fontSize: '0.95rem', fontWeight: active ? 600 : 500,
                transition: 'all 0.2s', textAlign: 'left'
              }}
            >
              <Icon size={18} style={{ color: active ? '#F3B250' : '#5A5A5A' }} />
              <span>{link.label}</span>
            </button>
          );
        })}

        <div style={{ margin: '32px 0 12px 16px', fontSize: '0.75rem', color: '#5A5A5A', fontWeight: 600 }}>
          Quick Access
        </div>

        {QUICK_ACCESS.map(link => {
          const Icon = link.icon;
          return (
            <button
              key={link.id}
              className="wb-sidebar-item"
              style={{
                display: 'flex', alignItems: 'center', gap: '14px', width: '100%',
                padding: '10px 16px', borderRadius: '8px', background: 'transparent',
                color: '#A8A8A8', border: 'none', cursor: 'pointer',
                marginBottom: '2px', fontSize: '0.85rem', transition: 'all 0.2s', textAlign: 'left'
              }}
            >
              <Icon size={16} style={{ color: '#5A5A5A' }} />
              <span>{link.label}</span>
            </button>
          );
        })}
      </div>

      {/* Bottom Profile Area */}
      <div style={{ padding: '24px 16px', borderTop: '1px solid rgba(255,255,255,0.05)' }}>
        
        {/* Clearance Card */}
        <div style={{ background: 'rgba(255,255,255,0.03)', borderRadius: '12px', padding: '16px', marginBottom: '16px', border: '1px solid rgba(255,255,255,0.05)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
            <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#22c55e' }}></div>
            <span style={{ fontSize: '0.75rem', color: '#A8A8A8', fontWeight: 600 }}>Clearance Level</span>
          </div>
          <div style={{ fontSize: '1.2rem', fontWeight: 800, color: '#F3B250', marginBottom: '4px' }}>
            {currentUser?.clearance || 'SECRET'}
          </div>
          <div style={{ fontSize: '0.75rem', color: '#5A5A5A' }}>Access to all authorized content</div>
        </div>

        {/* User Card */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', padding: '8px 4px', cursor: 'pointer' }}>
           <div className="wb-user-avatar lg" style={{ '--av': currentUser?.clearanceColor || '#BD7035' }}>
              {currentUser?.initials || 'RJ'}
           </div>
           <div style={{ flex: 1 }}>
             <div style={{ fontSize: '0.95rem', fontWeight: 700, color: '#F0F0F0' }}>{currentUser?.name || 'Rehan J.'}</div>
             <div style={{ fontSize: '0.75rem', color: '#A8A8A8' }}>{currentUser?.role || 'Engineer (Secret)'}</div>
           </div>
           <ChevronRight size={16} color="#5A5A5A" />
        </div>
      </div>
    </aside>
  );
}
