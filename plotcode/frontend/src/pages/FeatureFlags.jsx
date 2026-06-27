import { useEffect, useState } from 'react';
import { getFeatureFlags, toggleFeatureFlag, createFeatureFlag, deleteFeatureFlag } from '../api';
import { toast } from '../components/Toast';

export default function FeatureFlags() {
  const [flags, setFlags] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [newKey, setNewKey] = useState('');
  const [newDesc, setNewDesc] = useState('');

  const load = () => {
    setLoading(true);
    getFeatureFlags().then(d => { setFlags(d?.flags || []); setLoading(false); });
  };

  useEffect(() => { load(); }, []);

  const toggle = async (key, env, current) => {
    const result = await toggleFeatureFlag(key, env, !current);
    if (result?.updated) {
      toast('success', '🚩 Flag Updated', `${key} → ${env} ${!current ? 'ON' : 'OFF'}`);
      load();
    } else {
      toast('error', '❌ Update Failed', 'Could not toggle flag.');
    }
  };

  const add = async () => {
    if (!newKey.trim()) return;
    const result = await createFeatureFlag(newKey, newDesc);
    if (result?.flag) {
      toast('success', '✅ Flag Created', `${newKey} added.`);
      setNewKey(''); setNewDesc(''); setShowAdd(false);
      load();
    } else {
      toast('error', '❌ Failed', 'Flag may already exist.');
    }
  };

  const remove = async (key) => {
    await deleteFeatureFlag(key);
    toast('info', '🗑️ Deleted', `Flag ${key} removed.`);
    load();
  };

  return (
    <div>
      <div className="section-header">
        <div className="section-title">Feature Flags</div>
        <button className="btn btn-primary btn-sm" onClick={() => setShowAdd(s => !s)}>➕ New Flag</button>
      </div>

      {showAdd && (
        <div className="card mb-16">
          <div className="card-title">Create Feature Flag</div>
          <div className="form-group">
            <label className="form-label">Key</label>
            <input className="form-input" value={newKey} onChange={e => setNewKey(e.target.value)}
              placeholder="my_feature_flag"/>
          </div>
          <div className="form-group">
            <label className="form-label">Description</label>
            <input className="form-input" value={newDesc} onChange={e => setNewDesc(e.target.value)}
              placeholder="What this flag controls"/>
          </div>
          <button className="btn btn-primary btn-sm" onClick={add}>Create</button>
        </div>
      )}

      <div className="card">
        {loading ? (
          <div className="skeleton" style={{height:200}}/>
        ) : flags.length === 0 ? (
          <div className="empty"><span className="empty-icon">🚩</span><div className="empty-title">No feature flags</div><div className="empty-desc">Create a flag to get started.</div></div>
        ) : flags.map(f => (
          <div className="flag-row" key={f.key}>
            <div className="flag-info">
              <span className="flag-name">{f.key}</span>
              <span className="flag-desc">{f.desc || '—'}</span>
              <div className="flag-envs">
                {Object.entries(f.envs || {}).map(([env, on]) => (
                  <span key={env} className={`flag-env ${on ? 'on' : 'off'}`}
                    onClick={() => toggle(f.key, env, on)} style={{cursor:'pointer'}}>
                    {env}: {on ? 'ON' : 'OFF'}
                  </span>
                ))}
              </div>
              <div className="text-muted text-xs mt-4">Updated by {f.updated_by || '—'} · {f.updated_at?.slice(0,10) || '—'}</div>
            </div>
            <button className="btn btn-ghost" onClick={() => remove(f.key)} style={{color:'var(--danger)'}}>🗑️</button>
          </div>
        ))}
      </div>
    </div>
  );
}
