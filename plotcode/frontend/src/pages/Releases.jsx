import { useEffect, useState } from 'react';
import { getRequests } from '../api';
import { relativeTime } from '../utils';

export default function Releases() {
  const [releases, setReleases] = useState([]);

  useEffect(() => {
    getRequests({ limit: 200 }).then(d => {
      const rel = (d?.requests || []).filter(r => r.release_version || r.status === 'closed');
      setReleases(rel);
    });
  }, []);

  return (
    <div>
      <div className="section-header">
        <div className="section-title">Releases</div>
        <div className="text-muted text-sm">Version history and changelogs</div>
      </div>
      <div className="card">
        {releases.length === 0 ? (
          <div className="empty"><span className="empty-icon">🏷️</span><div className="empty-title">No releases yet</div><div className="empty-desc">Releases appear after requests are deployed and closed.</div></div>
        ) : (
          releases.map(r => (
            <div key={r.request_id} style={{padding:'14px 0', borderBottom:'1px solid var(--border)'}}>
              <div className="flex items-center gap-8 mb-4">
                <span className="token-pill" style={{fontSize:13, padding:'4px 10px'}}>{r.release_version || 'unversioned'}</span>
                <span className="req-id">{r.request_id}</span>
                <span className="text-muted text-xs" style={{marginLeft:'auto'}}>{relativeTime(r.completed_at)}</span>
              </div>
              <div style={{fontWeight:600, fontSize:13}}>{r.title}</div>
              <div className="text-muted text-sm mt-4">{r.affected_service} · {r.requester_name}</div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
