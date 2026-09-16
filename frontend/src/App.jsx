import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import ChatWindow from './components/ChatWindow';
import RightDrawer from './components/RightDrawer';
import AuditModal from './components/AuditModal';
import SandboxModal from './components/SandboxModal';
import KnowledgeHubModal from './components/KnowledgeHubModal';
import DocViewerModal from './components/DocViewerModal';
import { fetchHealthStatus, loginUser } from './services/api';

export default function App() {
  const [activeModel, setActiveModel] = useState('Qwen 2.5 7B');
  const [systemHealth, setSystemHealth] = useState(null);
  const [currentResponse, setCurrentResponse] = useState(null);
  const [activeTab, setActiveTab] = useState('context');
  const [currentUser, setCurrentUser] = useState(null);

  const [auditOpen, setAuditOpen] = useState(false);
  const [sandboxOpen, setSandboxOpen] = useState(false);
  const [knowledgeOpen, setKnowledgeOpen] = useState(false);

  const [selectedCitation, setSelectedCitation] = useState(null);
  const [docViewerOpen, setDocViewerOpen] = useState(false);

  const handleRoleSwitch = async (newRole) => {
    try {
      const authData = await loginUser(`user_${newRole.toLowerCase()}`, newRole);
      setCurrentUser(authData.user);
    } catch (err) {
      console.error('Role switch error:', err);
    }
  };

  const handleOpenCitation = (citation) => {
    setSelectedCitation(citation);
    setDocViewerOpen(true);
  };

  useEffect(() => {
    fetchHealthStatus().then((data) => {
      if (data) setSystemHealth(data);
    });
    // Auto login default user (ENGINEER)
    handleRoleSwitch('ENGINEER');
  }, []);

  return (
    <div className="app-container">
      <Header
        systemHealth={systemHealth}
        currentUser={currentUser}
        onSelectRole={handleRoleSwitch}
      />
      <div className="workbench-layout">
        <Sidebar
          activeModel={activeModel}
          setActiveModel={setActiveModel}
          onOpenAudit={() => setAuditOpen(true)}
          onOpenSandbox={() => setSandboxOpen(true)}
          onOpenKnowledgeHub={() => setKnowledgeOpen(true)}
        />
        <ChatWindow
          activeModel={activeModel}
          setActiveModel={setActiveModel}
          currentUser={currentUser}
          onNewResponse={(resp) => setCurrentResponse(resp)}
          onSelectCitation={handleOpenCitation}
        />
        <RightDrawer
          response={currentResponse}
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          onSelectCitation={handleOpenCitation}
        />
      </div>

      <AuditModal isOpen={auditOpen} onClose={() => setAuditOpen(false)} />
      <SandboxModal isOpen={sandboxOpen} onClose={() => setSandboxOpen(false)} />
      <KnowledgeHubModal isOpen={knowledgeOpen} onClose={() => setKnowledgeOpen(false)} />
      <DocViewerModal
        isOpen={docViewerOpen}
        citation={selectedCitation}
        onClose={() => setDocViewerOpen(false)}
      />
    </div>
  );
}

