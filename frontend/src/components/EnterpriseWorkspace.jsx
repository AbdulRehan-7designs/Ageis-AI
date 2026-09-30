import React, { useEffect, useMemo, useState } from 'react';
import { Navigate, Route, Routes, useLocation, useNavigate } from 'react-router-dom';
import {
  Activity,
  AlertCircle,
  Archive,
  ChevronRight,
  Cpu,
  FileText,
  Home,
  Menu,
  Network,
  PanelLeftClose,
  PanelLeftOpen,
  Search,
  ShieldCheck,
  Workflow,
} from 'lucide-react';
import AegisChatPanel from './AegisChatPanel';
import AegisSourcePanel from './AegisSourcePanel';
import {
  fetchAuditLogs,
  fetchAgentRuns,
  fetchDocumentList,
  fetchEgressStatus,
  fetchHealthStatus,
  fetchModelCatalog,
  searchDocuments,
  verifyAuditChain,
} from '../services/api';
import './enterprise.css';

const navigation = [
  { group: 'Workspace', items: [
    { id: 'home', label: 'Home', icon: Home },
    { id: 'chat', label: 'Chat', icon: Workflow },
    { id: 'documents', label: 'Documents', icon: FileText },
  ] },
  { group: 'Intelligence', items: [
    { id: 'models', label: 'Models', icon: Cpu },
    { id: 'runs', label: 'Agent Runs', icon: Network },
  ] },
  { group: 'Governance', items: [
    { id: 'audit', label: 'Audit Logs', icon: Archive },
    { id: 'security', label: 'Security', icon: ShieldCheck },
  ] },
  { group: 'System', items: [
  ] },
];

const pageTitles = {
  home: ['Home', 'Industrial intelligence overview'],
  chat: ['Chat', 'Evidence-backed engineering analysis'],
  documents: ['Documents', 'Authorized technical knowledge'],
  models: ['Models', 'Local model registry and availability'],
  runs: ['Agent Runs', 'Traceable orchestration activity'],
  audit: ['Audit Logs', 'Tamper-evident governance activity'],
  security: ['Security', 'Clearance, access, and sovereignty state'],
};

const workspaceRoutes = new Set(['home', 'chat', 'documents', 'models', 'runs', 'audit', 'security']);

function viewFromPath(pathname) {
  const segment = pathname.replace(/^\/workspace\/?/, '').split('/')[0];
  return segment || 'home';
}

function StatusDot({ tone = 'neutral' }) {
  return <span className={`enterprise-status-dot ${tone}`} aria-hidden="true" />;
}

function DataState({ loading, error, empty, children }) {
  if (loading) return <div className="enterprise-state">Loading live Aegis data…</div>;
  if (error) return <div className="enterprise-state error"><AlertCircle size={16} /> {error}</div>;
  if (empty) return <div className="enterprise-state">{empty}</div>;
  return children;
}

function MetricRow({ label, value, tone = 'neutral' }) {
  return (
    <div className="enterprise-metric-row">
      <span><StatusDot tone={tone} />{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function HomePage({ health, egress, documents, audits, onNavigate, currentUser }) {
  const services = health?.services || {};
  const auditCount = Array.isArray(audits) ? audits.length : 0;
  return (
    <div className="enterprise-page">
      <div className="enterprise-page-intro">
        <div>
          <span className="enterprise-eyebrow">Operational workspace</span>
          <h1>Welcome back, {currentUser?.name || currentUser?.username || 'operator'}</h1>
          <p>Review live service health, authorized knowledge, and recent governance activity.</p>
        </div>
        <div className="enterprise-clearance-chip"><ShieldCheck size={15} /> {currentUser?.clearance || 'Unknown clearance'}</div>
      </div>

      <div className="enterprise-action-grid">
        {[
          ['Ask Aegis', 'Start an evidence-backed investigation', 'chat', Workflow],
          ['Search Documents', 'Review the indexed knowledge base', 'documents', Search],
          ['View Agent Runs', 'Inspect the latest execution trace', 'runs', Network],
        ].map(([title, description, id, Icon]) => (
          <button key={id} className="enterprise-action-card" onClick={() => onNavigate(id)}>
            <Icon size={18} />
            <span><strong>{title}</strong><small>{description}</small></span>
            <ChevronRight size={15} />
          </button>
        ))}
      </div>

      <div className="enterprise-dashboard-grid">
        <section className="enterprise-card">
          <div className="enterprise-card-heading"><div><span className="enterprise-eyebrow">Live services</span><h2>System status</h2></div><Activity size={17} /></div>
          <MetricRow label="API" value={health ? health.status || 'online' : 'Unavailable'} tone={health ? 'good' : 'bad'} />
          <MetricRow label="Local model provider" value={services.ollama?.status || 'Unknown'} tone={services.ollama?.status === 'online' ? 'good' : 'warn'} />
          <MetricRow label="Retrieval / vector database" value={services.qdrant?.status || 'Unknown'} tone={services.qdrant?.status === 'online' ? 'good' : 'warn'} />
          <MetricRow label="Egress monitor" value={egress?.sovereign_status || health?.egress_monitor?.sovereign_status || 'Unknown'} tone={egress ? 'good' : 'neutral'} />
        </section>

        <section className="enterprise-card">
          <div className="enterprise-card-heading"><div><span className="enterprise-eyebrow">Governance</span><h2>Recent activity</h2></div><Archive size={17} /></div>
          <DataState loading={false} error={null} empty={auditCount ? null : 'No audit events are available yet.'}>
            <div className="enterprise-activity-list">
              {audits.slice(-5).reverse().map((event, index) => (
                <div className="enterprise-activity-row" key={event.id || `${event.event_type}-${index}`}>
                  <StatusDot tone={event.status === 'FAILED' ? 'bad' : 'good'} />
                  <div><strong>{event.event_type || event.event || 'Audit event'}</strong><small>{event.timestamp || event.created_at || 'Timestamp unavailable'}</small></div>
                </div>
              ))}
            </div>
          </DataState>
        </section>
      </div>

      <section className="enterprise-card">
        <div className="enterprise-card-heading"><div><span className="enterprise-eyebrow">Knowledge base</span><h2>Authorized documents</h2></div><FileText size={17} /></div>
        {documents.length ? (
          <div className="enterprise-document-strip">{documents.slice(0, 6).map((document, index) => (
            <div className="enterprise-document-chip" key={document.id || document.doc_name || index}>
              <FileText size={14} /><span>{document.doc_name || document.name || document.filename || 'Document'}</span>
            </div>
          ))}</div>
        ) : <div className="enterprise-state">Document indexing API returned no documents.</div>}
      </section>
    </div>
  );
}

function DocumentsPage({ documents, loading, error, onSearch }) {
  const [query, setQuery] = useState('');
  const [searching, setSearching] = useState(false);
  const handleSubmit = async (event) => {
    event.preventDefault();
    setSearching(true);
    try {
      await onSearch(query.trim());
    } finally {
      setSearching(false);
    }
  };
  return (
    <div className="enterprise-page">
      <div className="enterprise-page-intro"><div><span className="enterprise-eyebrow">Knowledge workspace</span><h1>Documents</h1><p>Only documents returned by the authorized indexing API are shown.</p></div></div>
      <form className="enterprise-search" onSubmit={handleSubmit}><Search size={16} /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search document names, tags, or metadata" /><button type="submit" disabled={searching}>{searching ? 'Searching…' : 'Search'}</button></form>
      <DataState loading={loading} error={error} empty={!documents.length ? 'No authorized indexed documents match this view.' : null}>
        <div className="enterprise-table-wrap"><table className="enterprise-table"><thead><tr><th>Document</th><th>Type</th><th>Classification</th><th>Asset / tag</th></tr></thead><tbody>{documents.map((document, index) => <tr key={document.id || document.document_name || index}><td><strong>{document.document_name || document.filename || 'Unnamed document'}</strong></td><td>{document.document_type || 'Not provided'}</td><td>{document.classification_tag || 'Not provided'}</td><td>{document.object_tag || (document.equipment_tags || []).join(', ') || 'Not provided'}</td></tr>)}</tbody></table></div>
      </DataState>
    </div>
  );
}

function ModelsPage({ catalog, loading, error }) {
  const models = catalog?.models || [];
  return <div className="enterprise-page"><div className="enterprise-page-intro"><div><span className="enterprise-eyebrow">Model registry</span><h1>Local models</h1><p>Availability and capabilities are read from the backend registry. Routing remains server-controlled.</p></div></div><DataState loading={loading} error={error} empty={!models.length ? 'Model catalog is unavailable.' : null}><div className="enterprise-model-grid">{models.map((model) => <article className="enterprise-model-card" key={model.id}><div className="enterprise-model-heading"><Cpu size={17} /><strong>{model.display_name || model.id}</strong><span className={model.enabled ? 'enterprise-badge good' : 'enterprise-badge'}>{model.enabled ? 'Enabled' : 'Disabled'}</span></div><p>{model.description || 'No description provided by the registry.'}</p><dl><div><dt>Provider</dt><dd>{model.auto ? 'Router controlled' : 'Local registry'}</dd></div><div><dt>Capabilities</dt><dd>{(model.task_types || []).join(', ') || 'Not provided'}</dd></div><div><dt>Runtime tag</dt><dd>{model.ollama_tag || 'Automatic selection'}</dd></div></dl></article>)}</div></DataState></div>;
}

function AuditPage({ audits, loading, error, verification }) {
  return <div className="enterprise-page"><div className="enterprise-page-intro"><div><span className="enterprise-eyebrow">Governance</span><h1>Audit logs</h1><p>Events returned by the backend audit service. Sensitive payloads are not expanded here.</p></div>{verification && <div className="enterprise-clearance-chip"><ShieldCheck size={15} /> Chain {verification.valid ? 'verified' : 'requires review'}</div>}</div><DataState loading={loading} error={error} empty={!audits.length ? 'No audit events are available.' : null}><div className="enterprise-table-wrap"><table className="enterprise-table"><thead><tr><th>Timestamp</th><th>Event</th><th>User</th><th>Status</th><th>Citations</th></tr></thead><tbody>{audits.slice().reverse().map((event, index) => <tr key={event.id || index}><td>{event.timestamp || event.created_at || 'Not provided'}</td><td><strong>{event.event_type || event.event || 'Audit event'}</strong></td><td>{event.username || event.user || 'Not provided'}</td><td>{event.status || 'Not provided'}</td><td>{event.citations_count ?? 'Not provided'}</td></tr>)}</tbody></table></div></DataState></div>;
}

function AgentRunsPage({ runs, loading, error }) {
  return <div className="enterprise-page"><div className="enterprise-page-intro"><div><span className="enterprise-eyebrow">Orchestration</span><h1>Agent runs</h1><p>Execution records returned by the authenticated orchestrator session.</p></div></div><DataState loading={loading} error={error} empty={!runs.length ? 'No agent runs have been recorded for this user.' : null}><div className="enterprise-table-wrap"><table className="enterprise-table"><thead><tr><th>Run</th><th>Task</th><th>Model</th><th>Status</th><th>Created</th></tr></thead><tbody>{runs.slice().reverse().map((run) => <tr key={run.run_id}><td><strong>{run.run_id}</strong></td><td>{run.task}</td><td>{run.model_id || 'Not provided'}</td><td>{run.status}</td><td>{run.created_at}</td></tr>)}</tbody></table></div></DataState></div>;
}

function SecurityPage({ health, egress, currentUser, verification }) {
  const rows = [
    ['Clearance', currentUser?.clearance || 'Not provided'],
    ['RBAC context', currentUser?.clearance_tags?.join(', ') || 'Not provided'],
    ['On-premise / egress', egress?.sovereign_status || health?.egress_monitor?.sovereign_status || 'Not provided'],
    ['External packets blocked', egress?.blocked_count ?? health?.egress_monitor?.external_packets ?? 'Not provided'],
    ['Audit chain', verification ? (verification.valid ? 'Verified' : 'Invalid') : 'Not available'],
  ];
  return <div className="enterprise-page"><div className="enterprise-page-intro"><div><span className="enterprise-eyebrow">Security context</span><h1>Security</h1><p>These indicators reflect backend-reported state; the interface does not infer security guarantees.</p></div></div><div className="enterprise-security-list">{rows.map(([label, value]) => <div key={label}><span>{label}</span><strong>{String(value)}</strong></div>)}</div></div>;
}

export default function EnterpriseWorkspace({ currentUser, onLogout, accessDeniedMessage = '' }) {
  const location = useLocation();
  const navigate = useNavigate();
  const activeView = viewFromPath(location.pathname);
  const [collapsed, setCollapsed] = useState(false);
  const [health, setHealth] = useState(null);
  const [egress, setEgress] = useState(null);
  const [catalog, setCatalog] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [audits, setAudits] = useState([]);
  const [runs, setRuns] = useState([]);
  const [verification, setVerification] = useState(null);
  const [loading, setLoading] = useState({ documents: true, models: true, audit: true, runs: true });
  const [errors, setErrors] = useState({});
  const [currentResponse, setCurrentResponse] = useState(null);
  const [selectedCitation, setSelectedCitation] = useState(null);

  const onNavigate = (view) => {
    if (workspaceRoutes.has(view)) {
      navigate(view === 'home' ? '/workspace' : `/workspace/${view}`);
    }
  };

  useEffect(() => {
    fetchHealthStatus().then(setHealth);
    fetchEgressStatus().then(setEgress);
    fetchModelCatalog().then((data) => {
      setCatalog(data);
      setLoading((state) => ({ ...state, models: false }));
    }).catch(() => {
      setErrors((state) => ({ ...state, models: 'Unable to load the model catalog.' }));
      setLoading((state) => ({ ...state, models: false }));
    });
    fetchDocumentList().then((data) => {
      setDocuments(data || []);
      setLoading((state) => ({ ...state, documents: false }));
    }).catch(() => {
      setErrors((state) => ({ ...state, documents: 'Unable to load authorized documents.' }));
      setLoading((state) => ({ ...state, documents: false }));
    });
    fetchAuditLogs().then((data) => {
      setAudits(data || []);
      setLoading((state) => ({ ...state, audit: false }));
    }).catch(() => {
      setErrors((state) => ({ ...state, audit: 'Unable to load audit events.' }));
      setLoading((state) => ({ ...state, audit: false }));
    });
    fetchAgentRuns().then((data) => {
      setRuns(data || []);
      setLoading((state) => ({ ...state, runs: false }));
    }).catch(() => {
      setErrors((state) => ({ ...state, runs: 'Unable to load agent runs.' }));
      setLoading((state) => ({ ...state, runs: false }));
    });
    verifyAuditChain().then(setVerification).catch(() => setVerification(null));
  }, []);

  const handleDocumentSearch = async (query) => {
    const data = await searchDocuments(query);
    setDocuments(data || []);
  };

  const handleResponseReceived = async (response) => {
    setCurrentResponse(response);
    const [latestAudits, latestRuns] = await Promise.all([
      fetchAuditLogs(),
      fetchAgentRuns(),
    ]);
    setAudits(latestAudits || []);
    setRuns(latestRuns || []);
  };

  const [title, subtitle] = pageTitles[activeView] || pageTitles.home;
  const chatResponse = useMemo(() => currentResponse, [currentResponse]);

  return (
    <div className="enterprise-shell">
      <aside className={`enterprise-sidebar ${collapsed ? 'collapsed' : ''}`}>
        <div className="enterprise-brand"><div className="enterprise-brand-mark">A</div>{!collapsed && <div><strong>AEGIS AI</strong><small>Industrial Intelligence</small></div>}</div>
        <button className="enterprise-collapse" onClick={() => setCollapsed((value) => !value)} aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}>{collapsed ? <PanelLeftOpen size={16} /> : <PanelLeftClose size={16} />}</button>
        <nav className="enterprise-nav">{navigation.map((section) => <div key={section.group} className="enterprise-nav-group">{!collapsed && <span>{section.group}</span>}{section.items.map(({ id, label, icon: Icon }) => <button key={id} className={activeView === id ? 'active' : ''} onClick={() => onNavigate(id)} title={collapsed ? label : undefined}><Icon size={16} />{!collapsed && <span>{label}</span>}</button>)}</div>)}</nav>
        {!collapsed && <div className="enterprise-sidebar-footer"><div><StatusDot tone={health ? 'good' : 'neutral'} /><span>System status · {health ? health.status || 'online' : 'checking'}</span></div><small>{currentUser?.name || currentUser?.username || 'Authenticated operator'}</small><strong>{currentUser?.clearance || 'Clearance unavailable'}</strong><button onClick={onLogout}>Sign out</button></div>}
      </aside>

      <div className="enterprise-main">
        {accessDeniedMessage && <div className="enterprise-empty-callout" role="alert"><AlertCircle size={18} /><div>{accessDeniedMessage}</div></div>}
        <header className="enterprise-header"><div className="enterprise-header-title"><button className="enterprise-mobile-menu" onClick={() => setCollapsed((value) => !value)}><Menu size={17} /></button><div><strong>{title}</strong><small>{subtitle}</small></div></div><div className="enterprise-global-search"><Search size={15} /><span>Search documents, assets, and audit events</span><kbd>Ctrl K</kbd></div><div className="enterprise-header-actions"><span className="enterprise-onprem"><StatusDot tone={egress ? 'good' : 'neutral'} /> ON-PREMISE</span><span className="enterprise-user">{currentUser?.name || currentUser?.username || 'Operator'} · {currentUser?.clearance || currentUser?.role || 'USER'}</span></div></header>
        <Routes>
          <Route index element={<HomePage health={health} egress={egress} documents={documents} audits={audits} onNavigate={onNavigate} currentUser={currentUser} />} />
          <Route path="chat/:conversationId?" element={<div className="enterprise-chat-layout"><AegisChatPanel activeModel="auto" currentResponse={chatResponse} currentUser={currentUser} citations={chatResponse?.citations || []} onResponseReceived={handleResponseReceived} onSelectCitation={setSelectedCitation} /><AegisSourcePanel currentResponse={chatResponse} currentUser={currentUser} systemHealth={health} egressSnapshot={egress} citations={chatResponse?.citations || []} selectedCitation={selectedCitation} onSelectCitation={setSelectedCitation} /></div>} />
          <Route path="documents" element={<DocumentsPage documents={documents} loading={loading.documents} error={errors.documents} onSearch={handleDocumentSearch} />} />
          <Route path="models" element={<ModelsPage catalog={catalog} loading={loading.models} error={errors.models} />} />
          <Route path="audit" element={<AuditPage audits={audits} loading={loading.audit} error={errors.audit} verification={verification} />} />
          <Route path="security" element={<SecurityPage health={health} egress={egress} currentUser={currentUser} verification={verification} />} />
          <Route path="runs" element={<AgentRunsPage runs={runs} loading={loading.runs} error={errors.runs} />} />
          <Route path="*" element={<Navigate to="/workspace" replace />} />
        </Routes>
      </div>
    </div>
  );
}
