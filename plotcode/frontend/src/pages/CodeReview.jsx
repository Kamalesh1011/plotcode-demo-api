import { useEffect, useState } from 'react';
import { getRequests } from '../api';
import { relativeTime, statusClass, priorityClass } from '../utils';

export default function CodeReview() {
  const [reqs, setReqs] = useState([]);

  useEffect(() => {
    getRequests({ limit: 100 }).then(d => {
      const reviewable = (d?.requests || []).filter(r =>
        ['plan_pending_approval', 'plan_approved', 'pr_open'].includes(r.status)
      );
      setReqs(reviewable);
    });
  }, []);

  return (
    <div>
      <div className="section-header">
        <div className="section-title">Code Review</div>
        <div className="text-muted text-sm">Plans and PRs awaiting review</div>
      </div>
      <div className="grid-2">
        {reqs.length === 0 ? (
          <div className="card" style={{gridColumn:'span 2'}}>
            <div className="empty"><span className="empty-icon">👁️</span><div className="empty-title">Nothing to review</div><div className="empty-desc">Plans and PRs will appear here for review.</div></div>
          </div>
        ) : reqs.map(r => (
          <div className="card" key={r.request_id}>
            <div className="flex items-center gap-8 mb-16">
              <span className="req-id">{r.request_id}</span>
              <span className={priorityClass(r.priority)}>{r.priority}</span>
              <span className={statusClass(r.status)}>{r.status?.replace(/_/g,' ')}</span>
            </div>
            <div style={{fontWeight:600, fontSize:14, marginBottom:8}}>{r.title}</div>
            <div className="text-muted text-sm" style={{marginBottom:12}}>{r.business_need}</div>
            {r.implementation_plan && (
              <div className="plan-block" style={{maxHeight:160, marginBottom:12}}>
                {r.implementation_plan.slice(0, 800)}…
              </div>
            )}
            {r.pr_url && (
              <a href={r.pr_url} target="_blank" rel="noreferrer" className="btn btn-secondary btn-sm">
                🔀 View PR #{r.pr_number} ↗
              </a>
            )}
            <div className="text-muted text-xs mt-8">Updated {relativeTime(r.updated_at)}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
