import React from 'react';
import { Bot, UserRound, Quote, ShieldCheck } from 'lucide-react';

export default function AegisMessageBubble({ role, content, timestamp, streaming = false, citations = [], evidenceBlocks = [], evidenceConfidence, evidenceState, evidenceWarnings = [] }) {
  const isUser = role === 'user';

  return (
    <div className={`aegis-message-row ${isUser ? 'user' : 'assistant'}`}>
      <div className="aegis-message-avatar">
        {isUser ? <UserRound size={15} /> : <Bot size={15} />}
      </div>

      <div className="aegis-message-card">
        <div className="aegis-message-header">
          <span>{isUser ? 'Operator' : 'Aegis Analyst'}</span>
          {timestamp && <small>{timestamp}</small>}
        </div>

        <div className="aegis-message-body">
          {content || (streaming ? 'Aegis is preparing the response…' : '')}
          {streaming && <span className="aegis-inline-loading" aria-label="Response loading"><i /><i /><i /></span>}
        </div>

        {evidenceState === 'insufficient_evidence' && (
          <div className="aegis-evidence-warning">
            <strong>Insufficient authorized evidence</strong>
            <span>No technical action should be taken from this response.</span>
          </div>
        )}

        {evidenceState === 'conflicting_evidence' && (
          <div className="aegis-evidence-warning">
            <strong>Conflicting evidence requires review</strong>
            {evidenceWarnings.map((warning) => <span key={warning}>{warning}</span>)}
          </div>
        )}

        {citations.length > 0 && (
          <div className="aegis-message-citations">
            {citations.slice(0, 3).map((citation, index) => (
              <span key={`${citation.document || 'doc'}-${index}`} className="aegis-inline-citation">
                <Quote size={10} />
                {citation.document || 'Evidence'}
              </span>
            ))}
          </div>
        )}

        {evidenceBlocks.length > 0 && (
          <div className="aegis-evidence-blocks">
            <div className="aegis-evidence-blocks-header">
              <span><ShieldCheck size={11} /> Evidence reviewed</span>
              {evidenceConfidence != null && <span>Backend confidence: {evidenceConfidence}</span>}
            </div>
            {evidenceBlocks.slice(0, 5).map((block) => (
              <div key={block.evidence_id} className="aegis-evidence-block">
                <div className="aegis-evidence-block-meta">
                  <strong>{block.document}</strong>
                  <span>{block.location?.sheet ? `Sheet ${block.location.sheet}` : `Page ${block.location?.page || 1}`}</span>
                </div>
                <p>{block.snippet}</p>
                <small>{block.asset || 'General source'} · {block.classification || 'INTERNAL'}</small>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
