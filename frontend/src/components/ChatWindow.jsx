import React, { useState } from 'react';
import {
  Wrench,
  ChevronDown,
  Maximize2,
  Send,
  Paperclip,
  CheckCircle2,
  AlertTriangle,
  FileText,
  Copy,
  Bookmark,
  ThumbsUp,
  ThumbsDown,
  ChevronRight,
  ShieldAlert
} from 'lucide-react';
import { sendChatMessage } from '../services/api';

export default function ChatWindow({ activeModel, onNewResponse }) {
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState([
    {
      role: 'user',
      content: 'P-204 is showing abnormal vibration. Can you diagnose the possible cause and recommend the next approved maintenance action?'
    },
    {
      role: 'assistant',
      reply_title: 'Diagnosis Summary',
      diagnosis_summary: 'P-204 is showing an abnormal vibration of 8.2 mm/s, which is above the critical threshold (>7.1 mm/s) as per SOP-017. Based on the available evidence, the most likely cause is bearing degradation, which could lead to increased vibration and potential failure if not addressed.',
      metrics: {
        vibration: '8.2 mm/s',
        vibration_status: 'Critical',
        threshold: '> 7.1 mm/s',
        temp: '74 °C',
        status: 'Running'
      },
      recommended_action: {
        title: 'Schedule immediate inspection and maintenance',
        sop: 'Follow SOP-017: Pump Maintenance',
        requires_approval: true,
        steps: [
          'Verify sensor readings and confirm vibration trend.',
          'Isolate and shut down the pump (requires approval).',
          'Perform mechanical inspection (bearing, coupling, alignment).',
          'Replace/repair as needed based on findings.'
        ],
        why_reasoning: [
          'Vibration (8.2 mm/s) exceeds critical threshold (>7.1 mm/s) from SOP-017 (p.4).',
          'Historical records show similar vibration pattern in the last 3 months (see Maintenance History).',
          'P&ID confirms P-204 is a critical pump in the main line (see Plant_Piping_P204.pdf).',
          'SOP requires inspection before any shutdowns.'
        ]
      },
      citations: [
        { document: 'SOP-017 - Pump Maintenance', page: 'Page 4 • Section 3.2', tag: 'CONFIDENTIAL', type: 'pdf' },
        { document: 'P-204 Manual', page: 'Page 28 • Vibration Limits', tag: 'INTERNAL', type: 'doc' },
        { document: 'Maintenance History', page: 'Page 6 • 12 Mar 2025', tag: 'RESTRICTED', type: 'doc' }
      ]
    }
  ]);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userText = input;
    setMessages((prev) => [...prev, { role: 'user', content: userText }]);
    setInput('');
    setLoading(true);

    try {
      const data = await sendChatMessage({
        message: userText,
        model_override: activeModel
      });

      const assistantMsg = {
        role: 'assistant',
        reply_title: data.reply_title || 'Analysis Summary',
        diagnosis_summary: data.diagnosis_summary,
        metrics: data.equipment_details
          ? {
              vibration: data.equipment_details.vibration_val,
              vibration_status: data.equipment_details.vibration_status,
              threshold: data.equipment_details.threshold,
              temp: data.equipment_details.temp,
              status: data.equipment_details.status
            }
          : null,
        recommended_action: {
          title: data.recommended_action.title,
          sop: `Follow ${data.recommended_action.sop_code}`,
          requires_approval: data.recommended_action.requires_approval,
          steps: data.recommended_action.steps,
          why_reasoning: data.recommended_action.why_reasoning
        },
        citations: data.citations.map((c) => ({
          document: c.document,
          page: `Page ${c.page}`,
          tag: c.tag,
          type: 'pdf'
        }))
      };

      setMessages((prev) => [...prev, assistantMsg]);
      if (onNewResponse) onNewResponse(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="main-chat-area">
      {/* Agent Banner Top */}
      <div className="agent-banner">
        <div className="agent-banner-left">
          <div className="agent-avatar">
            <Wrench size={18} />
          </div>
          <div>
            <div className="agent-title-row">
              <h2>Maintenance Intelligence Agent</h2>
              <span className="online-badge">• Online</span>
            </div>
            <p className="agent-desc">
              Diagnose equipment issues, provide SOP-based guidance, and recommend actions.
            </p>
          </div>
        </div>

        <div className="agent-banner-right">
          <div className="model-selector-btn">
            <div className="model-icon">🤖</div>
            <span>{activeModel || 'Llama 3.1 8B'}</span>
            <span className="sub-model">Local Model</span>
            <ChevronDown size={14} />
          </div>

          <button className="tools-btn">
            <span>Tools</span>
            <ChevronDown size={14} />
          </button>

          <button className="icon-btn-ghost">
            <Maximize2 size={16} />
          </button>
        </div>
      </div>

      {/* Messages Thread */}
      <div className="chat-messages-container">
        <div className="breadcrumb-nav">
          <span>Maintenance Intelligence</span>
          <ChevronRight size={14} />
          <span className="active">P-204 Analysis</span>
        </div>

        {messages.map((msg, idx) => (
          <div key={idx} className="message-wrapper">
            {msg.role === 'user' ? (
              <div className="user-message-row">
                <div className="user-avatar-small">RJ</div>
                <div className="user-bubble">
                  {msg.content}
                  <div className="time-stamp">Today, 14:32</div>
                </div>
              </div>
            ) : (
              <div className="assistant-message-card">
                <div className="assistant-header-bar">
                  <div className="agent-badge-icon">M</div>
                  <div className="status-pill">
                    <CheckCircle2 size={14} color="#10b981" />
                    <span>Analysis complete</span>
                  </div>
                  <span className="dot-divider">•</span>
                  <span className="trace-link">Thought process • 6 steps • 18.4s</span>
                </div>

                <div className="card-body-content">
                  <h3 className="card-title">{msg.reply_title || 'Diagnosis Summary'}</h3>
                  <p className="summary-paragraph">{msg.diagnosis_summary}</p>

                  {/* Metrics Row */}
                  {msg.metrics && (
                    <div className="metrics-grid">
                      <div className="metric-box">
                        <div className="metric-label">Current Vibration</div>
                        <div className="metric-value-row">
                          <span className="metric-number">{msg.metrics.vibration}</span>
                          <span className="badge-critical">{msg.metrics.vibration_status}</span>
                        </div>
                      </div>

                      <div className="metric-box">
                        <div className="metric-label">SOP Threshold</div>
                        <div className="metric-value">{msg.metrics.threshold}</div>
                      </div>

                      <div className="metric-box">
                        <div className="metric-label">Temperature</div>
                        <div className="metric-value">{msg.metrics.temp}</div>
                      </div>

                      <div className="metric-box">
                        <div className="metric-label">Status</div>
                        <div className="status-running-row">
                          <span className="running-dot" />
                          <span>{msg.metrics.status}</span>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Recommended Action Box */}
                  {msg.recommended_action && (
                    <div className="action-box">
                      <div className="action-box-header">
                        <div className="action-icon">
                          <ShieldAlert size={20} color="#3b82f6" />
                        </div>
                        <div className="action-title-area">
                          <h4>{msg.recommended_action.title}</h4>
                          <span className="sop-text">{msg.recommended_action.sop}</span>
                        </div>
                        {msg.recommended_action.requires_approval && (
                          <div className="approval-badge">
                            <span>Requires Human Approval</span>
                            <ChevronRight size={14} />
                          </div>
                        )}
                      </div>

                      <ol className="action-steps-list">
                        {msg.recommended_action.steps.map((step, i) => (
                          <li key={i}>{step}</li>
                        ))}
                      </ol>

                      {/* Why reasoning dropdown/accordion */}
                      <div className="why-accordion">
                        <div className="accordion-header">
                          <ChevronRight size={14} />
                          <span>Why is this the recommendation?</span>
                        </div>
                        <ul className="why-list">
                          {msg.recommended_action.why_reasoning.map((why, i) => (
                            <li key={i}>{why}</li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  )}

                  {/* Sources & Citations */}
                  {msg.citations && msg.citations.length > 0 && (
                    <div className="citations-section">
                      <div className="citations-header">
                        <span>Sources & Citations</span>
                        <a href="#viewall" className="view-all-link">
                          View all ({msg.citations.length})
                        </a>
                      </div>

                      <div className="citations-cards-row">
                        {msg.citations.map((c, i) => (
                          <div key={i} className="citation-card-item">
                            <FileText size={16} color="#f43f5e" />
                            <div>
                              <div className="citation-doc-name">{c.document}</div>
                              <div className="citation-doc-page">{c.page}</div>
                            </div>
                          </div>
                        ))}
                      </div>

                      {/* Action buttons footer */}
                      <div className="message-action-bar">
                        <button className="action-btn-pill">
                          <Copy size={13} />
                          <span>Copy</span>
                        </button>
                        <button className="action-btn-pill">
                          <Bookmark size={13} />
                          <span>Save to Knowledge</span>
                        </button>
                        <div className="thumbs-group">
                          <button className="icon-thumb">
                            <ThumbsUp size={13} />
                          </button>
                          <button className="icon-thumb">
                            <ThumbsDown size={13} />
                          </button>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Input Box Bottom */}
      <form className="chat-input-container" onSubmit={handleSend}>
        <button type="button" className="attach-btn">
          <Paperclip size={18} />
        </button>
        <input
          type="text"
          className="main-prompt-input"
          placeholder="Ask a follow-up question..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
        />
        <div className="input-right-controls">
          <div className="small-model-chip">
            <span>Llama 3.1 8B</span>
            <ChevronDown size={12} />
          </div>
          <button type="submit" className="send-btn-round" disabled={loading}>
            <Send size={16} />
          </button>
        </div>
      </form>
    </div>
  );
}
