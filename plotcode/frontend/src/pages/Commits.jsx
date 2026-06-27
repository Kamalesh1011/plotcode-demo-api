import { useEffect, useState } from 'react';
import { getRepos, getCommits } from '../api';
import { relativeTime } from '../utils';

export default function Commits() {
  const [repos, setRepos] = useState([]);
  const [selected, setSelected] = useState('');
  const [commits, setCommits] = useState([]);
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
    getCommits(selected, 'main', 30).then(d => { setCommits(d?.commits || []); setLoading(false); });
  }, [selected]);

  return (
    <div>
      <div className="section-header">
        <div className="section-title">Commits</div>
        <select className="filter-select" value={selected} onChange={e => setSelected(e.target.value)}>
          {repos.map(r => <option key={r.name} value={r.name}>{r.name}</option>)}
        </select>
      </div>
      <div className="card">
        {loading ? (
          <div className="skeleton" style={{height:300}}/>
        ) : commits.length === 0 ? (
          <div className="empty"><span className="empty-icon">📝</span><div className="empty-title">No commits found</div></div>
        ) : (
          commits.map((c, i) => (
            <div className="commit-row" key={i}>
              <span className="commit-sha">{c.sha}</span>
              <span className="commit-msg truncate" style={{flex:1}}>{c.message}</span>
              <span className="commit-author">{c.author}</span>
              <span className="commit-date">{relativeTime(c.date)}</span>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
