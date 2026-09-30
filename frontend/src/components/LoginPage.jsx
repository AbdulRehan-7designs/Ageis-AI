import React, { useEffect, useRef, useState } from 'react';
import { AlertCircle, ArrowRight, Eye, EyeOff, Lock, ShieldCheck, User } from 'lucide-react';

export default function LoginPage({ onLogin, sessionMessage = '' }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState(sessionMessage);
  const [loading, setLoading] = useState(false);
  const heroBgRef = useRef(null);

  useEffect(() => {
    const handleScroll = () => {
      if (heroBgRef.current) heroBgRef.current.style.transform = `translateY(${window.scrollY * 0.3}px)`;
    };
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setLoading(true);
    setError('');
    try {
      await onLogin({ username: username.trim(), password });
    } catch (loginError) {
      setError(loginError?.response?.data?.detail || loginError?.message || 'Unable to sign in to Aegis services.');
      setLoading(false);
    }
  };

  return (
    <div className="lgn-root">
      <div className="lgn-bg" ref={heroBgRef} />
      <div className="lgn-overlay" />
      <div className="lgn-grid" />
      <div className="lgn-layout">
        <div className="lgn-left">
          <div className="lgn-brand">
            <div className="lgn-brand-logo"><ShieldCheck size={22} /></div>
            <div><span className="lgn-brand-name">AegisAI</span><span className="lgn-brand-tag">Sovereign Agentic Workbench</span></div>
          </div>
          <div className="lgn-left-body">
            <div className="lgn-left-badge"><span className="lgn-badge-dot" /> Secure industrial intelligence</div>
            <h1 className="lgn-left-title">Secure Access<br /><em>to your sovereign</em><br />AI workbench</h1>
            <p className="lgn-left-sub">Authentication, clearance, and audit identity are managed by the Aegis backend.</p>
          </div>
        </div>

        <div className="lgn-right">
          <div className="lgn-card">
            <div className="lgn-card-top">
              <div className="lgn-card-logo"><ShieldCheck size={20} /></div>
              <div><h2 className="lgn-card-title">Sign In</h2><p className="lgn-card-sub">AegisAI Secure Portal</p></div>
            </div>
            <form className="lgn-form" onSubmit={handleSubmit}>
              <div className="lgn-field">
                <label className="lgn-label" htmlFor="aegis-username">Username</label>
                <div className="lgn-input-wrap">
                  <User size={16} className="lgn-input-icon" />
                  <input id="aegis-username" type="text" className="lgn-input" placeholder="Enter your username" value={username} onChange={(event) => setUsername(event.target.value)} autoComplete="username" required disabled={loading} />
                </div>
              </div>
              <div className="lgn-field">
                <label className="lgn-label" htmlFor="aegis-password">Password</label>
                <div className="lgn-input-wrap">
                  <Lock size={16} className="lgn-input-icon" />
                  <input id="aegis-password" type={showPassword ? 'text' : 'password'} className="lgn-input" placeholder="Enter your password" value={password} onChange={(event) => setPassword(event.target.value)} autoComplete="current-password" required disabled={loading} />
                  <button type="button" className="lgn-pass-toggle" onClick={() => setShowPassword((value) => !value)} aria-label={showPassword ? 'Hide password' : 'Show password'}>{showPassword ? <EyeOff size={15} /> : <Eye size={15} />}</button>
                </div>
              </div>
              {error && <div className="lgn-error"><AlertCircle size={15} /><div>{error}</div></div>}
              <button type="submit" className={`lgn-submit${loading ? ' loading' : ''}`} disabled={loading || !username.trim() || !password}>
                {loading ? <><span className="lgn-spinner" /> Authenticating...</> : <>Sign In to Portal <ArrowRight size={16} /></>}
              </button>
            </form>
            <div className="lgn-card-footer">
              <div className="lgn-security-line"><span className="lgn-sec-dot" /> Secured · Air-Gapped · All sessions logged</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
