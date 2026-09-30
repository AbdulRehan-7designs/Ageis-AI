import React, { useState } from 'react';
import {
  Search, Bell, Shield, Sparkles, Activity, Settings, LogOut, ChevronDown, Lock
} from 'lucide-react';

export default function Header({ systemHealth, currentUser, activeDashboard, setActiveDashboard, onLogout, onSearch }) {
  const [searchVal, setSearchVal] = useState('');
  const [showDashMenu, setShowDashMenu] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);

  return (
    <header className="wb-header" style={{ padding: '0 32px', height: '64px', background: 'rgba(22, 17, 20, 0.95)', borderBottom: '1px solid rgba(255,255,255,0.05)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', zIndex: 100 }}>
      
      {/* Breadcrumbs / Tagline */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px', color: '#5A5A5A', fontSize: '0.85rem', fontWeight: 500 }}>
        <Sparkles size={16} />
        <span>Secure</span>
        <span style={{ color: 'rgba(255,255,255,0.1)' }}>|</span>
        <span>Intelligent</span>
        <span style={{ color: 'rgba(255,255,255,0.1)' }}>|</span>
        <span>Engineering Focused</span>
      </div>

      {/* Right Side Actions */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        
        {/* Search */}
        <div style={{ 
          display: 'flex', alignItems: 'center', gap: '8px', 
          background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.08)', 
          borderRadius: '20px', padding: '6px 16px', width: '300px'
        }}>
          <Search size={14} color="#5A5A5A" />
          <input
            style={{ background: 'transparent', border: 'none', outline: 'none', color: '#F0F0F0', fontSize: '0.85rem', width: '100%', fontFamily: 'inherit' }}
            placeholder="Search documents, equipment, P-204, tags..."
            value={searchVal}
            onChange={e => setSearchVal(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter') { onSearch?.(searchVal); setSearchVal(''); } }}
          />
        </div>

        {/* Icons */}
        <div style={{ position: 'relative', display: 'flex', alignItems: 'center', justifyContent: 'center', width: '36px', height: '36px', borderRadius: '50%', background: 'transparent', cursor: 'pointer', color: '#A8A8A8', transition: 'background 0.2s' }}
             onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(255,255,255,0.05)'}
             onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
        >
          <Bell size={18} />
          <div style={{ position: 'absolute', top: '8px', right: '10px', width: '6px', height: '6px', background: '#ef4444', borderRadius: '50%' }}></div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: '36px', height: '36px', borderRadius: '50%', background: 'transparent', cursor: 'pointer', color: '#A8A8A8', transition: 'background 0.2s' }}
             onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(255,255,255,0.05)'}
             onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
        >
          <Shield size={18} />
        </div>

        {/* Dashboard Menu Toggle (Hidden behind icon for clean look) */}
        <div style={{ position: 'relative' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: '36px', height: '36px', borderRadius: '50%', background: 'transparent', cursor: 'pointer', color: '#A8A8A8', transition: 'background 0.2s' }}
               onClick={() => setShowDashMenu(!showDashMenu)}
               onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(255,255,255,0.05)'}
               onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
          >
            <Settings size={18} />
          </div>

          {showDashMenu && (
            <div className="wb-dash-menu" onClick={e => e.stopPropagation()} style={{ right: 0, left: 'auto', top: '45px' }}>
              <div style={{ padding: '8px 12px', fontSize: '0.7rem', color: '#5A5A5A', textTransform: 'uppercase', fontWeight: 700 }}>Switch Role</div>
              {['maintenance', 'admin', 'security', 'analyst', 'operator'].map(d => (
                <button
                  key={d}
                  className={`wb-dash-item${d === activeDashboard ? ' active' : ''}`}
                  onClick={() => {
                    setActiveDashboard(d);
                    setShowDashMenu(false);
                  }}
                  style={{ textTransform: 'capitalize' }}
                >
                  <Activity size={14} />
                  <span>{d} Console</span>
                </button>
              ))}
              <div style={{ height: '1px', background: 'rgba(255,255,255,0.06)', margin: '8px 0' }}></div>
              <button className="wb-dash-item" onClick={onLogout} style={{ color: '#ef4444' }}>
                <LogOut size={14} />
                <span>Sign Out</span>
              </button>
            </div>
          )}
        </div>

      </div>
    </header>
  );
}
