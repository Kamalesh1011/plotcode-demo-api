import { useState, useEffect } from 'react';
import { getGitHubOAuthUrl, getGoogleOAuthUrl, getSystemConfig } from '../api';
import { toast } from '../components/Toast';

export default function Settings({ user }) {
  const [webhookUrl, setWebhookUrl] = useState('');
  const [config, setConfig] = useState(null);

  useEffect(() => {
    getSystemConfig().then(d => { if (d) setConfig(d); });
  }, []);

  // Connect GitHub — sets a flag so App.jsx knows to LINK (not login)
  const handleConnectGitHub = () => {
    localStorage.setItem('plotcode_oauth_link', 'github');
    getGitHubOAuthUrl().then(d => {
      if (d?.url) {
        window.location.href = d.url;
      } else {
        toast('error', '❌ GitHub OAuth Not Configured', 'Set GITHUB_CLIENT_ID in backend .env');
        localStorage.removeItem('plotcode_oauth_link');
      }
    });
  };

  // Connect Google — sets a flag so App.jsx knows to LINK (not login)
  const handleConnectGoogle = () => {
    localStorage.setItem('plotcode_oauth_link', 'google');
    getGoogleOAuthUrl().then(d => {
      if (d?.url) {
        window.location.href = d.url;
      } else {
        toast('error', '❌ Google OAuth Not Configured', 'Set GOOGLE_CLIENT_ID in backend .env');
        localStorage.removeItem('plotcode_oauth_link');
      }
    });
  };

  return (
    <div>
      <div className="section-header">
        <div className="section-title">Settings</div>
      </div>

      <div className="grid-2" style={{alignItems:'start'}}>
        {/* Account */}
        <div className="card">
          <div className="card-title">Account</div>
          <div className="setting-row">
            <div>
              <div className="setting-label">Username</div>
              <div className="setting-desc">{user?.username || 'admin'}</div>
            </div>
          </div>
          <div className="setting-row">
            <div>
              <div className="setting-label">Role</div>
              <div className="setting-desc">{user?.role || 'admin'}</div>
            </div>
          </div>
          <div className="setting-row">
            <div>
              <div className="setting-label">Email</div>
              <div className="setting-desc">{user?.email || '—'}</div>
            </div>
          </div>
          <div className="setting-row">
            <div>
              <div className="setting-label">Name</div>
              <div className="setting-desc">{user?.name || '—'}</div>
            </div>
          </div>
        </div>

        {/* Connected Accounts */}
        <div className="card">
          <div className="card-title">Connected Accounts</div>

          {/* GitHub */}
          <div className="setting-row">
            <div style={{display:'flex', alignItems:'center', gap:10}}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor" style={{color:'var(--text-primary)'}}>
                <path d="M12 .5C5.37.5 0 5.78 0 12.29c0 5.21 3.44 9.63 8.21 11.19.6.11.82-.26.82-.58 0-.29-.01-1.04-.02-2.05-3.34.72-4.04-1.59-4.04-1.59-.55-1.38-1.34-1.75-1.34-1.75-1.09-.74.08-.73.08-.73 1.21.09 1.84 1.23 1.84 1.23 1.07 1.8 2.81 1.28 3.5.98.11-.77.42-1.28.76-1.58-2.67-.3-5.47-1.31-5.47-5.84 0-1.29.47-2.34 1.23-3.17-.12-.3-.53-1.52.12-3.16 0 0 1-.32 3.3 1.21.96-.26 1.98-.39 3-.4 1.02.01 2.04.14 3 .4 2.28-1.53 3.28-1.21 3.28-1.21.65 1.64.24 2.86.12 3.16.77.83 1.23 1.88 1.23 3.17 0 4.54-2.81 5.53-5.49 5.83.43.36.81 1.08.81 2.18 0 1.58-.01 2.85-.01 3.24 0 .32.22.7.83.58C20.57 21.91 24 17.5 24 12.29 24 5.78 18.63.5 12 .5z"/>
              </svg>
              <div>
                <div className="setting-label">GitHub</div>
                <div className="setting-desc">
                  {user?.github_id ? `✅ Linked (ID: ${user.github_id})` : '❌ Not connected'}
                </div>
              </div>
            </div>
            {!user?.github_id && (
              <button className="btn btn-primary btn-sm" onClick={handleConnectGitHub}>
                Connect GitHub
              </button>
            )}
          </div>

          {/* Google */}
          <div className="setting-row">
            <div style={{display:'flex', alignItems:'center', gap:10}}>
              <svg width="20" height="20" viewBox="0 0 24 24">
                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
              </svg>
              <div>
                <div className="setting-label">Google</div>
                <div className="setting-desc">
                  {user?.google_id ? `✅ Linked (ID: ${user.google_id})` : '❌ Not connected'}
                </div>
              </div>
            </div>
            {!user?.google_id && (
              <button className="btn btn-primary btn-sm" onClick={handleConnectGoogle}>
                Connect Google
              </button>
            )}
          </div>
        </div>

        {/* System */}
        <div className="card">
          <div className="card-title">System Configuration</div>
          <div className="setting-row">
            <div>
              <div className="setting-label">API Endpoint</div>
              <div className="setting-desc">{config?.api_endpoint || 'localhost:8001'}</div>
            </div>
            <span className="badge status-approved">● {config?.api_online ? 'Online' : 'Offline'}</span>
          </div>
          <div className="setting-row">
            <div>
              <div className="setting-label">Database</div>
              <div className="setting-desc">{config ? `${config.database} · ${config.database_name}` : '—'}</div>
            </div>
          </div>
          <div className="setting-row">
            <div>
              <div className="setting-label">LLM Provider</div>
              <div className="setting-desc">{config ? `${config.llm_provider} (${config.llm_model})` : '—'}</div>
            </div>
          </div>
          <div className="setting-row">
            <div>
              <div className="setting-label">Chat Model</div>
              <div className="setting-desc">{config?.chat_model || '—'}</div>
            </div>
          </div>
          <div className="setting-row">
            <div>
              <div className="setting-label">CI Platform</div>
              <div className="setting-desc">{config?.ci_platform || '—'}</div>
            </div>
          </div>
          <div className="setting-row">
            <div>
              <div className="setting-label">GitHub Org</div>
              <div className="setting-desc">{config?.github_org || '—'}</div>
            </div>
            <span className={`badge ${config?.github_configured ? 'status-approved' : 'status-failed'}`}>
              {config?.github_configured ? '● Configured' : '○ Not configured'}
            </span>
          </div>
          <div className="setting-row">
            <div>
              <div className="setting-label">Google OAuth</div>
              <div className="setting-desc">{config?.google_configured ? 'Configured' : 'Not configured'}</div>
            </div>
          </div>
          <div className="setting-row">
            <div>
              <div className="setting-label">Telegram Bot</div>
              <div className="setting-desc">{config?.telegram_configured ? 'Configured' : 'Not configured'}</div>
            </div>
          </div>
          <div className="setting-row">
            <div>
              <div className="setting-label">Version</div>
              <div className="setting-desc">v{config?.version || '3.0.0'}</div>
            </div>
          </div>
          <div className="setting-row">
            <div>
              <div className="setting-label">WebSocket Subscribers</div>
              <div className="setting-desc">{config?.websocket_subscribers ?? 0} active</div>
            </div>
          </div>
          <div className="setting-row">
            <div>
              <div className="setting-label">Total Requests</div>
              <div className="setting-desc">{config?.total_requests ?? 0}</div>
            </div>
          </div>
          <div className="setting-row">
            <div>
              <div className="setting-label">Total Users</div>
              <div className="setting-desc">{config?.total_users ?? 0}</div>
            </div>
          </div>
          <div className="setting-row">
            <div>
              <div className="setting-label">Total Services</div>
              <div className="setting-desc">{config?.total_services ?? 0}</div>
            </div>
          </div>
        </div>

        {/* Webhook URL */}
        <div className="card">
          <div className="card-title">CI Webhook URL</div>
          <div className="form-group">
            <label className="form-label">Public URL for GitHub webhooks</label>
            <input className="form-input" value={webhookUrl} onChange={e => setWebhookUrl(e.target.value)}
              placeholder="https://your-ngrok-url.ngrok-free.app/ci-webhook"/>
          </div>
          <button className="btn btn-primary btn-sm" onClick={() => toast('info', '📋 Copied', 'Webhook URL saved (local only)')}>Save</button>
        </div>

        {/* Danger Zone */}
        <div className="card" style={{borderColor:'rgba(239,68,68,0.2)'}}>
          <div className="card-title" style={{color:'var(--danger)'}}>Danger Zone</div>
          <div className="setting-row">
            <div>
              <div className="setting-label">Clear Local Data</div>
              <div className="setting-desc">Clear cached notifications and preferences</div>
            </div>
            <button className="btn btn-secondary btn-sm" style={{borderColor:'rgba(239,68,68,0.3)', color:'var(--danger)'}}
              onClick={() => { localStorage.clear(); toast('success', '✅ Cleared', 'Local data cleared. Reload to apply.'); }}>
              Clear
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
