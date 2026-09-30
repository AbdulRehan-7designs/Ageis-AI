import React from 'react';
import { Activity, ShieldAlert, CheckCircle2 } from 'lucide-react';

export default function EgressMonitor({ snapshot }) {
  const enabled = snapshot?.enabled !== false;
  const blocked = snapshot?.blocked_count ?? 0;
  const allowed = snapshot?.allowed_count ?? 0;
  const status = snapshot?.sovereign_status || 'WAITING';
  const events = snapshot?.events || [];
  const ok = enabled && blocked === 0;

  return (
    <div className="widget-card">
      <div className="widget-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {ok ? <CheckCircle2 size={14} color="#10b981" /> : <ShieldAlert size={14} color="#f59e0b" />}
          <span>Network Egress Monitor</span>
        </div>
        <span style={{ fontSize: '0.7rem', color: ok ? '#10b981' : '#f59e0b', fontFamily: 'monospace' }}>
          {blocked} blocked · {allowed} on-prem
        </span>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '0.78rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 10px', background: 'rgba(15,23,42,0.6)', borderRadius: '6px' }}>
          <span style={{ color: '#94a3b8' }}>WAN destinations allowed:</span>
          <span style={{ color: '#10b981', fontFamily: 'monospace', fontWeight: '600' }}>{snapshot?.external_allowed ?? 0}</span>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 10px', background: 'rgba(15,23,42,0.6)', borderRadius: '6px' }}>
          <span style={{ color: '#94a3b8' }}>Air-gap policy:</span>
          <span style={{ color: '#00f2fe', fontFamily: 'monospace' }}>{status}</span>
        </div>
        {events.slice(0, 4).map((event, idx) => (
          <div
            key={`${event.timestamp}-${idx}`}
            style={{ display: 'flex', justifyContent: 'space-between', gap: '8px', padding: '4px 10px', color: event.allowed ? '#94a3b8' : '#f59e0b' }}
          >
            <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{event.host || event.url}</span>
            <span style={{ fontFamily: 'monospace', flexShrink: 0 }}>{event.allowed ? 'ALLOW' : 'BLOCK'}</span>
          </div>
        ))}
        {!events.length && (
          <div style={{ padding: '4px 10px', color: '#64748b' }}>Waiting for local HTTP probes (Ollama / Qdrant)…</div>
        )}
      </div>
    </div>
  );
}
