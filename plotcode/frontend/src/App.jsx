import { useState, useEffect, useRef } from 'react';
import {
  createEventSocket, getStoredUser, clearAuth, isAuthenticated,
  githubCallback, googleCallback, linkGitHub, linkGoogle, setAuth,
} from './api';
import { toast, ToastContainer } from './components/Toast';
import RequestDrawer from './components/RequestDrawer';
import NewRequestModal from './components/NewRequestModal';
import ChatWidget from './components/ChatWidget';
import Landing   from './pages/Landing';
import Login     from './pages/Login';
import Overview  from './pages/Overview';
import Requests  from './pages/Requests';
import Agents    from './pages/Agents';
import Metrics   from './pages/Metrics';
import Prompts   from './pages/Prompts';
import RBAC      from './pages/RBAC';
import Repos     from './pages/Repos';
import Pulls     from './pages/Pulls';
import Issues    from './pages/Issues';
import Pipelines from './pages/Pipelines';
import Deployments from './pages/Deployments';
import Branches  from './pages/Branches';
import Commits   from './pages/Commits';
import Team      from './pages/Team';
import Audit     from './pages/Audit';
import Notifications from './pages/Notifications';
import Settings  from './pages/Settings';
import CodeReview from './pages/CodeReview';
import FileBrowser from './pages/FileBrowser';
import FileUpload from './pages/FileUpload';
import DiffViewer from './pages/DiffViewer';
import Releases  from './pages/Releases';
import Webhooks  from './pages/Webhooks';
import FeatureFlags from './pages/FeatureFlags';
import './index.css';

const NAV = [
  { id:'overview',    icon:'🏠', label:'Overview',        section:'Main' },
  { id:'requests',    icon:'📋', label:'Requests',        section:'Main', badge:true },
  { id:'repos',       icon:'📦', label:'Repositories',    section:'Code' },
  { id:'branches',    icon:'🌿', label:'Branches',        section:'Code' },
  { id:'commits',     icon:'📝', label:'Commits',         section:'Code' },
  { id:'pulls',       icon:'🔀', label:'Pull Requests',   section:'Code' },
  { id:'issues',      icon:'🐛', label:'Issues',          section:'Code' },
  { id:'codereview',  icon:'👁️', label:'Code Review',    section:'Code' },
  { id:'filebrowser', icon:'📁', label:'File Browser',    section:'Code' },
  { id:'uploads',     icon:'📤', label:'Uploads',         section:'Code' },
  { id:'diffviewer',  icon:'🔍', label:'Diff Viewer',     section:'Code' },
  { id:'pipelines',   icon:'⚙️', label:'Pipelines',       section:'CI/CD' },
  { id:'deployments', icon:'🚀', label:'Deployments',     section:'CI/CD' },
  { id:'releases',    icon:'🏷️', label:'Releases',        section:'CI/CD' },
  { id:'agents',      icon:'🤖', label:'Agents',          section:'AI Engine' },
  { id:'prompts',     icon:'🧠', label:'Prompt Explorer', section:'AI Engine' },
  { id:'metrics',     icon:'📊', label:'Metrics',         section:'Analytics' },
  { id:'audit',       icon:'📜', label:'Audit Log',       section:'Analytics' },
  { id:'team',        icon:'👥', label:'Team',            section:'Admin' },
  { id:'rbac',        icon:'🔐', label:'RBAC',            section:'Admin' },
  { id:'notifications', icon:'🔔', label:'Notifications', section:'Admin' },
  { id:'webhooks',    icon:'🔗', label:'Webhooks',        section:'Admin' },
  { id:'featureflags', icon:'🚩', label:'Feature Flags',  section:'Admin' },
  { id:'settings',    icon:'⚙️', label:'Settings',        section:'Admin' },
];

const PAGE_META = {
  overview:    { title:'Overview',         sub:'Pipeline health & active requests' },
  requests:    { title:'Feature Requests', sub:'All delivery requests and their status' },
  repos:       { title:'Repositories',     sub:'Browse and manage connected repos' },
  branches:    { title:'Branches',         sub:'View and manage git branches' },
  commits:     { title:'Commits',          sub:'Recent commit history across repos' },
  pulls:       { title:'Pull Requests',    sub:'Open and merged pull requests' },
  issues:      { title:'Issues',           sub:'Track bugs and feature issues' },
  codereview:  { title:'Code Review',      sub:'Review pending code changes' },
  filebrowser: { title:'File Browser',     sub:'Browse repository file tree' },
  uploads:     { title:'File Uploads',      sub:'Upload and manage code files' },
  diffviewer:  { title:'Diff Viewer',      sub:'Compare changes between commits' },
  pipelines:   { title:'Pipelines',        sub:'CI/CD pipeline runs and status' },
  deployments: { title:'Deployments',      sub:'Deployment history across environments' },
  releases:    { title:'Releases',         sub:'Release versions and changelogs' },
  agents:      { title:'AI Agents',        sub:'Agent status, confidence, and last run' },
  prompts:     { title:'Prompt Explorer',  sub:'Every LLM call — prompt, tokens, confidence' },
  metrics:     { title:'Analytics',        sub:'Pipeline throughput, SLA, and performance' },
  audit:       { title:'Audit Log',        sub:'Immutable event trail for all actions' },
  team:        { title:'Team',             sub:'Team members and roles' },
  rbac:        { title:'RBAC',             sub:'Role-based access control & permissions' },
  notifications:{ title:'Notifications',   sub:'Real-time alerts and notifications' },
  webhooks:    { title:'Webhooks',         sub:'Webhook endpoints and delivery logs' },
  featureflags:{ title:'Feature Flags',    sub:'Toggle features on/off per environment' },
  settings:    { title:'Settings',         sub:'Account, GitHub, and system configuration' },
};

const EVENT_TOASTS = {
  'request.created':      ['info',    '📋 New Request',  r => `${r.request_id} submitted`],
  'request.approved':     ['success', '✅ Approved',     r => `${r.request_id} approved`],
  'request.rejected':     ['warning', '❌ Rejected',     r => `${r.request_id} rejected`],
  'agent.plan_generated': ['info',    '🧠 Plan Ready',   r => `${r.request_id} — ${r.confidence}% conf.`],
  'ci.passed':            ['success', '✅ CI Passed',    r => r.request_id],
  'ci.failed':            ['error',   '❌ CI Failed',    r => r.request_id],
  'agent.pr_created':     ['info',    '🔀 PR Created',   r => r.request_id],
  'deploy.prod_deployed': ['success', '🚀 Deployed!',    r => r.request_id],
  'sla.breached':         ['error',   '⏰ SLA Breached', r => `${r.request_id} ${r.priority}`],
  'request.closed':       ['success', '🏁 Closed',       r => r.request_id],
};

export default function App() {
  // All hooks must be called before any conditional returns (Rules of Hooks)

  // 'landing' | 'login' | 'dashboard'
  const [screen, setScreen] = useState(() => {
    return isAuthenticated() ? 'dashboard' : 'landing';
  });
  const [user, setUser] = useState(() => getStoredUser());

  // Dashboard state (always declared, even if not used in landing/login)
  const [page,          setPage]          = useState('overview');
  const [connStatus,    setConnStatus]    = useState('connecting');
  const [activeBadge,   setActiveBadge]   = useState(0);
  const [drawerRequest, setDrawerRequest] = useState(null);
  const [showModal,     setShowModal]     = useState(false);
  const [searchQ,       setSearchQ]       = useState('');
  const [theme,         setTheme]         = useState(() => localStorage.getItem('plotcode_theme') || 'dark');

  const oauthHandled = useRef(false);

  // Handle OAuth callback (URL contains ?code=...&state=...)
  // Works for both GitHub and Google — detects which based on URL path
  // Also handles "link" mode (from Settings page) vs "login" mode
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const code = params.get('code');
    const state = params.get('state');
    const path = window.location.pathname;
    if (!code) return;

    if (oauthHandled.current) return;
    oauthHandled.current = true;

    const isGoogle = path.includes('/auth/google');
    const providerName = isGoogle ? 'Google' : 'GitHub';
    const linkMode = localStorage.getItem('plotcode_oauth_link');

    if (linkMode) {
      // LINK mode — user is already logged in, linking an account from Settings
      const linkFn = isGoogle ? linkGoogle : linkGitHub;
      linkFn(code, state).then(data => {
        if (data && data.user) {
          // Update stored user with new linked data
          const current = getStoredUser();
          const updated = { ...current, ...data.user };
          const token = localStorage.getItem('plotcode_access_token');
          const refresh = localStorage.getItem('plotcode_refresh_token');
          if (token) setAuth(token, refresh, updated);
          setUser(updated);
          setScreen('dashboard');
          toast('success', `✅ ${providerName} Connected`, `${providerName} account linked successfully!`);
        } else {
          const errMsg = data?.error || `Could not link ${providerName} account.`;
          toast('error', `❌ Link Failed`, errMsg);
          setScreen('dashboard');
        }
        localStorage.removeItem('plotcode_oauth_link');
        window.history.replaceState({}, document.title, window.location.pathname);
      });
    } else {
      // LOGIN mode — user is signing in with OAuth
      const callbackFn = isGoogle ? googleCallback : githubCallback;
      callbackFn(code, state).then(data => {
        if (data && data.user) {
          setUser(data.user);
          setScreen('dashboard');
          toast('success', `✅ ${providerName} Login`, `Welcome ${data.user.name || data.user.username}!`);
        } else {
          toast('error', `❌ ${providerName} Login Failed`, `Could not complete ${providerName} authentication.`);
          setScreen('login');
        }
        window.history.replaceState({}, document.title, window.location.pathname);
      });
    }
  }, []);

  // Apply theme to document
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('plotcode_theme', theme);
  }, [theme]);

  // WebSocket (only active in dashboard)
  useEffect(() => {
    if (screen !== 'dashboard') return;
    const cleanup = createEventSocket(
      (event) => {
        // Toast
        const t = EVENT_TOASTS[event.type];
        if (t) toast(t[0], t[1], t[2](event.payload));
        // Badge bump for new requests
        if (event.type === 'request.created') setActiveBadge(n => n + 1);
      },
      setConnStatus,
    );
    return cleanup;
  }, [screen]);

  // Search
  useEffect(() => {
    if (searchQ.length >= 2) setPage('requests');
  }, [searchQ]);

  const handleLogin = (userData) => {
    setUser(userData);
    setScreen('dashboard');
  };

  const handleLogout = () => {
    clearAuth();
    setUser(null);
    setScreen('landing');
  };

  const toggleTheme = () => setTheme(t => t === 'dark' ? 'light' : 'dark');

  // Show landing page
  if (screen === 'landing') {
    return (
      <>
        <Landing onGetStarted={() => setScreen('login')} />
        <ToastContainer />
      </>
    );
  }

  // Show login page
  if (screen === 'login') {
    return (
      <>
        <Login onLogin={handleLogin} onBack={() => setScreen('landing')} />
        <ToastContainer />
      </>
    );
  }

  // ── Dashboard ────────────────────────────────────────────
  const sections = [...new Set(NAV.map(n => n.section))];

  const renderedPage = () => {
    const props = {
      onOpenRequest: setDrawerRequest,
      onNav: setPage,
    };
    switch (page) {
      case 'overview':    return <Overview {...props}/>;
      case 'requests':    return <Requests onOpenRequest={setDrawerRequest} externalSearch={searchQ}/>;
      case 'repos':       return <Repos onNav={setPage}/>;
      case 'branches':    return <Branches/>;
      case 'commits':     return <Commits/>;
      case 'pulls':       return <Pulls/>;
      case 'issues':      return <Issues/>;
      case 'codereview':  return <CodeReview/>;
      case 'filebrowser': return <FileBrowser/>;
      case 'uploads':     return <FileUpload/>;
      case 'diffviewer':  return <DiffViewer/>;
      case 'pipelines':   return <Pipelines/>;
      case 'deployments': return <Deployments/>;
      case 'releases':    return <Releases/>;
      case 'agents':      return <Agents/>;
      case 'prompts':     return <Prompts/>;
      case 'metrics':     return <Metrics/>;
      case 'audit':       return <Audit/>;
      case 'team':        return <Team/>;
      case 'rbac':        return <RBAC/>;
      case 'notifications': return <Notifications/>;
      case 'webhooks':    return <Webhooks/>;
      case 'featureflags': return <FeatureFlags/>;
      case 'settings':    return <Settings user={user}/>;
      default:            return <Overview {...props}/>;
    }
  };

  const meta = PAGE_META[page] || {};

  return (
    <div className="app-shell">

      {/* ─── Sidebar ─── */}
      <aside className="sidebar">
        <div className="sidebar-brand">
          <div className="brand-icon">⚡</div>
          <div>
            <div className="brand-name">Plotcode</div>
            <div className="brand-tag">Delivery Automation</div>
          </div>
        </div>

        <nav className="sidebar-nav">
          {sections.map(sec => (
            <div key={sec}>
              <div className="nav-section">{sec}</div>
              {NAV.filter(n => n.section === sec).map(n => (
                <div key={n.id}
                  className={`nav-item ${page === n.id ? 'active' : ''}`}
                  onClick={() => setPage(n.id)}
                >
                  <span className="nav-icon">{n.icon}</span>
                  {n.label}
                  {n.badge && activeBadge > 0 && (
                    <span className="nav-badge">{activeBadge}</span>
                  )}
                </div>
              ))}
            </div>
          ))}
        </nav>

        <div className="sidebar-footer">
          <div className="conn-pill">
            <div className={`conn-dot ${connStatus === 'live' ? 'live' : connStatus === 'error' ? 'error' : ''}`}/>
            <span>
              {connStatus === 'live' ? 'Live'
               : connStatus === 'error' ? 'Error'
               : 'Connecting…'}
            </span>
          </div>
        </div>
      </aside>

      {/* ─── Main ─── */}
      <div className="main-area">

        {/* Top Bar */}
        <header className="topbar">
          <div className="topbar-info">
            <div className="page-title">{meta.title || page}</div>
            <div className="page-subtitle">{meta.sub || ''}</div>
          </div>
          <div className="topbar-actions">
            <div className="search-box">
              <span>🔍</span>
              <input
                value={searchQ}
                onChange={e => setSearchQ(e.target.value)}
                placeholder="Search requests…"
                autoComplete="off"
              />
            </div>
            <button className="btn btn-icon" title="Toggle theme" onClick={toggleTheme}>
              {theme === 'dark' ? '☀️' : '🌙'}
            </button>
            <button className="btn btn-primary" onClick={() => setShowModal(true)}>
              ➕ New Request
            </button>
            {/* User pill */}
            <div style={{
              display:'flex', alignItems:'center', gap:8,
              background:'rgba(124,58,237,0.12)', border:'1px solid rgba(124,58,237,0.25)',
              borderRadius:8, padding:'5px 12px',
            }}>
              <span style={{fontSize:14}}>👤</span>
              <span style={{fontSize:12,fontWeight:600,color:'#9F67FF'}}>{user?.username || 'admin'}</span>
              <span style={{
                fontSize:9, fontWeight:700, letterSpacing:1,
                background:'rgba(124,58,237,0.3)', color:'#C4B5FD',
                padding:'1px 5px', borderRadius:4, textTransform:'uppercase',
              }}>{user?.role || 'admin'}</span>
            </div>
            <button className="btn btn-icon" title="Logout" onClick={handleLogout}
              style={{color:'var(--danger)',borderColor:'rgba(239,68,68,0.2)'}}>
              🚪
            </button>
          </div>
        </header>

        {/* Content */}
        <div className="content">
          {renderedPage()}
        </div>
      </div>

      {/* ─── Drawer ─── */}
      {drawerRequest && (
        <RequestDrawer
          requestId={drawerRequest}
          onClose={() => setDrawerRequest(null)}
        />
      )}

      {/* ─── Modal ─── */}
      {showModal && (
        <NewRequestModal
          onClose={() => setShowModal(false)}
          onCreated={() => {
            setActiveBadge(n => n + 1);
            setPage('requests');
          }}
        />
      )}

      {/* ─── Chat Widget ─── */}
      <ChatWidget currentPage={page} />

      {/* ─── Toasts ─── */}
      <ToastContainer/>
    </div>
  );
}
