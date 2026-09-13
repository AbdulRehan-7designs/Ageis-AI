import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import ChatWindow from './components/ChatWindow';
import RightDrawer from './components/RightDrawer';
import { fetchHealthStatus } from './services/api';

export default function App() {
  const [activeModel, setActiveModel] = useState('Llama 3.1 8B');
  const [systemHealth, setSystemHealth] = useState(null);
  const [currentResponse, setCurrentResponse] = useState(null);
  const [activeTab, setActiveTab] = useState('context');

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
        <ChatWindow
          activeModel={activeModel}
          onNewResponse={(resp) => setCurrentResponse(resp)}
        />
        <RightDrawer
          response={currentResponse}
          activeTab={activeTab}
          setActiveTab={setActiveTab}
        />
      </div>
    </div>
  );
}
