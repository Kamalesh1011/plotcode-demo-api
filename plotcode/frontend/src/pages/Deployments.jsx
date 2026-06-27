import { useEffect, useState } from 'react';
import { getRequests } from '../api';
import { relativeTime, statusClass } from '../utils';

export default function Deployments() {
  const [reqs, setReqs] = useState([]);

  useEffect(() => {
    getRequests({ limit: 100 }).then(d => {
      const deployed = (d?.requests || []).filter(r =>
        ['qa_deployed','deployed','closed'].includes(r.status)
      );
      setReqs(deployed);
    });
  }, []);

  return (
    <div>
      <div className="section-header">
        <div className="section-title">Deployments</div>
        <div className="text-muted text-sm">QA, staging, and production deployment history</div>
      </div>
      <div className="card">
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Request</th><th>Title</th><th>Environment</th>
                <th>Status</th><th>URL</th><th>Deployed</th>
              </tr>
            </thead>
            <tbody>
              {reqs.length === 0 ? (
                <tr><td colSpan={6}>
                  <div className="empty"><span className="empty-icon">🚀</span><div className="empty-title">No deployments yet</div></div>
                </td></tr>
              ) : reqs.map(r => (
                <tr key={r.request_id}>
                  <td><span className="req-id">{r.request_id}</span></td>
                  <td className="truncate" style={{maxWidth:200}}>{r.title}</td>
                  <td>{r.production_url ? '🏭 Production' : r.staging_url ? '🧪 Staging' : '—'}</td>
                  <td><span className={statusClass(r.status)}>{r.status?.replace(/_/g,' ')}</span></td>
                  <td className="text-muted text-xs truncate" style={{maxWidth:180}}>
                    {r.production_url || r.staging_url || '—'}
                  </td>
                  <td className="text-muted text-xs">{relativeTime(r.deploy_timestamp || r.updated_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
