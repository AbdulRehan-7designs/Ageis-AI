import React, { useEffect, useState } from 'react';
import { Activity, FileText, ShieldCheck, Database, Cpu, ArrowRight } from 'lucide-react';
import { fetchDocumentList, fetchHealthStatus } from '../services/api';

export default function HomeView({ currentUser, systemHealth, onSearch }) {
  const [query, setQuery] = useState('');
  const [documents, setDocuments] = useState([]);
  const [health, setHealth] = useState(systemHealth || null);

  useEffect(() => {
    fetchHealthStatus().then((data) => data && setHealth(data));
    fetchDocumentList().then((items) => setDocuments(items || []));
  }, []);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (query.trim()) {
      onSearch?.(query);
    }
  };

  const ollamaStatus = health?.services?.ollama?.status || 'unreachable';
  const qdrantStatus = health?.services?.qdrant?.status || 'unknown';
  const modelStatus = health?.services?.model_registry?.enabled?.length ? 'configured' : 'unavailable';

  return (
    <div className="wb-home">
      <div className="wb-home-inner">
        <div className="wb-home-header">
          <div className="wb-home-greeting-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" fill="rgba(189,112,53,0.2)"/>
              <circle cx="12" cy="12" r="3" fill="var(--yellow)" stroke="none" />
            </svg>
          </div>
          <div className="wb-home-greeting-text">
            <h1>Good morning, {(currentUser?.name?.split(' ') || [])[0] || 'User'}</h1>
            <p>Live engineering intelligence for authorized documents, assets, and operational evidence.</p>
          </div>
        </div>

        <div className="wb-home-pills">
          <button className="wb-home-pill" onClick={() => onSearch?.('What is the current status of the equipment?')}><Activity size={14} /> System Analysis</button>
          <button className="wb-home-pill" onClick={() => onSearch?.('Show maintenance history for Unit 5')}><FileText size={14} /> SOP status</button>
          <button className="wb-home-pill" onClick={() => onSearch?.('Find the P&ID for the cooling system')}><ShieldCheck size={14} /> Drawings</button>
          <button className="wb-home-pill" onClick={() => onSearch?.('Summarize the latest SOP updates')}><Database size={14} /> Maintenance history</button>
        </div>

        <div className="wb-home-omnibar-wrap">
          <form className="wb-home-omnibar" onSubmit={handleSubmit}>
            <div className="wb-omnibar-top">
              <div className="wb-omnibar-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" width="18" height="18">
                  <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path>
                  <polyline points="3.29 7 12 12 20.71 7"></polyline>
                  <line x1="12" y1="22" x2="12" y2="12"></line>
                </svg>
              </div>
              <input
                type="text"
                placeholder="Ask a question about your equipment, documents or procedures..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
              />
              <button type="submit" className="wb-omnibar-submit" disabled={!query.trim()}>
                <ArrowRight size={16} />
              </button>
            </div>
          </form>
        </div>

        <div className="wb-home-panels">
          <div className="wb-home-card-panel">
            <h3>System status</h3>
            <div className="wb-status-grid">
              <div><span>API</span><strong>{health ? 'online' : 'offline'}</strong></div>
              <div><span>Model provider</span><strong>{ollamaStatus}</strong></div>
              <div><span>Retrieval</span><strong>{qdrantStatus}</strong></div>
              <div><span>Model catalog</span><strong>{modelStatus}</strong></div>
            </div>
          </div>

          <div className="wb-home-card-panel">
            <h3>Recent documents</h3>
            {documents.length ? (
              <ul className="wb-quick-list">
                {documents.slice(0, 4).map((doc, idx) => (
                  <li key={doc.id || doc.doc_name || idx}><FileText size={12} /> {doc.doc_name || doc.name || 'Document'} </li>
                ))}
              </ul>
            ) : (
              <p className="wb-empty-state">Document indexing API not connected.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
