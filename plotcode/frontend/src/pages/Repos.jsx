import { useEffect, useState } from 'react';
import { getRepos } from '../api';
import { toast } from '../components/Toast';

export default function Repos({ onNav }) {
  const [repos, setRepos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [cloneRepo, setCloneRepo] = useState(null);
  const [cloneMode, setCloneMode] = useState('https');

  useEffect(() => {
    getRepos().then(d => { setRepos(d?.repos || []); setLoading(false); });
  }, []);

  const buildCloneUrl = (repo, mode) => {
    const url = repo.repo_url || '';
    // Convert github.com/org/repo to clone URL
    if (mode === 'https') {
      // https://github.com/org/repo.git
      return url.endsWith('.git') ? url : `${url}.git`;
    } else {
      // git@github.com:org/repo.git
      const match = url.match(/github\.com[:/]([^/]+\/[^/]+?)(?:\.git)?$/);
      if (match) return `git@github.com:${match[1]}.git`;
      return url;
    }
  };

  const copyUrl = (url) => {
    navigator.clipboard.writeText(url).then(() => {
      toast('success', '📋 Copied', 'Clone URL copied to clipboard');
    });
  };

  return (
    <div>
      <div className="section-header">
        <div className="section-title">Repositories</div>
      </div>

      {loading ? (
        <div className="grid-2">{[1,2].map(i => <div key={i} className="card"><div className="skeleton" style={{height:120}}/></div>)}</div>
      ) : repos.length === 0 ? (
        <div className="empty"><span className="empty-icon">📦</span><div className="empty-title">No repos connected</div><div className="empty-desc">Register a service to get started.</div></div>
      ) : (
        <div className="grid-2">
          {repos.map(r => {
            const httpsUrl = buildCloneUrl(r, 'https');
            const sshUrl = buildCloneUrl(r, 'ssh');
            return (
              <div className="repo-card" key={r.name} style={{ cursor: 'default' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
                  <div className="repo-name" style={{ cursor: 'pointer', flex: 1 }} onClick={() => onNav('filebrowser')}>
                    📦 {r.name}
                  </div>
                  <button
                    className="btn btn-primary btn-sm"
                    onClick={(e) => { e.stopPropagation(); setCloneRepo(r); setCloneMode('https'); }}
                    style={{ display: 'flex', alignItems: 'center', gap: 6 }}
                  >
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M6 3v12"/><circle cx="6" cy="17" r="3"/><circle cx="18" cy="6" r="3"/><path d="M18 9v9"/><path d="M6 6c0-1.5 1.5-3 3-3s3 1.5 3 3-1.5 3-3 3"/>
                    </svg>
                    Clone
                  </button>
                </div>
                <div className="repo-meta">{r.repo_url || '—'}</div>
                <div className="repo-meta">{r.tech_stack || '—'} · {r.team_owner || '—'}</div>
                <div className="repo-stats">
                  <div className="repo-stat"><strong>{r.default_branch || 'main'}</strong>default branch</div>
                  <div className="repo-stat"><strong>{r.is_active ? '✅' : '❌'}</strong>active</div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Clone Modal */}
      {cloneRepo && (
        <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && setCloneRepo(null)}>
          <div className="modal" style={{ maxWidth: 600 }}>
            <div className="flex items-center justify-between" style={{ marginBottom: 22 }}>
              <div className="modal-title" style={{ margin: 0 }}>Clone {cloneRepo.name}</div>
              <button className="btn btn-icon" onClick={() => setCloneRepo(null)}>✕</button>
            </div>

            {/* Clone mode tabs */}
            <div style={{ display: 'flex', gap: 0, marginBottom: 16, borderBottom: '1px solid var(--border)' }}>
              {['https', 'ssh'].map(mode => (
                <button
                  key={mode}
                  onClick={() => setCloneMode(mode)}
                  style={{
                    padding: '10px 20px',
                    background: 'none',
                    border: 'none',
                    borderBottom: cloneMode === mode ? '2px solid var(--primary)' : '2px solid transparent',
                    color: cloneMode === mode ? 'var(--primary)' : 'var(--text-muted)',
                    fontWeight: 600,
                    fontSize: 13,
                    cursor: 'pointer',
                    fontFamily: 'inherit',
                  }}
                >
                  {mode === 'https' ? 'HTTPS' : 'SSH'}
                </button>
              ))}
            </div>

            {/* Clone URL display */}
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: 0,
              border: '1px solid var(--border)',
              borderRadius: 'var(--radius)',
              overflow: 'hidden',
            }}>
              <input
                readOnly
                value={cloneMode === 'https' ? buildCloneUrl(cloneRepo, 'https') : buildCloneUrl(cloneRepo, 'ssh')}
                style={{
                  flex: 1,
                  background: 'var(--bg-input)',
                  border: 'none',
                  padding: '12px 14px',
                  fontSize: 13,
                  fontFamily: "'JetBrains Mono', monospace",
                  color: 'var(--text-primary)',
                  outline: 'none',
                }}
              />
              <button
                className="btn btn-primary"
                onClick={() => copyUrl(cloneMode === 'https' ? buildCloneUrl(cloneRepo, 'https') : buildCloneUrl(cloneRepo, 'ssh'))}
                style={{ borderRadius: 0, border: 'none', padding: '12px 18px' }}
              >
                📋 Copy
              </button>
            </div>

            {/* Help text */}
            <div style={{ marginTop: 16, padding: 14, background: 'rgba(124,58,237,0.05)', borderRadius: 'var(--radius)', fontSize: 12, color: 'var(--text-secondary)' }}>
              <div style={{ fontWeight: 600, marginBottom: 6 }}>Clone command:</div>
              <pre style={{ margin: 0, fontFamily: "'JetBrains Mono', monospace", fontSize: 12, color: 'var(--text-code)' }}>
{`git clone ${cloneMode === 'https' ? buildCloneUrl(cloneRepo, 'https') : buildCloneUrl(cloneRepo, 'ssh')}`}
              </pre>
            </div>

            {/* Additional info */}
            <div style={{ marginTop: 16, fontSize: 12, color: 'var(--text-muted)' }}>
              {cloneMode === 'https' ? (
                <>HTTPS is recommended for most users. You'll be asked for your GitHub username and password (use a Personal Access Token).</>
              ) : (
                <>SSH requires an SSH key added to your GitHub account. See GitHub SSH setup guide for details.</>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
