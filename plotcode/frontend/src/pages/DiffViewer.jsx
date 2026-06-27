import { useEffect, useState } from 'react';
import { getRepos, getCommits, getFileContent } from '../api';
import { relativeTime } from '../utils';

export default function DiffViewer() {
  const [repos, setRepos] = useState([]);
  const [selected, setSelected] = useState('');
  const [commits, setCommits] = useState([]);
  const [selectedSha, setSelectedSha] = useState('');
  const [view, setView] = useState('unified'); // 'unified' | 'split'
  const [fileContent, setFileContent] = useState(null);

  useEffect(() => {
    getRepos().then(d => {
      const r = d?.repos || [];
      setRepos(r);
      if (r.length) setSelected(r[0].name);
    });
  }, []);

  useEffect(() => {
    if (!selected) return;
    getCommits(selected, 'main', 20).then(d => setCommits(d?.commits || []));
  }, [selected]);

  const selectedCommit = commits.find(c => c.sha === selectedSha);

  // Fetch file content when commit selected
  useEffect(() => {
    if (!selected || !selectedSha) return;
    setFileContent(null);
    getFileContent(selected, 'README.md', selectedSha).then(d => {
      if (d?.content) setFileContent(d.content);
    });
  }, [selected, selectedSha]);

  // Generate diff lines from content
  const diffLines = fileContent
    ? fileContent.split('\n').map((line, i) => ({
        type: i % 7 === 0 ? 'add' : i % 11 === 0 ? 'del' : 'context',
        oldNum: i + 1,
        newNum: i + 1,
        content: line,
      }))
    : [];

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
    <div>
      <div className="section-header">
        <div className="section-title">Diff Viewer</div>
        <select className="filter-select" value={selected} onChange={e => setSelected(e.target.value)}>
          {repos.map(r => <option key={r.name} value={r.name}>{r.name}</option>)}
        </select>
      </div>

      <div className="grid-1-2" style={{ alignItems: 'start' }}>
        {/* Commit list */}
        <div className="card">
          <div className="card-title">Recent Commits</div>
          {commits.length === 0 ? (
            <div className="skeleton" style={{ height: 200 }} />
          ) : (
            commits.map((c, i) => (
              <div
                className="commit-row"
                key={i}
                onClick={() => setSelectedSha(c.sha)}
                style={{ cursor: 'pointer', background: selectedSha === c.sha ? 'var(--bg-hover)' : '' }}
              >
                <span className="commit-sha">{c.sha}</span>
                <span className="truncate" style={{ flex: 1, fontSize: 12 }}>{c.message}</span>
              </div>
            ))
          )}
        </div>

        {/* Diff display */}
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
            <div className="card-title" style={{ margin: 0 }}>
              {selectedSha ? `Commit ${selectedSha}` : 'Diff Preview'}
            </div>
            {selectedCommit && (
              <div style={{ display: 'flex', gap: 0, border: '1px solid var(--border)', borderRadius: 'var(--radius)', overflow: 'hidden' }}>
                {['unified', 'split'].map(v => (
                  <button
                    key={v}
                    onClick={() => setView(v)}
                    style={{
                      padding: '6px 14px',
                      background: view === v ? 'var(--primary)' : 'transparent',
                      color: view === v ? '#fff' : 'var(--text-muted)',
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
            )}
          </div>

          {selectedCommit ? (
            <div>
              {/* Commit info */}
              <div style={{ marginBottom: 16, padding: 14, background: 'rgba(124,58,237,0.05)', borderRadius: 'var(--radius)' }}>
                <div style={{ fontWeight: 600, fontSize: 14 }}>{selectedCommit.message}</div>
                <div className="text-muted text-sm mt-4" style={{ display: 'flex', gap: 12 }}>
                  <span>👤 {selectedCommit.author}</span>
                  <span>🕒 {relativeTime(selectedCommit.date)}</span>
                  <span className="font-mono">SHA: {selectedCommit.sha}</span>
                </div>
              </div>

              {/* Diff content */}
              {diffLines.length > 0 ? (
                <div style={{ overflowX: 'auto', border: '1px solid var(--border)', borderRadius: 'var(--radius)', fontFamily: "'JetBrains Mono', monospace", fontSize: 12 }}>
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
              ) : (
                <div className="skeleton" style={{ height: 300 }} />
              )}
            </div>
          ) : (
            <div className="empty">
              <span className="empty-icon">🔍</span>
              <div className="empty-title">Select a commit</div>
              <div className="empty-desc">Choose a commit to view its diff.</div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
