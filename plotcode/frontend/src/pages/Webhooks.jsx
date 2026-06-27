import { useEffect, useState } from 'react';
import { getWebhooks, createWebhook, toggleWebhook, deleteWebhook } from '../api';
import { toast } from '../components/Toast';

export default function Webhooks() {
  const [hooks, setHooks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [newUrl, setNewUrl] = useState('');
  const [newEvents, setNewEvents] = useState('push,pull_request');

  const load = () => {
    setLoading(true);
    getWebhooks().then(d => { setHooks(d?.webhooks || []); setLoading(false); });
  };

  useEffect(() => { load(); }, []);

  const add = async () => {
    if (!newUrl.trim()) return;
    const result = await createWebhook(newUrl, newEvents);
    if (result?.webhook) {
      toast('success', '✅ Webhook Added', 'New webhook endpoint registered.');
      setNewUrl('');
      load();
    } else {
      toast('error', '❌ Failed', 'Could not add webhook.');
    }
  };

  const toggle = async (id, current) => {
    await toggleWebhook(id, !current);
    load();
  };

  const remove = async (id) => {
    await deleteWebhook(id);
    toast('info', '🗑️ Removed', 'Webhook deleted.');
    load();
  };

  return (
    <div>
      <div className="section-header">
        <div className="section-title">Webhooks</div>
      </div>

      <div className="card mb-16">
        <div className="card-title">Add Webhook</div>
        <div className="form-group">
          <label className="form-label">URL</label>
          <input className="form-input" value={newUrl} onChange={e => setNewUrl(e.target.value)}
            placeholder="https://your-endpoint.com/webhook"/>
        </div>
        <div className="form-group">
          <label className="form-label">Events (comma-separated)</label>
          <input className="form-input" value={newEvents} onChange={e => setNewEvents(e.target.value)}
            placeholder="push,pull_request,ci.failed"/>
        </div>
        <button className="btn btn-primary" onClick={add}>➕ Add Webhook</button>
      </div>

      <div className="card">
        <div className="card-title">Registered Webhooks</div>
        {loading ? (
          <div className="skeleton" style={{height:100}}/>
        ) : hooks.length === 0 ? (
          <div className="empty"><span className="empty-icon">🔗</span><div className="empty-title">No webhooks</div><div className="empty-desc">Add a webhook endpoint above.</div></div>
        ) : hooks.map(h => (
          <div key={h.id} style={{padding:'14px 0', borderBottom:'1px solid var(--border)', display:'flex', alignItems:'center', gap:12}}>
            <div className={`toggle-switch ${h.active ? 'on' : ''}`} onClick={() => toggle(h.id, h.active)}/>
            <div style={{flex:1}}>
              <div className="font-mono text-sm">{h.url}</div>
              <div className="flex gap-8 mt-4">
                {(h.events || []).map(e => <span key={e} className="token-pill">{e}</span>)}
              </div>
              <div className="text-muted text-xs mt-4">Added by {h.created_by || '—'} · {h.created_at?.slice(0,10) || '—'}</div>
            </div>
            <button className="btn btn-ghost" onClick={() => remove(h.id)} style={{color:'var(--danger)'}}>🗑️</button>
          </div>
        ))}
      </div>
    </div>
  );
}
