import { useEffect, useState } from 'react';
import { getRepos, getIssues } from '../api';
import { relativeTime } from '../utils';

export default function Issues() {
  const [repos, setRepos] = useState([]);
  const [selected, setSelected] = useState('');
  const [issues, setIssues] = useState([]);
  const [state, setState] = useState('open');
  const [loading, setLoading] = useState(false);

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
    getIssues(selected, state, 30).then(d => { setIssues(d?.issues || []); setLoading(false); });
  }, [selected, state]);

  return (
    <div>
      <div className="section-header">
        <div className="section-title">Issues</div>
        <select className="filter-select" value={state} onChange={e => setState(e.target.value)}>
          <option value="open">Open</option>
          <option value="closed">Closed</option>
          <option value="all">All</option>
        </select>
        <select className="filter-select" value={selected} onChange={e => setSelected(e.target.value)}>
          {repos.map(r => <option key={r.name} value={r.name}>{r.name}</option>)}
        </select>
      </div>
      <div className="card">
        {loading ? (
          <div className="skeleton" style={{height:300}}/>
        ) : issues.length === 0 ? (
          <div className="empty"><span className="empty-icon">🐛</span><div className="empty-title">No issues found</div></div>
        ) : (
          issues.map(issue => (
            <div className="pr-row" key={issue.number} onClick={() => window.open(issue.url, '_blank')}>
              <span className="pr-number">#{issue.number}</span>
              <span className={`pr-state ${issue.state}`}>{issue.state}</span>
              <span style={{flex:1, fontWeight:500, fontSize:13}} className="truncate">{issue.title}</span>
              {issue.labels?.map(l => <span key={l} className="token-pill">{l}</span>)}
              <span className="text-muted text-xs">{relativeTime(issue.created_at)}</span>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
