import React from 'react';
import { ShieldCheck, ShieldAlert, Cpu, Lock } from 'lucide-react';

export default function Header({ systemHealth }) {
  const egressStatus = systemHealth?.egress_monitor?.sovereign_status || 'AIR_GAPPED_ENFORCED';

  return (
    <header className="header">
      <div className="brand">
        <div className="brand-logo">
          <ShieldCheck size={20} />
        </div>
        <div className="brand-text">
          <h1>AegisAI Workbench</h1>
          <span>Sovereign Industrial Workbench (SIH 2026)</span>
        </div>
      </div>

      <div className="header-badges">
        <div className="status-badge" style={{ borderColor: 'rgba(0, 242, 254, 0.3)' }}>
          <Lock size={12} color="#00f2fe" />
          <span>Classification: INTERNAL / CONFIDENTIAL</span>
        </div>

        <div className="status-badge">
          <div className="status-indicator"></div>
          <span>{egressStatus}</span>
        </div>

        <div className="status-badge">
          <Cpu size={12} color="#10b981" />
          <span>Local GPU Active (RTX 3050)</span>
        </div>
      </div>
    </header>
  );
}
