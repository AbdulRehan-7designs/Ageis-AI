import React from 'react';
import { Activity, ShieldAlert, CheckCircle2 } from 'lucide-react';

export default function EgressMonitor() {
  return (
    <div className="widget-card">
      <div className="widget-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Activity size={14} color="#00f2fe" />
          <span>Network Egress Monitor</span>
        </div>
        <span style={{ fontSize: '0.7rem', color: '#10b981', fontFamily: 'monospace' }}>0 B/s OUT</span>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '0.78rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 10px', background: 'rgba(15,23,42,0.6)', borderRadius: '6px' }}>
          <span style={{ color: '#94a3b8' }}>Outbound WAN Packets:</span>
          <span style={{ color: '#10b981', fontFamily: 'monospace', fontWeight: '600' }}>0 (BLOCKED)</span>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 10px', background: 'rgba(15,23,42,0.6)', borderRadius: '6px' }}>
          <span style={{ color: '#94a3b8' }}>Air-Gap Enforcement:</span>
          <span style={{ color: '#00f2fe', fontFamily: 'monospace' }}>CERT-In Compliant</span>
        </div>
      </div>
    </div>
  );
}
