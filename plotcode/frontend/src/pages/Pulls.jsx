import { useEffect, useState } from 'react';
import { getRepos, getPulls } from '../api';
import { relativeTime } from '../utils';
import { toast } from '../components/Toast';

export default function Pulls() {
  const [repos, setRepos] = useState([]);
  const [selected, setSelected] = useState('');
  const [pulls, setPulls] = useState([]);
  const [state, setState] = useState('open');
  const [loading, setLoading] = useState(false);
  const [selectedPR, setSelectedPR] = useState(null);

  useEffect(() => {
    getRepos().then(d => {
      const r = d?.repos || [];
      setRepos(r);
      if (r.length) setSelected(r[0].name);
    });
  }, []);

  useEffect(() => {
    if (!selected) return;
    setLoading(true);
    getPulls(selected, state, 30).then(d => { setPulls(d?.pulls || []); setLoading(false); });
  }, [selected, state]);

  // PR detail view (Bitbucket-style)
  if (selectedPR) {
    return <PRDetail pr={selectedPR} onBack={() => setSelectedPR(null)} />;
  }

  return (
    <div>
      <div className="section-header">
        <div className="section-title">Pull Requests</div>
        <select className="filter-select" value={state} onChange={e => setState(e.target.value)}>
          <option value="open">Open</option>
          <option value="closed">Closed</option>
          <option value="all">All</option>
        </select>
        <select className="filter-select" value={selected} onChange={e => setSelected(e.target.value)}>
          {repos.map(r => <option key={r.name} value={r.name}>{r.name}</option>)}
        </select>
      </div>

      {/* Stats bar */}
      {!loading && pulls.length > 0 && (
        <div className="flex gap-8 mb-16">
          <div className="card" style={{ padding: '12px 20px', flex: 1 }}>
            <div className="text-muted text-xs">Open</div>
            <div style={{ fontSize: 22, fontWeight: 800 }}>{pulls.filter(p => p.state === 'open').length}</div>
          </div>
          <div className="card" style={{ padding: '12px 20px', flex: 1 }}>
            <div className="text-muted text-xs">Merged</div>
            <div style={{ fontSize: 22, fontWeight: 800, color: 'var(--info)' }}>{pulls.filter(p => p.merged).length}</div>
          </div>
          <div className="card" style={{ padding: '12px 20px', flex: 1 }}>
            <div className="text-muted text-xs">Closed</div>
            <div style={{ fontSize: 22, fontWeight: 800, color: 'var(--danger)' }}>{pulls.filter(p => p.state === 'closed' && !p.merged).length}</div>
          </div>
        </div>
      )}

      <div className="card">
        {loading ? (
          <div className="skeleton" style={{height:300}}/>
        ) : pulls.length === 0 ? (
          <div className="empty"><span className="empty-icon">🔀</span><div className="empty-title">No pull requests</div></div>
        ) : (
          pulls.map(pr => (
            <div
              className="pr-row"
              key={pr.number}
              onClick={() => setSelectedPR(pr)}
              style={{ cursor: 'pointer' }}
            >
              <span className="pr-number">#{pr.number}</span>
              <span className={`pr-state ${pr.merged ? 'merged' : pr.state}`}>{pr.merged ? 'merged' : pr.state}</span>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontWeight: 500, fontSize: 13, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {pr.title}
                </div>
                <div className="text-muted text-xs mt-4" style={{ display: 'flex', gap: 12 }}>
                  <span>👤 {pr.author || '—'}</span>
                  <span>🌿 {pr.head} → {pr.base}</span>
                  <span>🕒 {relativeTime(pr.created_at)}</span>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

// ─── Bitbucket-style PR Detail View ──────────────────────────────────────────

function PRDetail({ pr, onBack }) {
  const [tab, setTab] = useState('overview');
  const [approveLoading, setApproveLoading] = useState(false);
  const [approved, setApproved] = useState(false);
  const [comment, setComment] = useState('');
  const [comments, setComments] = useState([]);
  const [diffView, setDiffView] = useState('unified'); // 'unified' | 'split'

  const handleApprove = () => {
    setApproveLoading(true);
    setTimeout(() => {
      setApproved(true);
      setApproveLoading(false);
      toast('success', '✅ Approved', `Pull request #${pr.number} approved`);
    }, 800);
  };

  const handleComment = (e) => {
    e.preventDefault();
    if (!comment.trim()) return;
    setComments(c => [...c, { author: 'You', text: comment, time: 'just now' }]);
    setComment('');
    toast('success', '💬 Commented', 'Your comment was added');
  };

  // Mock diff data based on PR
  const changedFiles = [
    { filename: 'src/api/handler.ts', additions: 12, deletions: 3, status: 'modified' },
    { filename: 'src/utils/helpers.js', additions: 5, deletions: 0, status: 'added' },
    { filename: 'src/legacy/old.py', additions: 0, deletions: 18, status: 'deleted' },
  ];

  return (
    <div>
      {/* Header */}
      <div className="section-header">
        <button className="btn btn-ghost btn-sm" onClick={onBack}>← Back to PRs</button>
      </div>

      {/* PR Title bar */}
      <div className="card mb-16">
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: 16 }}>
          <span className={`pr-state ${pr.merged ? 'merged' : pr.state}`} style={{ fontSize: 13, padding: '4px 12px' }}>
            {pr.merged ? 'MERGED' : pr.state.toUpperCase()}
          </span>
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: 20, fontWeight: 700 }}>
              {pr.title}
              <span className="text-muted" style={{ fontWeight: 400, marginLeft: 8 }}>#{pr.number}</span>
            </div>
            <div className="text-muted text-sm mt-4" style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
              <span>👤 {pr.author || 'Unknown'}</span>
              <span>🌿 {pr.head} → {pr.base}</span>
              <span>🕒 Opened {relativeTime(pr.created_at)}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 0, borderBottom: '1px solid var(--border)', marginBottom: 16 }}>
        {[
          { key: 'overview', label: 'Overview', icon: '📋' },
          { key: 'diff', label: 'Diff', icon: '📝' },
          { key: 'activity', label: 'Activity', icon: '💬' },
        ].map(t => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            style={{
              padding: '10px 20px',
              background: 'none',
              border: 'none',
              borderBottom: tab === t.key ? '2px solid var(--primary)' : '2px solid transparent',
              color: tab === t.key ? 'var(--primary)' : 'var(--text-muted)',
              fontWeight: 600,
              fontSize: 13,
              cursor: 'pointer',
              fontFamily: 'inherit',
              display: 'flex',
              alignItems: 'center',
              gap: 6,
            }}
          >
            {t.icon} {t.label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      {tab === 'overview' && (
        <div className="grid-2" style={{ alignItems: 'start' }}>
          {/* Description */}
          <div className="card">
            <div className="card-title">Description</div>
            <div style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.6 }}>
              {pr.body || 'No description provided.'}
            </div>

            {/* Branch info */}
            <div style={{ marginTop: 20, padding: 14, background: 'rgba(124,58,237,0.05)', borderRadius: 'var(--radius)' }}>
              <div className="text-muted text-xs mb-8">BRANCHES</div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, fontFamily: "'JetBrains Mono', monospace", fontSize: 12 }}>
                <span style={{ color: 'var(--success)' }}>{pr.head}</span>
                <span>→</span>
                <span style={{ color: 'var(--primary)' }}>{pr.base}</span>
              </div>
            </div>

            {/* Changed files summary */}
            <div style={{ marginTop: 20 }}>
              <div className="text-muted text-xs mb-8">CHANGED FILES</div>
              {changedFiles.map(f => (
                <div key={f.filename} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '6px 0', fontSize: 12 }}>
                  <span style={{ fontSize: 14 }}>{f.status === 'added' ? '➕' : f.status === 'deleted' ? '➖' : '✏️'}</span>
                  <span className="font-mono" style={{ flex: 1 }}>{f.filename}</span>
                  <span style={{ color: 'var(--success)', fontSize: 11 }}>+{f.additions}</span>
                  <span style={{ color: 'var(--danger)', fontSize: 11 }}>-{f.deletions}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Reviewers & Approvals */}
          <div className="card">
            <div className="card-title">Reviewers</div>
            <div style={{ padding: '10px 0', display: 'flex', alignItems: 'center', gap: 10 }}>
              <div style={{ width: 32, height: 32, borderRadius: '50%', background: 'var(--primary)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 13, fontWeight: 700 }}>
                {pr.author?.[0]?.toUpperCase() || 'U'}
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 13, fontWeight: 600 }}>{pr.author || 'Unknown'}</div>
                <div className="text-muted text-xs">Author</div>
              </div>
            </div>

            {approved && (
              <div style={{ padding: '10px 0', display: 'flex', alignItems: 'center', gap: 10, borderTop: '1px solid var(--border)' }}>
                <div style={{ width: 32, height: 32, borderRadius: '50%', background: 'var(--success)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 14 }}>
                  ✅
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 13, fontWeight: 600 }}>You</div>
                  <div className="text-muted text-xs">Approved</div>
                </div>
              </div>
            )}

            {/* Actions */}
            <div style={{ marginTop: 20, display: 'flex', gap: 8 }}>
              <button
                className="btn btn-primary"
                onClick={handleApprove}
                disabled={approveLoading || approved}
                style={{ flex: 1 }}
              >
                {approveLoading ? 'Approving…' : approved ? '✅ Approved' : '✅ Approve'}
              </button>
              <button
                className="btn btn-secondary"
                onClick={() => toast('info', '🔄 Requested Changes', 'Change request added')}
                disabled={approved}
                style={{ flex: 1 }}
              >
                ⚠️ Request Changes
              </button>
            </div>
            <button
              className="btn btn-secondary"
              onClick={() => toast('info', '🔀 Merge', 'Merge functionality requires GitHub API merge permission')}
              style={{ width: '100%', marginTop: 8, borderColor: 'rgba(124,58,237,0.3)', color: 'var(--primary)' }}
            >
              🔀 Merge Pull Request
            </button>
          </div>
        </div>
      )}

      {tab === 'diff' && (
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
            <div className="card-title" style={{ margin: 0 }}>Changes</div>
            <div style={{ display: 'flex', gap: 0, border: '1px solid var(--border)', borderRadius: 'var(--radius)', overflow: 'hidden' }}>
              {['unified', 'split'].map(v => (
                <button
                  key={v}
                  onClick={() => setDiffView(v)}
                  style={{
                    padding: '6px 14px',
                    background: diffView === v ? 'var(--primary)' : 'transparent',
                    color: diffView === v ? '#fff' : 'var(--text-muted)',
                    border: 'none',
                    fontSize: 12,
                    fontWeight: 600,
                    cursor: 'pointer',
                    fontFamily: 'inherit',
                  }}
                >
                  {v === 'unified' ? 'Unified' : 'Split'}
                </button>
              ))}
            </div>
          </div>

          {changedFiles.map(f => (
            <DiffBlock key={f.filename} file={f} view={diffView} />
          ))}
        </div>
      )}

      {tab === 'activity' && (
        <div className="card">
          <div className="card-title">Activity</div>

          {/* Comment form */}
          <form onSubmit={handleComment} style={{ marginBottom: 20 }}>
            <textarea
              className="form-textarea"
              rows={3}
              value={comment}
              onChange={e => setComment(e.target.value)}
              placeholder="Write a comment…"
              style={{ marginBottom: 8 }}
            />
            <button type="submit" className="btn btn-primary btn-sm" disabled={!comment.trim()}>
              💬 Comment
            </button>
          </form>

          {/* Activity timeline */}
          <div className="timeline">
            <div className="tl-item">
              <div className="tl-time">{relativeTime(pr.created_at)}</div>
              <div className="tl-action">{pr.author || 'Unknown'} opened this pull request</div>
              <div className="tl-actor">#{pr.number}</div>
            </div>
            {approved && (
              <div className="tl-item">
                <div className="tl-time">just now</div>
                <div className="tl-action">You approved this pull request</div>
                <div className="tl-actor">reviewer</div>
              </div>
            )}
            {comments.map((c, i) => (
              <div className="tl-item" key={i}>
                <div className="tl-time">{c.time}</div>
                <div className="tl-action">{c.author}: {c.text}</div>
                <div className="tl-actor">comment</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ─── Diff Block Component ────────────────────────────────────────────────────

function DiffBlock({ file, view }) {
  const [expanded, setExpanded] = useState(true);

  // Generate mock diff lines
  const diffLines = [
    { type: 'context', oldNum: 1, newNum: 1, content: 'function processData(input) {' },
    { type: 'context', oldNum: 2, newNum: 2, content: '  const result = [];' },
    { type: 'add',     oldNum: null, newNum: 3, content: '  // Added validation' },
    { type: 'add',     oldNum: null, newNum: 4, content: '  if (!input) return [];' },
    { type: 'context', oldNum: 3, newNum: 5, content: '  for (const item of input) {' },
    { type: 'del',     oldNum: 4, newNum: null, content: '    result.push(item.value);' },
    { type: 'add',     oldNum: null, newNum: 6, content: '    if (item.value !== null) {' },
    { type: 'add',     oldNum: null, newNum: 7, content: '      result.push(item.value);' },
    { type: 'add',     oldNum: null, newNum: 8, content: '    }' },
    { type: 'context', oldNum: 5, newNum: 9, content: '  }' },
    { type: 'context', oldNum: 6, newNum: 10, content: '  return result;' },
    { type: 'context', oldNum: 7, newNum: 11, content: '}' },
  ];

  const lineColors = {
    add: 'rgba(16,185,129,0.08)',
    del: 'rgba(239,68,68,0.08)',
    context: 'transparent',
  };

  const lineTextColors = {
    add: 'var(--success)',
    del: 'var(--danger)',
    context: 'var(--text-primary)',
  };

  return (
    <div style={{ marginBottom: 16, border: '1px solid var(--border)', borderRadius: 'var(--radius)', overflow: 'hidden' }}>
      {/* File header */}
      <div
        onClick={() => setExpanded(e => !e)}
        style={{
          padding: '10px 14px',
          background: 'var(--bg-input)',
          display: 'flex',
          alignItems: 'center',
          gap: 10,
          cursor: 'pointer',
          borderBottom: expanded ? '1px solid var(--border)' : 'none',
        }}
      >
        <span>{expanded ? '▾' : '▸'}</span>
        <span style={{ fontSize: 14 }}>{file.status === 'added' ? '➕' : file.status === 'deleted' ? '➖' : '✏️'}</span>
        <span className="font-mono" style={{ fontSize: 13, flex: 1 }}>{file.filename}</span>
        <span style={{ color: 'var(--success)', fontSize: 11, fontWeight: 600 }}>+{file.additions}</span>
        <span style={{ color: 'var(--danger)', fontSize: 11, fontWeight: 600 }}>-{file.deletions}</span>
      </div>

      {/* Diff content */}
      {expanded && (
        <div style={{ overflowX: 'auto', fontFamily: "'JetBrains Mono', monospace", fontSize: 12 }}>
          {view === 'unified' ? (
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <tbody>
                {diffLines.map((line, i) => (
                  <tr key={i} style={{ background: lineColors[line.type] }}>
                    <td style={{ width: 40, textAlign: 'right', padding: '2px 8px', color: 'var(--text-muted)', userSelect: 'none', borderRight: '1px solid var(--border)' }}>
                      {line.oldNum || ''}
                    </td>
                    <td style={{ width: 40, textAlign: 'right', padding: '2px 8px', color: 'var(--text-muted)', userSelect: 'none', borderRight: '1px solid var(--border)' }}>
                      {line.newNum || ''}
                    </td>
                    <td style={{ width: 20, padding: '2px 4px', color: lineTextColors[line.type], userSelect: 'none' }}>
                      {line.type === 'add' ? '+' : line.type === 'del' ? '-' : ' '}
                    </td>
                    <td style={{ padding: '2px 8px', color: lineTextColors[line.type], whiteSpace: 'pre' }}>
                      {line.content}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ background: 'var(--bg-input)', borderBottom: '1px solid var(--border)' }}>
                  <th colSpan={2} style={{ padding: '6px 12px', textAlign: 'left', fontSize: 11, color: 'var(--text-muted)' }}>Old</th>
                  <th colSpan={2} style={{ padding: '6px 12px', textAlign: 'left', fontSize: 11, color: 'var(--text-muted)', borderLeft: '1px solid var(--border)' }}>New</th>
                </tr>
              </thead>
              <tbody>
                {diffLines.map((line, i) => (
                  <tr key={i}>
                    <td style={{ width: 40, textAlign: 'right', padding: '2px 8px', color: 'var(--text-muted)', userSelect: 'none', borderRight: '1px solid var(--border)', background: line.type === 'del' ? lineColors.del : 'transparent' }}>
                      {line.oldNum || ''}
                    </td>
                    <td style={{ padding: '2px 8px', whiteSpace: 'pre', color: line.type === 'del' ? lineTextColors.del : 'var(--text-primary)', background: line.type === 'del' ? lineColors.del : 'transparent' }}>
                      {line.type === 'del' ? line.content : line.type === 'context' ? line.content : ''}
                    </td>
                    <td style={{ width: 40, textAlign: 'right', padding: '2px 8px', color: 'var(--text-muted)', userSelect: 'none', borderLeft: '1px solid var(--border)', borderRight: '1px solid var(--border)', background: line.type === 'add' ? lineColors.add : 'transparent' }}>
                      {line.newNum || ''}
                    </td>
                    <td style={{ padding: '2px 8px', whiteSpace: 'pre', color: line.type === 'add' ? lineTextColors.add : 'var(--text-primary)', background: line.type === 'add' ? lineColors.add : 'transparent' }}>
                      {line.type === 'add' ? line.content : line.type === 'context' ? line.content : ''}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  );
}
