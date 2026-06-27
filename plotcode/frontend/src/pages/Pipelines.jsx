import { useEffect, useState } from 'react';
import { getRepos, getCheckRuns } from '../api';
import { relativeTime } from '../utils';

export default function Pipelines() {
  const [repos, setRepos] = useState([]);
  const [selected, setSelected] = useState('');
  const [runs, setRuns] = useState([]);
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
    getCheckRuns(selected, 'main').then(d => { setRuns(d?.check_runs || []); setLoading(false); });
  }, [selected]);

  return (
    <div>
      <div className="section-header">
        <div className="section-title">CI/CD Pipelines</div>
        <select className="filter-select" value={selected} onChange={e => setSelected(e.target.value)}>
          {repos.map(r => <option key={r.name} value={r.name}>{r.name}</option>)}
        </select>
      </div>
      <div className="card">
        {loading ? (
          <div className="skeleton" style={{height:200}}/>
        ) : runs.length === 0 ? (
          <div className="empty"><span className="empty-icon">⚙️</span><div className="empty-title">No pipeline runs</div><div className="empty-desc">CI check runs will appear here when GitHub Actions is configured.</div></div>
        ) : (
          runs.map((r, i) => (
            <div className="pipeline-row" key={i}>
              <div className={`pipeline-status ${r.conclusion || r.status}`}/>
              <span style={{fontWeight:600, fontSize:13, flex:1}}>{r.name}</span>
              <span className="token-pill">{r.conclusion || r.status}</span>
              {r.html_url && <a href={r.html_url} target="_blank" rel="noreferrer" className="text-xs" style={{color:'var(--accent)'}}>View ↗</a>}
              <span className="text-muted text-xs">{relativeTime(r.completed_at || r.started_at)}</span>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
