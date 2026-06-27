/**
 * API & WebSocket client — all backend calls go through here.
 * In development: proxy in vite.config.js rewrites /api → http://localhost:8001
 * In production (Vercel): same origin, /api/* routes to Python serverless function
 * In production (separate backend): VITE_API_URL env var points to backend URL
 */

const BASE = import.meta.env.VITE_API_URL || '/api';

// ─── Token Management ─────────────────────────────────────────

const TOKEN_KEY   = 'plotcode_access_token';
const REFRESH_KEY = 'plotcode_refresh_token';
const USER_KEY    = 'plotcode_user';

export function getAccessToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function getRefreshToken() {
  return localStorage.getItem(REFRESH_KEY);
}

export function getStoredUser() {
  const s = localStorage.getItem(USER_KEY);
  return s ? JSON.parse(s) : null;
}

export function setAuth(accessToken, refreshToken, user) {
  localStorage.setItem(TOKEN_KEY, accessToken);
  if (refreshToken) localStorage.setItem(REFRESH_KEY, refreshToken);
  if (user) localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function clearAuth() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(REFRESH_KEY);
  localStorage.removeItem(USER_KEY);
}

export function isAuthenticated() {
  return !!getAccessToken();
}

// ─── HTTP with auto-refresh ───────────────────────────────────

let isRefreshing = false;
let refreshPromise = null;

async function refreshToken() {
  if (isRefreshing) return refreshPromise;
  isRefreshing = true;
  refreshPromise = (async () => {
    const rt = getRefreshToken();
    if (!rt) throw new Error('No refresh token');
    const res = await fetch(BASE + '/auth/refresh', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: rt }),
    });
    if (!res.ok) {
      clearAuth();
      throw new Error('Refresh failed');
    }
    const data = await res.json();
    setAuth(data.access_token, data.refresh_token || rt, getStoredUser());
    return data.access_token;
  })();
  try {
    return await refreshPromise;
  } finally {
    isRefreshing = false;
    refreshPromise = null;
  }
}

export async function apiFetch(path, opts = {}) {
  const token = getAccessToken();
  const headers = { 'Content-Type': 'application/json', ...opts.headers };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  try {
    let res = await fetch(BASE + path, { ...opts, headers });

    // Auto-refresh on 401
    if (res.status === 401 && token && !opts._retried) {
      try {
        await refreshToken();
        return apiFetch(path, { ...opts, _retried: true });
      } catch {
        clearAuth();
        return null;
      }
    }

    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

// ─── Auth ─────────────────────────────────────────────────────

export async function login(username, password) {
  try {
    const res = await fetch(BASE + '/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });
    if (!res.ok) return null;
    const data = await res.json();
    setAuth(data.access_token, data.refresh_token, data.user);
    return data;
  } catch {
    return null;
  }
}

export async function register(body) {
  try {
    const res = await fetch(BASE + '/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (!res.ok) return null;
    const data = await res.json();
    setAuth(data.access_token, data.refresh_token, data.user);
    return data;
  } catch {
    return null;
  }
}

export async function getMe() {
  return apiFetch('/auth/me');
}

export async function getGitHubOAuthUrl() {
  return apiFetch('/auth/github');
}

export async function githubCallback(code, state) {
  return apiFetch('/auth/github/callback', {
    method: 'POST',
    body: JSON.stringify({ code, state }),
  });
}

export async function linkGitHub(code, state) {
  return _linkOAuth('/auth/github/link', code, state);
}

export async function getGoogleOAuthUrl() {
  return apiFetch('/auth/google');
}

export async function googleCallback(code, state) {
  return apiFetch('/auth/google/callback', {
    method: 'POST',
    body: JSON.stringify({ code, state }),
  });
}

export async function linkGoogle(code, state) {
  return _linkOAuth('/auth/google/link', code, state);
}

// Dedicated link function with proper error handling
async function _linkOAuth(path, code, state) {
  const token = getAccessToken();
  const headers = { 'Content-Type': 'application/json' };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  try {
    // Try refresh first if no token
    if (!token) {
      try { await refreshToken(); } catch { /* ignore */ }
      const newToken = getAccessToken();
      if (newToken) headers['Authorization'] = `Bearer ${newToken}`;
    }

    const res = await fetch(BASE + path, {
      method: 'POST',
      headers,
      body: JSON.stringify({ code, state }),
    });

    if (res.status === 401) {
      return { error: 'Not authenticated. Please log in again before linking.' };
    }

    if (!res.ok) {
      let detail = '';
      try { detail = (await res.json()).detail || ''; } catch { detail = res.statusText; }
      return { error: detail || `Server error (${res.status})` };
    }

    return await res.json();
  } catch (e) {
    return { error: e.message || 'Network error' };
  }
}

// ─── Requests ─────────────────────────────────────────────────

export const getRequests = (params = {}) => {
  const q = new URLSearchParams(Object.fromEntries(
    Object.entries(params).filter(([, v]) => v != null && v !== '')
  )).toString();
  return apiFetch(`/requests${q ? '?' + q : ''}`);
};

export const getRequest       = (id) => apiFetch(`/requests/${id}`);
export const getRequestAudit  = (id) => apiFetch(`/requests/${id}/audit`);
export const searchRequests   = (q)  => apiFetch(`/requests/search?q=${encodeURIComponent(q)}`);
export const approveRequest   = (id, actor = 'dashboard-user') =>
  apiFetch(`/requests/${id}/approve`, {
    method: 'POST',
    body: JSON.stringify({ actor_id: actor }),
  });
export const createRequest    = (body) =>
  apiFetch('/requests', { method: 'POST', body: JSON.stringify(body) });
export const updateRequest    = (id, body) =>
  apiFetch(`/requests/${id}`, { method: 'PATCH', body: JSON.stringify(body) });

// Metrics, agents, prompts
export const getMetrics    = () => apiFetch('/metrics');
export const getAgents     = () => apiFetch('/agents/status');
export const getPrompts    = (params = {}) => {
  const q = new URLSearchParams(Object.fromEntries(
    Object.entries(params).filter(([, v]) => v != null && v !== '')
  )).toString();
  return apiFetch(`/prompts${q ? '?' + q : ''}`);
};

// RBAC
export const getUsers     = () => apiFetch('/users');
export const updateRole   = (id, role) =>
  apiFetch(`/users/${id}/role`, { method: 'PATCH', body: JSON.stringify({ role }) });

// Health
export const getHealth = () => apiFetch('/health');

// ─── GitHub: Repos, Branches, Commits, PRs, Issues ────────────

export const getRepos              = () => apiFetch('/repos');
export const getBranches           = (repo) => apiFetch(`/repos/${repo}/branches`);
export const getCommits            = (repo, branch = 'main', limit = 20) =>
  apiFetch(`/repos/${repo}/commits?branch=${branch}&limit=${limit}`);
export const getPulls              = (repo, state = 'open', limit = 20) =>
  apiFetch(`/repos/${repo}/pulls?state=${state}&limit=${limit}`);
export const getIssues             = (repo, state = 'open', limit = 20) =>
  apiFetch(`/repos/${repo}/issues?state=${state}&limit=${limit}`);
export const getRepoContents       = (repo, path = '', ref = 'main') =>
  apiFetch(`/repos/${repo}/contents?path=${encodeURIComponent(path)}&ref=${ref}`);
export const getFileContent        = (repo, path, ref = 'main') =>
  apiFetch(`/repos/${repo}/file?path=${encodeURIComponent(path)}&ref=${ref}`);
export const getCheckRuns          = (repo, branch = 'main') =>
  apiFetch(`/repos/${repo}/check-runs?branch=${branch}`);

// ─── Chat ─────────────────────────────────────────────────────

export async function sendChat(message, context = {}) {
  return apiFetch('/chat', {
    method: 'POST',
    body: JSON.stringify({ message, context }),
  });
}

// ─── Services ─────────────────────────────────────────────────

export const getServices = () => apiFetch('/services');

// ─── Webhooks ─────────────────────────────────────────────────

export const getWebhooks     = () => apiFetch('/webhooks');
export const createWebhook   = (url, events = 'push,pull_request') =>
  apiFetch(`/webhooks?url=${encodeURIComponent(url)}&events=${encodeURIComponent(events)}`, { method: 'POST' });
export const toggleWebhook   = (id, active) =>
  apiFetch(`/webhooks/${id}?active=${active}`, { method: 'PATCH' });
export const deleteWebhook   = (id) =>
  apiFetch(`/webhooks/${id}`, { method: 'DELETE' });

// ─── Feature Flags ────────────────────────────────────────────

export const getFeatureFlags   = () => apiFetch('/feature-flags');
export const createFeatureFlag = (key, desc = '') =>
  apiFetch(`/feature-flags?key=${encodeURIComponent(key)}&desc=${encodeURIComponent(desc)}`, { method: 'POST' });
export const toggleFeatureFlag = (key, env, enabled) =>
  apiFetch(`/feature-flags/${key}?env=${env}&enabled=${enabled}`, { method: 'PATCH' });
export const deleteFeatureFlag = (key) =>
  apiFetch(`/feature-flags/${key}`, { method: 'DELETE' });

// ─── System Config ────────────────────────────────────────────

export const getSystemConfig = () => apiFetch('/system/config');

// ─── File Uploads ─────────────────────────────────────────────

export async function uploadFile(file) {
  const token = getAccessToken();
  const formData = new FormData();
  formData.append('file', file);
  try {
    const res = await fetch(BASE + '/upload', {
      method: 'POST',
      headers: token ? { 'Authorization': `Bearer ${token}` } : {},
      body: formData,
    });
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

export const getUploads    = () => apiFetch('/uploads');
export const getUpload     = (id) => apiFetch(`/uploads/${id}`);
export const deleteUpload  = (id) => apiFetch(`/uploads/${id}`, { method: 'DELETE' });

// ─── Real-time Events (WebSocket with polling fallback) ─────────────────────

// In production, connect to the backend WebSocket directly
// In development, use the Vite proxy (same origin)
const WS_URL = BASE.startsWith('http')
  ? `${BASE.replace(/^http/, 'ws')}/ws/events`
  : `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws/events`;

export function createEventSocket(onEvent, onStatusChange) {
  let ws = null;
  let reconnectTimer = null;
  let pollTimer = null;
  let lastPollTime = 0;
  let usePolling = false;

  // Try WebSocket first, fall back to polling if it fails (e.g. on Vercel)
  const connect = () => {
    try {
      ws = new WebSocket(WS_URL);
      ws.onopen = () => {
        usePolling = false;
        onStatusChange('live');
      };
      ws.onclose = () => {
        onStatusChange('reconnecting');
        // If WebSocket keeps failing, switch to polling
        if (!usePolling) {
          usePolling = true;
          startPolling();
        } else {
          reconnectTimer = setTimeout(connect, 4000);
        }
      };
      ws.onerror = () => {
        onStatusChange('error');
        // Don't wait for onclose, start polling immediately
        if (!usePolling) {
          usePolling = true;
          ws?.close();
          startPolling();
        }
      };
      ws.onmessage = (e) => {
        try { const ev = JSON.parse(e.data); if (ev.type !== 'ping') onEvent(ev); }
        catch { /* ignore */ }
      };
    } catch {
      usePolling = true;
      startPolling();
    }
  };

  // Polling fallback — fetch recent events every 5 seconds
  const startPolling = () => {
    onStatusChange('live'); // Show as live even in polling mode
    if (pollTimer) clearInterval(pollTimer);
    pollTimer = setInterval(async () => {
      try {
        const data = await apiFetch(`/requests?since=${lastPollTime}&limit=20`);
        if (data && data.requests) {
          for (const req of data.requests) {
            const ts = new Date(req.updated_at || req.created_at || 0).getTime();
            if (ts > lastPollTime) {
              lastPollTime = ts;
              onEvent({ type: 'request.updated', request_id: req.request_id, status: req.status, data: req });
            }
          }
        }
      } catch { /* ignore polling errors */ }
    }, 5000);
  };

  connect();
  return () => {
    clearTimeout(reconnectTimer);
    clearInterval(pollTimer);
    ws?.close();
  };
}
