import { useEffect, useState } from 'react';
import { getRequest, getRequestAudit, approveRequest } from '../api';
import { relativeTime, statusClass, priorityClass } from '../utils';
import { toast } from './Toast';

export default function RequestDrawer({ requestId, onClose }) {
  const [req, setReq] = useState(null);
  const [audit, setAudit] = useState([]);

  useEffect(() => {
    if (!requestId) return;
    Promise.all([
      getRequest(requestId),
      getRequestAudit(requestId),
    ]).then(([r, a]) => {
      setReq(r);
      setAudit(a?.logs || []);
    });
  }, [requestId]);

  const handleApprove = async () => {
    const res = await approveRequest(requestId);
    if (res) {
      toast('success', '✅ Approved', `${requestId} — analysis starting…`);
      onClose();
    } else {
      toast('error', '❌ Failed', 'Could not approve.');
    }
  };

  const fields = req ? [
    ['Status',         <span className={statusClass(req.status)}>{req.status?.replace(/_/g,' ')}</span>],
    ['Priority',       <span className={priorityClass(req.priority)}>{req.priority}</span>],
    ['Service',        req.affected_service || '—'],
    ['Requester',      req.requester_name || '—'],
    ['Branch',         req.feature_branch ? <span className="req-id">{req.feature_branch}</span> : '—'],
    ['PR',             req.pr_url ? <a href={req.pr_url} target="_blank" rel="noreferrer" style={{color:'var(--accent)'}}>#${req.pr_number} ↗</a> : '—'],
    ['Staging',        req.staging_url ? <a href={req.staging_url} target="_blank" rel="noreferrer" style={{color:'var(--accent)'}}>Open ↗</a> : '—'],
    ['Confidence',     req.ai_confidence ? <span style={{color: req.ai_confidence >= 80 ? 'var(--success)' : 'var(--warning)'}}>{req.ai_confidence}%</span> : '—'],
    ['Created',        req.created_at ? new Date(req.created_at).toLocaleString() : '—'],
  ] : [];

  return (
    <>
      <div className="drawer-overlay" onClick={onClose} />
      <div className="drawer">
        <div className="drawer-header">
          <div>
            <div style={{fontSize:16,fontWeight:700}}>{requestId}</div>
            <div className="text-muted text-sm">{req?.title || 'Loading…'}</div>
          </div>
          <button className="btn btn-icon" onClick={onClose}>✕</button>
        </div>

        <div className="drawer-body">
          {!req ? (
            <>
              <div className="skeleton" style={{height:120,marginBottom:16,borderRadius:10}}/>
              <div className="skeleton" style={{height:80,marginBottom:16,borderRadius:10}}/>
              <div className="skeleton" style={{height:180,borderRadius:10}}/>
            </>
          ) : (
            <>
              {/* Details */}
              <div className="drawer-section">
                <div className="drawer-section-title">Details</div>
                {fields.map(([k, v]) => (
                  <div className="detail-row" key={k}>
                    <div className="detail-key">{k}</div>
                    <div className="detail-val">{v}</div>
                  </div>
                ))}
              </div>

              {/* Description */}
              <div className="drawer-section">
                <div className="drawer-section-title">Business Need</div>
                <div className="text-sm text-muted" style={{lineHeight:1.75}}>{req.business_need || '—'}</div>
              </div>
              <div className="drawer-section">
                <div className="drawer-section-title">Expected Behavior</div>
                <div className="text-sm text-muted" style={{lineHeight:1.75}}>{req.expected_behavior || '—'}</div>
              </div>

              {/* Plan */}
              {req.implementation_plan && (
                <div className="drawer-section">
                  <div className="drawer-section-title">Implementation Plan</div>
                  <div className="plan-block">{req.implementation_plan}</div>
                </div>
              )}

              {/* Risk */}
              {req.risk_notes && (
                <div className="drawer-section">
                  <div className="drawer-section-title">Risk Notes</div>
                  <div className="plan-block">{req.risk_notes}</div>
                </div>
              )}

              {/* Audit */}
              <div className="drawer-section">
                <div className="drawer-section-title">Audit Trail ({audit.length})</div>
                <div className="timeline">
                  {audit.length === 0
                    ? <div className="text-sm text-muted">No events yet.</div>
                    : audit.map((l, i) => (
                      <div className="tl-item" key={i}>
                        <div className="tl-time">{relativeTime(l.created_at)}</div>
                        <div className="tl-action">{l.action}</div>
                        <div className="tl-actor">{l.actor_type} · {l.actor_id}</div>
                      </div>
                    ))
                  }
                </div>
              </div>

              {/* Actions */}
              <div className="flex gap-8" style={{marginTop:16,flexWrap:'wrap'}}>
                {req.status === 'submitted' && (
                  <button className="btn btn-primary btn-sm" onClick={handleApprove}>✅ Approve</button>
                )}
                {req.pr_url && (
                  <a href={req.pr_url} target="_blank" rel="noreferrer" className="btn btn-secondary btn-sm">🔀 View PR</a>
                )}
                <button className="btn btn-secondary btn-sm"
                  onClick={() => { navigator.clipboard.writeText(requestId); toast('info','📋 Copied', requestId); }}>
                  📋 Copy ID
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </>
  );
}
