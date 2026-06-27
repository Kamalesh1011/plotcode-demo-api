import { useEffect, useState } from 'react';
import { getRepos, getBranches } from '../api';

export default function Branches() {
  const [repos, setRepos] = useState([]);
  const [selected, setSelected] = useState('');
  const [branches, setBranches] = useState([]);
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
    getBranches(selected).then(d => { setBranches(d?.branches || []); setLoading(false); });
  }, [selected]);

  return (
    <div>
      <div className="section-header">
        <div className="section-title">Branches</div>
        <select className="filter-select" value={selected} onChange={e => setSelected(e.target.value)}>
          {repos.map(r => <option key={r.name} value={r.name}>{r.name}</option>)}
        </select>
      </div>
      <div className="card">
        {loading ? (
          <div className="skeleton" style={{height:200}}/>
        ) : branches.length === 0 ? (
          <div className="empty"><span className="empty-icon">🌿</span><div className="empty-title">No branches found</div></div>
        ) : (
          branches.map(b => (
            <div className="branch-row" key={b.name}>
              <span className="branch-icon">🌿</span>
              <span className="branch-name">{b.name}</span>
              <span className="token-pill" style={{marginLeft:'auto'}}>{b.commit}</span>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
