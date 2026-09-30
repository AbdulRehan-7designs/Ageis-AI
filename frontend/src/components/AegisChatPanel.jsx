import React, { useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { SendHorizonal, Sparkles, ShieldCheck, Trash2, RotateCcw, Copy, Check, Keyboard, Search, FileText, Activity, ChevronDown, Square } from 'lucide-react';
import {
  createConversation,
  fetchConversation,
  fetchConversations,
  sendChatMessageStream,
} from '../services/api';
import AegisCitationBadge from './AegisCitationBadge';
import AegisMessageBubble from './AegisMessageBubble';
import AegisDocFilterBar from './AegisDocFilterBar';
import { Spokes } from './Spokes';

const SUGGESTED_PROMPTS = [
  'Summarize the latest authorized maintenance evidence.',
  'What does the indexed procedure say about vibration limits?',
  'Find the relevant inspection steps for this equipment.',
];

export default function AegisChatPanel({
  activeModel,
  currentResponse,
  currentUser,
  citations = [],
  uploadedDocuments = [],
  onSelectCitation,
  onResponseReceived,
  activeFilter = 'all',
  onFilterChange,
  filterOptions = [],
}) {
  const navigate = useNavigate();
  const { conversationId } = useParams();
  const [conversations, setConversations] = useState([]);
  const [conversationState, setConversationState] = useState('LOADING');
  const [messages, setMessages] = useState([]);
  const [draft, setDraft] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [requestStatus, setRequestStatus] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const [lastFailedPrompt, setLastFailedPrompt] = useState('');
  const [copiedMessageId, setCopiedMessageId] = useState(null);
  const abortControllerRef = useRef(null);
  const lastResponseState = currentResponse?.evidence_state || null;
  const sourceChainLabel = !currentResponse
    ? 'Source chain ready'
    : lastResponseState === 'grounded'
      ? 'Sources verified'
      : lastResponseState === 'conflicting_evidence'
        ? 'Conflicting sources'
        : lastResponseState === 'insufficient_evidence'
          ? 'Evidence insufficient'
          : currentResponse.retrieval_trace?.length
            ? 'Retrieval complete'
            : 'Retrieval not required';

  const restoreMessage = (message) => ({
    id: message.message_id,
    role: message.role.toLowerCase(),
    content: message.content,
    citations: message.metadata?.citations || [],
    evidenceBlocks: message.metadata?.evidence_blocks || [],
    evidenceConfidence: message.metadata?.evidence_confidence,
    evidenceState: message.metadata?.evidence_state,
    evidenceWarnings: message.metadata?.evidence_warnings || [],
  });

  useEffect(() => {
    let cancelled = false;
    setConversationState('LOADING');
    setMessages([]);
    fetchConversations()
      .then((items) => {
        if (cancelled) return;
        setConversations(items || []);
        if (!conversationId) {
          setConversationState('EMPTY');
          return;
        }
        return fetchConversation(conversationId);
      })
      .then((conversation) => {
        if (cancelled || !conversation) return;
        const restored = (conversation.messages || []).map(restoreMessage);
        setMessages(restored);
        const lastAssistant = [...restored].reverse().find((message) => message.role === 'assistant');
        if (lastAssistant && onResponseReceived) {
          onResponseReceived({
            diagnosis_summary: lastAssistant.content,
            citations: lastAssistant.citations,
            evidence_blocks: lastAssistant.evidenceBlocks,
            evidence_confidence: lastAssistant.evidenceConfidence,
            evidence_state: lastAssistant.evidenceState,
            evidence_warnings: lastAssistant.evidenceWarnings,
          });
        }
        setConversationState('READY');
      })
      .catch((error) => {
        if (cancelled) return;
        setConversationState(error?.response?.status === 404 ? 'NOT_FOUND' : 'ERROR');
        setErrorMessage('Unable to load this conversation from the server.');
      });
    return () => {
      cancelled = true;
    };
  }, [conversationId]);

  const openConversation = (id) => navigate(`/workspace/chat/${id}`);

  const handleNewConversation = async () => {
    setErrorMessage('');
    try {
      const conversation = await createConversation();
      setConversations((items) => [conversation, ...items]);
      openConversation(conversation.conversation_id);
    } catch {
      setErrorMessage('Unable to create a conversation on the server.');
    }
  };

  const quoteCitations = useMemo(() => citations.slice(0, 3), [citations]);

  const handleSend = async (prompt = draft) => {
    if (!prompt.trim() || isSending) return;
    let activeConversationId = conversationId;
    if (!activeConversationId) {
      try {
        const conversation = await createConversation();
        activeConversationId = conversation.conversation_id;
        setConversations((items) => [conversation, ...items]);
        openConversation(activeConversationId);
      } catch {
        setErrorMessage('Unable to create a conversation on the server.');
        return;
      }
    }
    const userMessage = { role: 'user', content: prompt.trim(), citations: [] };
    setMessages((prev) => [...prev, userMessage]);
    setDraft('');
    setIsSending(true);
    setErrorMessage('');
    setLastFailedPrompt('');
    setRequestStatus('Request accepted by Aegis services.');
    abortControllerRef.current = new AbortController();

    const streamMessageId = globalThis.crypto?.randomUUID?.() || `stream-${Date.now()}`;
    const assistantMessage = {
      id: streamMessageId,
      role: 'assistant',
      content: '',
      citations: [],
      streaming: true,
    };
    setMessages((prev) => [...prev, assistantMessage]);

    try {
      const payload = {
        message: userMessage.content,
        conversation_id: activeConversationId,
        model_override: activeModel || 'auto',
      };

      await sendChatMessageStream(
        payload,
        (chunk) => {
          if (chunk.includes('Retrieving authorized evidence')) {
            setRequestStatus('Searching authorized engineering evidence…');
          } else if (chunk.trim()) {
            setRequestStatus('Generating grounded response…');
          }
          setMessages((prev) => prev.map((msg) =>
            msg.id === streamMessageId
              ? { ...msg, content: (msg.content || '') + chunk }
              : msg
          ));
        },
        (result) => {
          setRequestStatus('Response complete.');
          const finalContent = result?.diagnosis_summary || result?.reply_title || 'I analyzed the evidence and will return a traceable answer.';
          setMessages((prev) => prev.map((msg) =>
            msg.id === streamMessageId
              ? { ...msg, content: finalContent, citations: result?.citations || [], evidenceBlocks: result?.evidence_blocks || [], evidenceConfidence: result?.evidence_confidence, evidenceState: result?.evidence_state, evidenceWarnings: result?.evidence_warnings || [], streaming: false }
              : msg
          ));
          fetchConversation(activeConversationId).then((conversation) => {
            setMessages((conversation.messages || []).map(restoreMessage));
            setConversations((items) => items.map((item) => item.conversation_id === activeConversationId ? conversation : item));
          }).catch(() => setErrorMessage('Response completed, but conversation history could not be refreshed.'));
          if (onResponseReceived) onResponseReceived(result);
        },
        (status) => setRequestStatus(status || 'Processing request…'),
        abortControllerRef.current.signal
      );
    } catch (error) {
      if (error?.name === 'AbortError') {
        setRequestStatus('Generation stopped.');
        setMessages((prev) => prev.filter((msg) => msg.id !== streamMessageId));
        return;
      }
      setErrorMessage(error?.message || 'Aegis services could not complete this request.');
      setLastFailedPrompt(userMessage.content);
      setRequestStatus('Request failed.');
      setMessages((prev) => prev.filter((msg) => msg.id !== streamMessageId));
    } finally {
      abortControllerRef.current = null;
      setIsSending(false);
    }
  };

  const stopGeneration = () => {
    abortControllerRef.current?.abort();
  };

  const clearConversation = () => {
    if (isSending) return;
    setMessages([]);
    setErrorMessage('');
    setRequestStatus('');
  };

  const copyMessage = async (message) => {
    try {
      await navigator.clipboard.writeText(message.content || '');
      setCopiedMessageId(message.id || message.content);
      window.setTimeout(() => setCopiedMessageId(null), 1400);
    } catch {
      setErrorMessage('The browser did not allow copying this response.');
    }
  };

  return (
    <main className="aegis-chat-panel">
      <div className="aegis-chat-header">
        <div>
          <span className="aegis-eyebrow">Evidence-first operations</span>
          <h2>Maintenance Intelligence Workspace</h2>
        </div>
        <div className={`aegis-header-status ${lastResponseState || 'ready'}`}>
          <ShieldCheck size={14} />
          <span>{sourceChainLabel}</span>
        </div>
      </div>

      <AegisDocFilterBar
        totalDocs={Math.max(citations.length, uploadedDocuments.length)}
        activeModel={activeModel}
        filterOptions={filterOptions}
        activeFilter={activeFilter}
        onFilterChange={onFilterChange}
      />

      <div className="aegis-chat-toolbar">
        <div className="aegis-chat-toolbar-status">
          {isSending && <Spokes className="aegis-spokes" style={{ '--duration': '0.8s' }} />}
          <span>{requestStatus || 'Ready for an evidence-backed request.'}</span>
        </div>
        <button type="button" className="aegis-quiet-btn" onClick={clearConversation} disabled={isSending}>
          <Trash2 size={13} /> Clear
        </button>
      </div>

      <div className="aegis-chat-toolbar">
        <button type="button" className="aegis-quiet-btn" onClick={handleNewConversation}>New Conversation</button>
        <select value={conversationId || ''} onChange={(event) => event.target.value && openConversation(event.target.value)} aria-label="Saved conversations">
          <option value="">Select saved conversation</option>
          {conversations.map((conversation) => (
            <option key={conversation.conversation_id} value={conversation.conversation_id}>
              {conversation.title} · {new Date(conversation.updated_at).toLocaleString()}
            </option>
          ))}
        </select>
      </div>

      {conversationState === 'ERROR' && <div className="aegis-chat-error"><span>Conversation history is unavailable.</span></div>}
      {conversationState === 'NOT_FOUND' && <div className="aegis-chat-error"><span>Conversation not found or not authorized.</span></div>}
      {conversationState !== 'LOADING' && !messages.length && !isSending && (
        <div className="aegis-chat-empty">
          <div className="aegis-chat-empty-icon"><Search size={22} /></div>
          <strong>Ask Aegis about your authorized knowledge base</strong>
          <p>Search authorized procedures, maintenance history, drawings, and indexed evidence.</p>
          <div className="aegis-suggestion-grid">
            {SUGGESTED_PROMPTS.map((prompt, index) => (
              <button type="button" key={prompt} onClick={() => setDraft(prompt)}>
                {index === 0 ? <Activity size={13} /> : <FileText size={13} />}
                <span>{prompt}</span>
                <ChevronDown size={13} />
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="aegis-citation-row">
        {quoteCitations.length ? (
          quoteCitations.map((citation, index) => (
            <AegisCitationBadge key={`${citation.document || 'source'}-${index}`} citation={citation} onClick={onSelectCitation} />
          ))
        ) : (
          <span className="aegis-empty-inline">No evidence selected</span>
        )}
      </div>

      <div className="aegis-conversation">
        {messages.map((message, index) => (
          <div className="aegis-message-with-actions" key={`${message.role}-${message.id || index}`}>
            <AegisMessageBubble
              role={message.role}
              content={message.content}
              streaming={message.streaming}
              citations={message.citations || []}
              evidenceBlocks={message.evidenceBlocks || []}
              evidenceConfidence={message.evidenceConfidence}
              evidenceState={message.evidenceState}
              evidenceWarnings={message.evidenceWarnings || []}
            />
            {message.role === 'assistant' && message.content && !message.streaming && (
              <div className="aegis-message-actions">
                <button type="button" className="aegis-message-action" onClick={() => copyMessage(message)}>
                  {copiedMessageId === (message.id || message.content) ? <Check size={12} /> : <Copy size={12} />}
                  {copiedMessageId === (message.id || message.content) ? 'Copied' : 'Copy'}
                </button>
                {index > 0 && messages[index - 1]?.role === 'user' && (
                  <button type="button" className="aegis-message-action" onClick={() => handleSend(messages[index - 1].content)} disabled={isSending}>
                    <RotateCcw size={12} /> Retry
                  </button>
                )}
              </div>
            )}
          </div>
        ))}
      </div>

      {errorMessage && (
        <div className="aegis-chat-error">
          <span>{errorMessage}</span>
          {lastFailedPrompt && <button type="button" onClick={() => handleSend(lastFailedPrompt)}><RotateCcw size={13} /> Retry</button>}
        </div>
      )}

      <div className="aegis-composer">
        <textarea
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === 'Enter' && !event.shiftKey) {
              event.preventDefault();
              handleSend();
            }
          }}
          rows={3}
          placeholder="Ask about an asset, procedure, drawing, or maintenance event…"
        />
        <div className="aegis-composer-actions">
          <div className="aegis-composer-meta">
            {isSending ? <Spokes className="aegis-spokes" style={{ '--duration': '0.8s' }} /> : <Sparkles size={14} />}
            <span>{isSending ? requestStatus : 'Evidence-grounded answers'}</span>
            {!isSending && <span className="aegis-key-hint"><Keyboard size={12} /> Enter to send · Shift+Enter for new line</span>}
          </div>
          {isSending ? (
            <button className="aegis-send-btn stop" onClick={stopGeneration}>
              <Square size={14} />
              <span>Stop</span>
            </button>
          ) : (
            <button className="aegis-send-btn" onClick={handleSend} disabled={!draft.trim()}>
              <SendHorizonal size={16} />
              <span>Send</span>
            </button>
          )}
        </div>
      </div>
    </main>
  );
}
