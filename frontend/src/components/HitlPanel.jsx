import React from 'react';
import { UserCheck, AlertTriangle, Check, X } from 'lucide-react';

export default function HitlPanel({ pendingActions }) {
  return (
    <div className="widget-card">
      <div className="widget-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <UserCheck size={14} color="#f59e0b" />
          <span>Human-in-the-Loop Approval</span>
        </div>
        <span style={{ fontSize: '0.7rem', color: '#f59e0b', fontFamily: 'monospace' }}>
          {pendingActions.length} PENDING
        </span>
      </div>

      {pendingActions.length === 0 ? (
        <div style={{ fontSize: '0.78rem', color: '#64748b', textAlign: 'center', padding: '12px 0' }}>
          No pending critical safety actions requiring review.
        </div>
      ) : (
        pendingActions.map((action, idx) => (
          <div key={idx} style={{ background: 'rgba(245, 158, 11, 0.08)', border: '1px solid rgba(245, 158, 11, 0.2)', borderRadius: '8px', padding: '10px', marginTop: '8px' }}>
            <div style={{ fontSize: '0.8rem', fontWeight: '600', color: '#fbbf24', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <AlertTriangle size={12} />
              <span>{action.title}</span>
            </div>
            <div style={{ fontSize: '0.74rem', color: '#cbd5e1', margin: '6px 0' }}>{action.description}</div>
            <div style={{ display: 'flex', gap: '8px', marginTop: '8px' }}>
              <button style={{ flex: 1, padding: '4px 8px', background: '#10b981', color: '#000', border: 'none', borderRadius: '4px', fontSize: '0.72rem', fontWeight: '600', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '4px' }}>
                <Check size={12} /> Approve
              </button>
              <button style={{ flex: 1, padding: '4px 8px', background: '#ef4444', color: '#fff', border: 'none', borderRadius: '4px', fontSize: '0.72rem', fontWeight: '600', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '4px' }}>
                <X size={12} /> Reject
              </button>
            </div>
          </div>
        ))
      )}
    </div>
  );
}
