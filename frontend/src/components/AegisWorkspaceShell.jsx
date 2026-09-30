import React, { useMemo, useState } from 'react';
import AegisSidebarNav from './AegisSidebarNav';
import AegisChatPanel from './AegisChatPanel';
import AegisSourcePanel from './AegisSourcePanel';
import { Bell, Search, ShieldCheck, Sun, MessageSquare, Database, PanelsTopLeft, ScrollText, Cpu, Menu } from 'lucide-react';

export default function AegisWorkspaceShell({
  activeModel,
  setActiveModel,
  currentUser,
  systemHealth,
  egressSnapshot,
  currentResponse,
  uploadedDocuments = [],
  selectedCitation: externallySelectedCitation,
  onSelectCitation,
  onSelectDocument,
  onResponseReceived,
  onSelectRole,
  onOpenAudit,
  onOpenSandbox,
  onOpenKnowledgeHub,
}) {
  const citations = currentResponse?.citations || [];
  const [activeFilter, setActiveFilter] = useState('all');
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [activeView, setActiveView] = useState('chat');

  const topNav = [
    { id: 'chat', label: 'Chat', icon: MessageSquare },
    { id: 'knowledge', label: 'Knowledge', icon: Database },
    { id: 'evidence', label: 'Evidence', icon: PanelsTopLeft },
    { id: 'audit', label: 'Audit', icon: ScrollText },
    { id: 'models', label: 'Models', icon: Cpu },
  ];

  const handleTopNav = (view) => {
    setActiveView(view);
    if (view === 'knowledge' && onOpenKnowledgeHub) onOpenKnowledgeHub();
    if (view === 'audit' && onOpenAudit) onOpenAudit();
  };

  const filterOptions = useMemo(() => {
    const options = [
      { id: 'all', label: 'All Sources' },
      { id: 'documents', label: 'Documents' },
      { id: 'drawings', label: 'Drawings' },
    ];
    const objectTags = [...new Set(citations.map((citation) => citation.object_tag || citation.target?.tag).filter(Boolean))];
    objectTags.slice(0, 3).forEach((tag) => {
      options.push({ id: `tag:${tag}`, label: tag });
    });
    return options;
  }, [citations]);

  const filteredCitations = useMemo(() => {
    if (activeFilter === 'documents') {
      return citations.filter((citation) => citation.document_type !== 'engineering_drawing');
    }
    if (activeFilter === 'drawings') {
      return citations.filter((citation) => citation.document_type === 'engineering_drawing' || citation.drawing_type);
    }
    if (activeFilter.startsWith('tag:')) {
      const tag = activeFilter.replace('tag:', '');
      return citations.filter((citation) => (citation.object_tag || citation.target?.tag) === tag);
    }
    return citations;
  }, [activeFilter, citations]);

  const selectedCitation = externallySelectedCitation || filteredCitations[0] || null;

  return (
    <div className="aegis-shell">
      <header className="aegis-topbar">
        <button type="button" className="aegis-mobile-menu" onClick={() => setSidebarCollapsed((value) => !value)} aria-label="Toggle navigation">
          <Menu size={18} />
        </button>
        <div className="aegis-brand-wrap">
          <div className="aegis-brand-mark">A</div>
          <div className="aegis-brand-copy">
            <h1>Ageis AI</h1>
            <span>Sovereign Agentic AI Workbench</span>
          </div>
        </div>

        <div className="aegis-global-search">
          <Search size={15} />
          <input type="text" placeholder='Ask anything... (e.g., "Diagnose P-204 vibration")' />
          <span className="aegis-search-shortcut">Ctrl + K</span>
        </div>

        <nav className="aegis-top-nav" aria-label="Primary navigation">
          {topNav.map(({ id, label, icon: Icon }) => (
            <button key={id} type="button" className={activeView === id ? 'active' : ''} onClick={() => handleTopNav(id)}>
              <Icon size={14} />
              <span>{label}</span>
            </button>
          ))}
        </nav>

        <div className="aegis-topbar-actions">
          <div className="aegis-sovereign-badge">
            <ShieldCheck size={15} color="#10b981" />
            <div>
              <span className="aegis-sovereign-title">Sovereign Mode</span>
              <small>{egressSnapshot?.sovereign_status || systemHealth?.egress_monitor?.sovereign_status || 'Protected'}</small>
            </div>
          </div>

          <button className="aegis-icon-btn" aria-label="Notifications">
            <Bell size={17} />
            <span className="aegis-notification-dot">3</span>
          </button>

          <button className="aegis-icon-btn" aria-label="Theme toggle">
            <Sun size={17} />
          </button>

          <div className="aegis-user-badge">
            <div className="aegis-avatar">
              {(currentUser?.username || 'US').slice(0, 2).toUpperCase()}
            </div>
            <div className="aegis-user-meta">
              <span>{currentUser?.username || 'Operator'}</span>
              <small>{currentUser?.role || 'ENGINEER'}</small>
            </div>
            {onSelectRole && (
              <select value={currentUser?.role || 'ENGINEER'} onChange={(event) => onSelectRole(event.target.value)}>
                <option value="ADMIN">ADMIN</option>
                <option value="ENGINEER">ENGINEER</option>
                <option value="OPERATOR">OPERATOR</option>
                <option value="AUDITOR">AUDITOR</option>
                <option value="PUBLIC">PUBLIC</option>
              </select>
            )}
          </div>
        </div>
      </header>

      <div className="aegis-shell-body">
        <AegisSidebarNav
          activeModel={activeModel}
          setActiveModel={setActiveModel}
          systemHealth={systemHealth}
          collapsed={sidebarCollapsed}
          onToggleCollapse={() => setSidebarCollapsed((value) => !value)}
          onOpenAudit={onOpenAudit}
          onOpenSandbox={onOpenSandbox}
          onOpenKnowledgeHub={onOpenKnowledgeHub}
        />

        <AegisChatPanel
          activeModel={activeModel}
          currentResponse={currentResponse}
          currentUser={currentUser}
          citations={filteredCitations}
          uploadedDocuments={uploadedDocuments}
          onSelectCitation={onSelectCitation}
          onResponseReceived={onResponseReceived}
          activeFilter={activeFilter}
          onFilterChange={setActiveFilter}
          filterOptions={filterOptions}
        />

        <AegisSourcePanel
          currentResponse={currentResponse}
          currentUser={currentUser}
          systemHealth={systemHealth}
          egressSnapshot={egressSnapshot}
          citations={filteredCitations}
          uploadedDocuments={uploadedDocuments}
          selectedCitation={selectedCitation}
          onSelectCitation={onSelectCitation}
          onSelectDocument={onSelectDocument}
        />
      </div>
    </div>
  );
}
