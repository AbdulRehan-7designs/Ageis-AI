import React from 'react';
import { Cpu, Eye, Code, Database, FileText } from 'lucide-react';

export default function Sidebar({ activeModel, setActiveModel }) {
  const models = [
    { id: 'qwen2.5:7b', name: 'Qwen2.5 7B', type: 'General Reasoning', icon: Cpu, active: true },
    { id: 'qwen2-vl:7b', name: 'Qwen2-VL 7B', type: 'Vision & P&ID Parsing', icon: Eye },
    { id: 'qwen2.5-coder:7b', name: 'Qwen2.5 Coder', type: 'Scripting & Code', icon: Code },
  ];

  return (
    <aside className="sidebar">
      <div className="sidebar-section">
        <h3>Model Auto-Router</h3>
        {models.map((m) => {
          const IconComponent = m.icon;
          const isSelected = activeModel === m.id;
          return (
            <div
              key={m.id}
              className={`model-card ${isSelected ? 'active' : ''}`}
              onClick={() => setActiveModel(m.id)}
            >
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontWeight: '600', fontSize: '0.85rem' }}>
                  <IconComponent size={14} color={isSelected ? '#00f2fe' : '#94a3b8'} />
                  <span>{m.name}</span>
                </div>
                <div style={{ fontSize: '0.72rem', color: '#64748b', marginTop: '2px' }}>{m.type}</div>
              </div>
              <div style={{ fontSize: '0.65rem', padding: '2px 6px', borderRadius: '4px', background: 'rgba(255,255,255,0.05)', color: '#94a3b8' }}>
                7B INT4
              </div>
            </div>
          );
        })}
      </div>

      <div className="sidebar-section">
        <h3>Local Data Stores</h3>
        <div className="model-card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.82rem' }}>
            <Database size={14} color="#10b981" />
            <span>Qdrant Vector DB</span>
          </div>
          <span style={{ fontSize: '0.7rem', color: '#10b981', fontFamily: 'monospace' }}>ONLINE</span>
        </div>
        <div className="model-card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.82rem' }}>
            <FileText size={14} color="#3b82f6" />
            <span>ChromaDB Hybrid</span>
          </div>
          <span style={{ fontSize: '0.7rem', color: '#3b82f6', fontFamily: 'monospace' }}>READY</span>
        </div>
      </div>
    </aside>
  );
}
