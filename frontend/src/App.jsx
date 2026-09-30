import React, { useEffect, useState } from 'react';
import { Navigate, Route, Routes, useLocation, useNavigate } from 'react-router-dom';
import LandingPage from './components/LandingPage';
import LoginPage from './components/LoginPage';
import { loginUser } from './services/api';
import EnterpriseWorkspace from './components/EnterpriseWorkspace';
import './landing.css';
import './login.css';
import './workbench.css';

const normalizeUser = (user) => {
  const username = user?.username || user?.name || 'engineer';
  const role = (user?.role || 'ENGINEER').toUpperCase();
  const clearance = user?.clearance || user?.clearance_tags?.[0] || role;
  return {
    ...user,
    id: user?.id || username,
    username,
    name: user?.name || username,
    role,
    clearance,
    clearance_tags: user?.clearance_tags || [clearance],
    initials: (user?.name || username)
      .split(/\s+/)
      .map((part) => part[0])
      .slice(0, 2)
      .join('')
      .toUpperCase() || 'AI',
  };
};

const readStoredUser = () => {
  try {
    const saved = localStorage.getItem('aegis_user');
    return saved ? normalizeUser(JSON.parse(saved)) : null;
  } catch {
    return null;
  }
};

function isAuthenticated() {
  return Boolean(localStorage.getItem('aegis_jwt_token') && readStoredUser());
}

function ProtectedWorkspace({ currentUser, onLogout, accessDeniedMessage }) {
  const location = useLocation();
  if (!currentUser || !isAuthenticated()) {
    const destination = `${location.pathname}${location.search}${location.hash}`;
    return <Navigate to="/login" replace state={{ from: destination }} />;
  }
  return (
    <EnterpriseWorkspace
      currentUser={currentUser}
      accessDeniedMessage={accessDeniedMessage}
      onLogout={onLogout}
    />
  );
}

function LoginRoute({ onLogin, sessionMessage }) {
  const navigate = useNavigate();
  const location = useLocation();
  const requestedPath = location.state?.from;
  const safeDestination = typeof requestedPath === 'string'
    && requestedPath.startsWith('/')
    && !requestedPath.startsWith('//')
    && !requestedPath.startsWith('/login')
    ? requestedPath
    : '/workspace';

  const handleLogin = async (credentials) => {
    await onLogin(credentials);
    navigate(safeDestination, { replace: true });
  };

  return <LoginPage onLogin={handleLogin} sessionMessage={sessionMessage} />;
}

export default function App() {
  const navigate = useNavigate();
  const [currentUser, setCurrentUser] = useState(readStoredUser);
  const [sessionMessage, setSessionMessage] = useState('');
  const [accessDeniedMessage, setAccessDeniedMessage] = useState('');

  useEffect(() => {
    const handleSessionExpired = () => {
      setCurrentUser(null);
      setSessionMessage('Your session expired. Please sign in again.');
      navigate('/login', { replace: true });
    };
    const handleAccessDenied = (event) => {
      setAccessDeniedMessage(event.detail || 'Access denied for this operation.');
    };
    window.addEventListener('aegis:session-expired', handleSessionExpired);
    window.addEventListener('aegis:access-denied', handleAccessDenied);
    return () => {
      window.removeEventListener('aegis:session-expired', handleSessionExpired);
      window.removeEventListener('aegis:access-denied', handleAccessDenied);
    };
  }, [navigate]);

  const handleLogin = async (credentials) => {
    const username = credentials?.username?.trim();
    const password = credentials?.password;
    try {
      const data = await loginUser(username, password);
      const user = normalizeUser({ ...(data?.user || {}), username });
      setCurrentUser(user);
      setSessionMessage('');
      localStorage.setItem('aegis_user', JSON.stringify(user));
    } catch (error) {
      console.error('Login failed:', error);
      throw error;
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('aegis_jwt_token');
    localStorage.removeItem('aegis_user');
    setCurrentUser(null);
    setAccessDeniedMessage('');
    navigate('/login', { replace: true });
  };

  return (
    <Routes>
      <Route path="/" element={<LandingPage onEnter={() => navigate('/login')} />} />
      <Route path="/login" element={<LoginRoute onLogin={handleLogin} sessionMessage={sessionMessage} />} />
      <Route
        path="/workspace/*"
        element={(
          <ProtectedWorkspace
            currentUser={currentUser}
            accessDeniedMessage={accessDeniedMessage}
            onLogout={handleLogout}
          />
        )}
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
