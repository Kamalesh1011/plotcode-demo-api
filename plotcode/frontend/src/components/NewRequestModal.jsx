import { useState, useEffect } from 'react';
import { createRequest, getServices } from '../api';
import { toast } from './Toast';

const PRIORITIES = ['P0','P1','P2','P3'];
const PRIORITY_LABELS = { P0:'P0 — Critical', P1:'P1 — High', P2:'P2 — Medium', P3:'P3 — Low' };

export default function NewRequestModal({ onClose, onCreated }) {
  const [services, setServices] = useState([]);
  const [form, setForm] = useState({
    title:'', business_need:'', expected_behavior:'',
    priority:'P2', affected_service:'', requester_name:''
  });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    getServices().then(d => {
      const list = (d?.services || []).map(s => s.name || s.service_name).filter(Boolean);
      setServices(list);
      if (list.length > 0 && !form.affected_service) {
        setForm(f => ({ ...f, affected_service: list[0] }));
      }
    });
  }, []);

  const set = (k) => (e) => setForm(f => ({ ...f, [k]: e.target.value }));

  const submit = async (e) => {
    e.preventDefault();
    setLoading(true);
    const res = await createRequest({ ...form, source: 'dashboard' });
    setLoading(false);
    if (res) {
      toast('success', '🚀 Submitted!', `${res.request_id} created.`);
      onCreated?.(res);
      onClose();
    } else {
      toast('error', '❌ Failed', 'Could not submit request.');
    }
  };

  return (
    <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal">
        <div className="flex items-center justify-between" style={{marginBottom:22}}>
          <div className="modal-title" style={{margin:0}}>Submit Feature Request</div>
          <button className="btn btn-icon" onClick={onClose}>✕</button>
        </div>

        <form onSubmit={submit}>
          <div className="form-group">
            <label className="form-label">Title *</label>
            <input className="form-input" required value={form.title}
              onChange={set('title')} placeholder="e.g. Add rate limiting to /api/users"/>
          </div>
          <div className="form-group">
            <label className="form-label">Business Need *</label>
            <textarea className="form-textarea" required rows={2} value={form.business_need}
              onChange={set('business_need')} placeholder="Why is this needed?"/>
          </div>
          <div className="form-group">
            <label className="form-label">Expected Behavior *</label>
            <textarea className="form-textarea" required rows={2} value={form.expected_behavior}
              onChange={set('expected_behavior')} placeholder="What should it do?"/>
          </div>
          <div className="grid-2" style={{gap:12,marginBottom:16}}>
            <div className="form-group" style={{margin:0}}>
              <label className="form-label">Priority</label>
              <select className="form-select" value={form.priority} onChange={set('priority')}>
                {PRIORITIES.map(p => <option key={p} value={p}>{PRIORITY_LABELS[p]}</option>)}
              </select>
            </div>
            <div className="form-group" style={{margin:0}}>
              <label className="form-label">Service</label>
              <select className="form-select" value={form.affected_service} onChange={set('affected_service')}>
                {services.length === 0 && <option value="">— Loading services —</option>}
                {services.map(s => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>
          </div>
          <div className="form-group">
            <label className="form-label">Your Name *</label>
            <input className="form-input" required value={form.requester_name}
              onChange={set('requester_name')} placeholder="Your name"/>
          </div>
          <div className="flex gap-8" style={{marginTop:6}}>
            <button type="button" className="btn btn-secondary flex-1" onClick={onClose}>Cancel</button>
            <button type="submit" className="btn btn-primary flex-1" disabled={loading}>
              {loading ? 'Submitting…' : 'Submit Request 🚀'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
