import React from 'react';
import { CheckCircle2, Clock3, Sparkles } from 'lucide-react';

export default function AegisAgentTrace({ trace = [] }) {
  if (!trace.length) {
    return (
      <div className="aegis-empty-panel">
        <Sparkles size={18} />
        <span>No agent trace yet for this session.</span>
      </div>
    );
  }

  return (
    <div className="aegis-trace-list">
      {trace.map((step, index) => (
        <div key={`${step.title}-${index}`} className="aegis-trace-row">
          <div className="aegis-trace-icon">
            {step.status === 'completed' ? <CheckCircle2 size={14} /> : <Clock3 size={14} />}
          </div>
          <div className="aegis-trace-body">
            <strong>{step.step_number || index + 1}. {step.title}</strong>
            <p>{step.description}</p>
          </div>
        </div>
      ))}
    </div>
  );
}
