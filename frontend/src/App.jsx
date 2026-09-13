import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import ChatWindow from './components/ChatWindow';
import EgressMonitor from './components/EgressMonitor';
import HitlPanel from './components/HitlPanel';
import { fetchHealthStatus } from './services/api';

export default function App() {
  const [activeModel, setActiveModel] = useState('qwen2.5:7b');
  const [systemHealth, setSystemHealth] = useState(null);
  const [pendingActions] = useState([
    {
      title: 'CONFIDENTIAL Document Export',
      description: 'Requesting permission to compile turbine_safety_report.docx inheriting CONFIDENTIAL source tag.'
    }
  ]);

  useEffect(() => {
    fetchHealthStatus().then((data) => {
      if (data) setSystemHealth(data);
    });
  }, []);

  return (
    <div className="app-container">
      <Header systemHealth={systemHealth} />
      <div className="workbench-layout">
        <Sidebar activeModel={activeModel} setActiveModel={setActiveModel} />
        <ChatWindow activeModel={activeModel} />
        <aside className="widgets-sidebar">
          <EgressMonitor />
          <HitlPanel pendingActions={pendingActions} />
        </aside>
      </div>
    </div>
  );
}
