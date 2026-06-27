import { useEffect, useState } from 'react';
import { apiFetch } from '../api';
import { relativeTime } from '../utils';

export default function Audit() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiFetch('/audit/export?format=json').then(d => {
      setLogs(d?.logs || []);
      setLoading(false);
    });
  }, []);

  const exportCsv = () => window.open('/api/audit/export?format=csv', '_blank');

  return (
    <div>
      <div className="section-header">
        <div className="section-title">Audit Log</div>
        <button className="btn btn-secondary btn-sm" onClick={exportCsv}>⬇ Export CSV</button>
      </div>
      <div className="card">
        <div className="table-wrap">
          <table>
            <thead>
              <tr><th>Time</th><th>Request</th><th>Actor</th><th>Type</th><th>Action</th></tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={5}><div className="skeleton" style={{height:200}}/></td></tr>
              ) : logs.length === 0 ? (
                <tr><td colSpan={5}><div className="empty"><span className="empty-icon">📜</span><div className="empty-title">No audit entries</div></div></td></tr>
              ) : logs.slice(0, 100).map((l, i) => (
                <tr key={i}>
                  <td className="text-muted text-xs">{relativeTime(l.created_at)}</td>
                  <td><span className="req-id">{l.request_id}</span></td>
                  <td className="text-sm">{l.actor_id}</td>
                  <td><span className="badge" style={{background:'rgba(124,58,237,0.1)', color:l.actor_type === 'ai' ? 'var(--accent)' : 'var(--primary-light)'}}>{l.actor_type}</span></td>
                  <td className="text-sm font-mono">{l.action}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
