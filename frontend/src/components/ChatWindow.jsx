import React, { useState } from 'react';
import { Send, FileText, Bot, User, Sparkles } from 'lucide-react';
import { sendChatMessage } from '../services/api';

export default function ChatWindow({ activeModel }) {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: 'Welcome to **AegisAI Sovereign Workbench**. Query confidential technical SOPs, upload engineering drawings, or execute multi-step analysis fully offline.',
      citations: [
        {
          document: 'Aegis_Security_Architecture.pdf',
          page: 1,
          tag: 'CONFIDENTIAL',
          snippet: 'Air-gapped deployment verified: zero outbound telemetry.'
        }
      ]
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMsg = { role: 'user', content: input };
    setMessages((prev) => [...prev, userMsg]);
    const currentInput = input;
    setInput('');
    setLoading(true);

    try {
      const data = await sendChatMessage({
        message: currentInput,
        model_override: activeModel
      });

      const assistantMsg = {
        role: 'assistant',
        content: data.reply,
        citations: data.citations || [],
        tag: data.classification_level
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: '⚠️ Unable to connect to AegisAI Backend. Ensure FastAPI service is running at http://localhost:8000.'
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="main-chat-area">
      <div className="chat-messages">
        {messages.map((msg, index) => (
          <div
            key={index}
            className={`message-bubble ${msg.role === 'user' ? 'message-user' : 'message-assistant'}`}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px', fontSize: '0.78rem', color: '#94a3b8' }}>
              {msg.role === 'user' ? <User size={14} color="#00f2fe" /> : <Bot size={14} color="#10b981" />}
              <span style={{ fontWeight: '600' }}>{msg.role === 'user' ? 'Operator' : 'AegisAI Agent'}</span>
              {msg.tag && (
                <span className={`tag-${msg.tag.toLowerCase()}`}>
                  {msg.tag}
                </span>
              )}
            </div>

            <div>{msg.content}</div>

            {msg.citations && msg.citations.length > 0 && (
              <div style={{ marginTop: '10px', display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                {msg.citations.map((c, i) => (
                  <div key={i} className="citation-chip">
                    <FileText size={12} />
                    <span>{c.document} (p. {c.page})</span>
                    <span className="tag-confidential">{c.tag}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
        {loading && (
          <div className="message-bubble message-assistant" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Sparkles size={14} className="spin" color="#00f2fe" />
            <span style={{ fontSize: '0.85rem', color: '#94a3b8' }}>Agent is reasoning locally using {activeModel}...</span>
          </div>
        )}
      </div>

      <form className="chat-input-area" onSubmit={handleSend}>
        <input
          type="text"
          className="chat-input"
          placeholder={`Ask AegisAI anything (using ${activeModel})...`}
          value={input}
          onChange={(e) => setInput(e.target.value)}
        />
        <button type="submit" className="btn-primary" disabled={loading}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Send size={16} />
            <span>Send</span>
          </div>
        </button>
      </form>
    </div>
  );
}
