import React, { useState, useRef } from 'react';
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
  ShieldAlert,
  Loader2,
  Sparkles,
  UploadCloud,
  X,
  FileSpreadsheet,
  FileCode,
  ShieldCheck,
  Zap,
  Activity,
  Cpu
} from 'lucide-react';
import { sendChatMessage, uploadDocument, approveHitlAction, sendFeedback } from '../services/api';

const AVAILABLE_MODELS = [
  { id: 'Qwen 2.5 7B', type: 'General Reasoning & SOPs', badge: 'Fast', VRAM: '5.2 GB' },
  { id: 'Qwen 2.5 Coder 14B', type: 'Code & Math Analysis', badge: 'High Accuracy', VRAM: '9.8 GB' },
  { id: 'Qwen2-VL 7B', type: 'P&ID & Image Parsing', badge: 'Vision', VRAM: '6.4 GB' },
  { id: 'DeepSeek-R1 Distill 14B', type: 'Complex Industrial Reasoning', badge: 'Reasoning', VRAM: '11.2 GB' }
];

const PROMPT_SUGGESTIONS = [
  {
    title: 'Diagnose Pump P-204 Vibration',
    subtitle: 'Check SOP-017 limits & telemetry',
    prompt: 'P-204 is showing abnormal vibration of 8.2 mm/s. Can you diagnose the cause and recommend SOP actions?'
  },
  {
    title: 'Analyze P&ID Safety Interlocks',
    subtitle: 'Inspect high-pressure isolation valves',
    prompt: 'Analyze line pressure on P&ID diagram and verify emergency shutdown valve (ESV-102) interlock sequence.'
  },
  {
    title: 'Calculate Bearing Replacement Interval',
    subtitle: 'Execute diagnostic Python script',
    prompt: 'Run a thermal vibration degradation model in the sandbox to estimate remaining useful life (RUL) for P-204.'
  }
];

export default function ChatWindow({ activeModel, setActiveModel, onNewResponse, currentUser, onSelectCitation }) {
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [selectedTag, setSelectedTag] = useState('INTERNAL');
  const [showModelPicker, setShowModelPicker] = useState(false);
  const [stagedFiles, setStagedFiles] = useState([]);
  const fileInputRef = useRef(null);
  const chatBottomRef = useRef(null);

  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      reply_title: 'AegisAI Sovereign Workbench Ready',
      diagnosis_summary: 'System initialized in full air-gapped sovereign mode. All local LLMs (Qwen 2.5 / DeepSeek R1), Hybrid RAG vector store, and sandbox tools are running on-premise with 0 outbound network calls.',
      metrics: {
        tag: 'P-204',
        vibration: '8.2 mm/s',
        vibration_status: 'Critical',
        threshold: '> 7.1 mm/s',
        temp: '74 °C',
        status: 'Running'
      },
      recommended_action: {
        title: 'Schedule Immediate Inspection & Isolation',
        sop: 'Follow SOP-017: Pump Maintenance',
        requires_approval: true,
        steps: [
          'Verify sensor readings and confirm vibration trend.',
          'Isolate and shut down the pump (requires HITL Approval).',
          'Perform mechanical inspection (bearing, coupling, alignment).',
          'Replace/repair as needed based on findings.'
        ],
        why_reasoning: [
          'Vibration (8.2 mm/s) exceeds critical threshold (>7.1 mm/s) from SOP-017 (p.4).',
          'Historical records show similar vibration pattern in the last 3 months.',
          'P&ID confirms P-204 is a critical pump in main process line A.'
        ]
      },
      citations: [
        { document: 'SOP-017 - Pump Maintenance', page: 'Page 4 • Section 3.2', tag: 'CONFIDENTIAL', type: 'pdf' },
        { document: 'P-204 Manual', page: 'Page 28 • Vibration Limits', tag: 'INTERNAL', type: 'doc' },
        { document: 'Maintenance History Log', page: 'Page 6 • 12 Mar 2025', tag: 'RESTRICTED', type: 'doc' }
      ]
    }
  ]);

  const scrollToBottom = () => {
    setTimeout(() => {
      chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, 100);
  };

  const handleFileUpload = async (e) => {
    const files = Array.from(e.target.files || []);
    if (!files.length) return;

    setUploading(true);
    for (const file of files) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'user',
          content: `📄 Uploading document to Sovereign RAG: ${file.name} [Tag: ${selectedTag}]`
        }
      ]);

      try {
        const res = await uploadDocument(file, selectedTag);
        setMessages((prev) => [
          ...prev,
          {
            role: 'assistant',
            reply_title: 'Document Ingestion Complete',
            diagnosis_summary: `Successfully ingested "${res.filename}" into the Hybrid RAG engine. Indexed ${res.chunks_indexed} layout-aware chunks with dual-vector embeddings (Dense + Sparse BM25). Encrypted and tagged as ${res.classification_tag}.`,
            recommended_action: {
              title: 'Document Ready for Querying & Citation',
              sop: 'Sovereign Knowledge Base Updated',
              requires_approval: false,
              steps: ['Ask questions regarding this document in the prompt bar below.'],
              why_reasoning: [res.message || 'Indexed without external calls. Data remains strictly on-premise.']
            },
            citations: [
              { document: res.filename, page: `Page 1+ (${res.chunks_indexed} chunks)`, tag: res.classification_tag, type: 'pdf' }
            ]
          }
        ]);
        scrollToBottom();
      } catch (err) {
        console.error('File upload error:', err);
        setMessages((prev) => [
          ...prev,
          {
            role: 'assistant',
            reply_title: 'Ingestion Error',
            diagnosis_summary: `Failed to ingest document "${file.name}": ${err.response?.data?.detail || err.message}`
          }
        ]);
      }
    }
    setUploading(false);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleApproveAction = async (msgIndex) => {
    try {
      const targetMsg = messages[msgIndex];
      const res = await approveHitlAction({
        action_id: `ACT-${Date.now().toString().slice(-4)}`,
        equipment_tag: targetMsg?.metrics?.tag || 'P-204',
        approved_by: currentUser?.username || 'Operator',
        comments: 'Engineer confirmed shutdown & isolation under SOP-017'
      });

      setMessages((prev) =>
        prev.map((m, idx) => {
          if (idx === msgIndex && m.recommended_action) {
            return {
              ...m,
              recommended_action: {
                ...m.recommended_action,
                requires_approval: false,
                approved: true,
                approval_hash: res.entry_hash
              }
            };
          }
          return m;
        })
      );
      alert(`HITL Action Approved & Written to Cryptographic Audit Chain!\nEntry Hash: ${res.entry_hash ? res.entry_hash.substring(0, 24) + '...' : res.id}`);
    } catch (err) {
      console.error(err);
      alert('Failed to approve action: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleSend = async (e, textOverride = null) => {
    if (e) e.preventDefault();
    const queryText = textOverride || input;
    if (!queryText.trim() || loading) return;

    setMessages((prev) => [...prev, { role: 'user', content: queryText }]);
    if (!textOverride) setInput('');
    setLoading(true);
    scrollToBottom();

    try {
      const data = await sendChatMessage({
        message: queryText,
        model_override: activeModel
      });

      const assistantMsg = {
        role: 'assistant',
        reply_title: data.reply_title || 'Industrial Analysis Summary',
        diagnosis_summary: data.diagnosis_summary,
        classification_level: data.classification_level,
        metrics: data.equipment_details
          ? {
              tag: data.equipment_details.tag,
              vibration: data.equipment_details.vibration_val,
              vibration_status: data.equipment_details.vibration_status,
              threshold: data.equipment_details.threshold,
              temp: data.equipment_details.temp,
              status: data.equipment_details.status
            }
          : null,
        recommended_action: data.recommended_action
          ? {
              title: data.recommended_action.title,
              sop: `Follow ${data.recommended_action.sop_code || 'SOP-017'}`,
              requires_approval: data.recommended_action.requires_approval ?? data.hitl_approval_required,
              steps: data.recommended_action.steps || [],
              why_reasoning: data.recommended_action.why_reasoning || []
            }
          : null,
        citations: (data.citations || []).map((c) => ({
          document: c.document,
          page: `Page ${c.page}`,
          tag: c.tag || 'INTERNAL',
          snippet: c.snippet,
          type: 'pdf'
        }))
      };

      setMessages((prev) => [...prev, assistantMsg]);
      if (onNewResponse) onNewResponse(data);
      scrollToBottom();
    } catch (err) {
      console.error(err);
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          reply_title: 'Execution Error',
          diagnosis_summary: `Error executing query against on-premise model: ${err.response?.data?.detail || err.message}`
        }
      ]);
    } finally {
      setLoading(false);
      scrollToBottom();
    }
  };

  return (
    <div className="main-chat-area">
      {/* Top Banner Bar */}
      <div className="agent-banner">
        <div className="agent-banner-left">
          <div className="agent-avatar">
            <Wrench size={18} />
          </div>
          <div>
            <div className="agent-title-row">
              <h2>Maintenance & Engineering Agent</h2>
              <span className="online-badge">• Sovereign Engine Active</span>
            </div>
            <p className="agent-desc">
              On-Premise Industrial Diagnostics • Multimodal RAG • Tamper-Evident HITL Audit
            </p>
          </div>
        </div>

        <div className="agent-banner-right">
          {/* Model Dropdown Trigger */}
          <div className="model-selector-wrapper">
            <button
              className="model-selector-btn"
              onClick={() => setShowModelPicker(!showModelPicker)}
            >
              <Cpu size={16} color="#3b82f6" />
              <span>{activeModel || 'Qwen 2.5 7B'}</span>
              <span className="sub-model">On-Prem GPU</span>
              <ChevronDown size={14} />
            </button>

            {showModelPicker && (
              <div className="model-dropdown-menu">
                <div className="dropdown-title">Select Sovereign LLM Model</div>
                {AVAILABLE_MODELS.map((m) => (
                  <div
                    key={m.id}
                    className={`model-option-item ${activeModel === m.id ? 'active' : ''}`}
                    onClick={() => {
                      if (setActiveModel) setActiveModel(m.id);
                      setShowModelPicker(false);
                    }}
                  >
                    <div className="model-option-head">
                      <span className="m-name">{m.id}</span>
                      <span className="m-badge">{m.badge}</span>
                    </div>
                    <div className="model-option-sub">
                      <span>{m.type}</span>
                      <span className="vram-tag">{m.VRAM}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          <button className="tools-btn" onClick={() => handleSend(null, 'Run system diagnostics on P-204')}>
            <Sparkles size={14} color="#00f2fe" />
            <span>Auto Diagnostics</span>
          </button>

          <button className="icon-btn-ghost" title="Expand View">
            <Maximize2 size={16} />
          </button>
        </div>
      </div>

      {/* Messages Thread Container */}
      <div className="chat-messages-container">
        <div className="breadcrumb-nav">
          <span>Maintenance Workbench</span>
          <ChevronRight size={14} />
          <span>Industrial RAG Thread</span>
          <ChevronRight size={14} />
          <span className="active">P-204 Real-Time Diagnostic</span>
        </div>

        {/* Quick Suggestion Pills */}
        <div className="suggestions-grid">
          {PROMPT_SUGGESTIONS.map((s, idx) => (
            <div
              key={idx}
              className="suggestion-card"
              onClick={() => handleSend(null, s.prompt)}
            >
              <div className="sug-head">
                <Zap size={14} color="#3b82f6" />
                <span>{s.title}</span>
              </div>
              <div className="sug-sub">{s.subtitle}</div>
            </div>
          ))}
        </div>

        {messages.map((msg, idx) => (
          <div key={idx} className="message-wrapper">
            {msg.role === 'user' ? (
              <div className="user-message-row">
                <div className="user-avatar-small">
                  {currentUser?.username ? currentUser.username.substring(0, 2).toUpperCase() : 'OP'}
                </div>
                <div className="user-bubble">
                  {msg.content}
                  <div className="time-stamp">Logged • Sovereign Local Thread</div>
                </div>
              </div>
            ) : (
              <div className="assistant-message-card">
                <div className="assistant-header-bar">
                  <div className="agent-badge-icon">A</div>
                  <div className="status-pill">
                    <CheckCircle2 size={14} color="#10b981" />
                    <span>Inference Verified</span>
                  </div>
                  <span className="dot-divider">•</span>
                  <span className="trace-link">Model: {activeModel || 'Qwen 2.5'} • 0 Egress</span>
                  {msg.classification_level && (
                    <span className={`doc-tag-badge ${msg.classification_level}`} style={{ marginLeft: 'auto' }}>
                      {msg.classification_level}
                    </span>
                  )}
                </div>

                <div className="card-body-content">
                  <h3 className="card-title">{msg.reply_title || 'Diagnosis Summary'}</h3>
                  <p className="summary-paragraph">{msg.diagnosis_summary}</p>

                  {/* Telemetry Metrics Grid */}
                  {msg.metrics && (
                    <div className="metrics-grid">
                      <div className="metric-box">
                        <div className="metric-label">Equipment Tag</div>
                        <div className="metric-value">{msg.metrics.tag || 'P-204'}</div>
                      </div>

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

                  {/* Recommended Action Card */}
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
                        {msg.recommended_action.requires_approval ? (
                          <button className="approval-badge clickable" onClick={() => handleApproveAction(idx)}>
                            <ShieldCheck size={14} />
                            <span>Approve HITL Action</span>
                            <ChevronRight size={14} />
                          </button>
                        ) : msg.recommended_action.approved ? (
                          <div className="approval-badge approved">
                            <CheckCircle2 size={14} color="#10b981" />
                            <span>Approved & Audit Logged</span>
                          </div>
                        ) : null}
                      </div>

                      <ol className="action-steps-list">
                        {msg.recommended_action.steps.map((step, i) => (
                          <li key={i}>{step}</li>
                        ))}
                      </ol>

                      {/* Reasoning Accordion */}
                      {msg.recommended_action.why_reasoning?.length > 0 && (
                        <div className="why-accordion">
                          <div className="accordion-header">
                            <ChevronRight size={14} />
                            <span>Sovereign RAG Rationale & SOP Compliance</span>
                          </div>
                          <ul className="why-list">
                            {msg.recommended_action.why_reasoning.map((why, i) => (
                              <li key={i}>{why}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Citations & Evidence Section */}
                  {msg.citations && msg.citations.length > 0 && (
                    <div className="citations-section">
                      <div className="citations-header">
                        <span>Retrieved Citations ({msg.citations.length})</span>
                      </div>

                      <div className="citations-cards-row">
                        {msg.citations.map((c, i) => (
                          <div key={i} className="citation-card-item clickable" onClick={() => onSelectCitation && onSelectCitation(c)}>
                            <FileText size={16} color="#3b82f6" />
                            <div style={{ flex: 1, minWidth: 0 }}>
                              <div className="citation-doc-name">{c.document}</div>
                              <div className="citation-doc-page">
                                Page {c.page} {c.section_title ? `• ${c.section_title}` : ''}
                              </div>
                            </div>
                            <span className={`doc-tag-badge ${c.tag}`}>{c.tag}</span>
                          </div>
                        ))}
                      </div>

                      <div className="message-action-bar">
                        <button className="action-btn-pill" onClick={() => navigator.clipboard.writeText(msg.diagnosis_summary)}>
                          <Copy size={13} />
                          <span>Copy Response</span>
                        </button>
                        <button className="action-btn-pill" onClick={() => alert('Saved citation package to local knowledge base!')}>
                          <Bookmark size={13} />
                          <span>Save Knowledge</span>
                        </button>
                        <div className="thumbs-group">
                          <button
                            className={`icon-thumb ${msg.user_feedback === 'thumbs_up' ? 'active' : ''}`}
                            onClick={async () => {
                              try {
                                await sendFeedback({ rating: 'thumbs_up', query: msg.reply_title });
                                alert('Thank you! Positively logged in audit ledger.');
                              } catch (e) {
                                console.error(e);
                              }
                            }}
                          >
                            <ThumbsUp size={13} />
                          </button>
                          <button
                            className={`icon-thumb ${msg.user_feedback === 'thumbs_down' ? 'active' : ''}`}
                            onClick={async () => {
                              try {
                                await sendFeedback({ rating: 'thumbs_down', query: msg.reply_title });
                                alert('Feedback recorded for model refinement.');
                              } catch (e) {
                                console.error(e);
                              }
                            }}
                          >
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
        <div ref={chatBottomRef} />
      </div>

      {/* Bottom Input Area */}
      <form className="chat-input-container" onSubmit={(e) => handleSend(e)}>
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileUpload}
          accept=".pdf,.png,.jpg,.jpeg,.doc,.docx"
          multiple
          style={{ display: 'none' }}
        />

        {/* Classification Tag Selector */}
        <div className="tag-selector-wrapper">
          <label className="tag-select-label">RBAC Tag:</label>
          <select
            value={selectedTag}
            onChange={(e) => setSelectedTag(e.target.value)}
            className={`tag-select-dropdown ${selectedTag}`}
          >
            <option value="INTERNAL">INTERNAL</option>
            <option value="RESTRICTED">RESTRICTED</option>
            <option value="CONFIDENTIAL">CONFIDENTIAL</option>
          </select>
        </div>

        <button
          type="button"
          className="attach-btn"
          onClick={() => fileInputRef.current?.click()}
          disabled={uploading}
          title="Upload Document / PDF / Image to Sovereign Vector DB"
        >
          {uploading ? <Loader2 size={18} className="animate-spin" /> : <Paperclip size={18} />}
        </button>

        <input
          type="text"
          className="main-prompt-input"
          placeholder="Ask anything, query SOPs, or upload documents..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={loading}
        />

        <div className="input-right-controls">
          <div className="small-model-chip" onClick={() => setShowModelPicker(!showModelPicker)}>
            <span>{activeModel || 'Qwen 2.5 7B'}</span>
            <ChevronDown size={12} />
          </div>
          <button type="submit" className="send-btn-round" disabled={loading || !input.trim()}>
            {loading ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
          </button>
        </div>
      </form>
    </div>
  );
}

