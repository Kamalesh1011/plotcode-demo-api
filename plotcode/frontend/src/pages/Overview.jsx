import { useEffect, useState, useRef } from 'react';
import { getMetrics, getRequests } from '../api';
import { relativeTime, statusClass, priorityClass } from '../utils';

const STAGE_ORDER = [
  { key:'submitted',             icon:'📋', label:'Submitted' },
  { key:'approved',              icon:'✅', label:'Approved' },
  { key:'plan_pending_approval', icon:'🧠', label:'Planning' },
  { key:'plan_approved',         icon:'✓',  label:'Plan OK' },
  { key:'ci_running',            icon:'⚙️', label:'CI' },
  { key:'pr_open',               icon:'🔀', label:'PR' },
  { key:'qa_deployed',           icon:'🧪', label:'QA' },
  { key:'deployed',              icon:'🚀', label:'Prod' },
];

export default function Overview({ onOpenRequest, onNav }) {
  const [metrics, setMetrics] = useState(null);
  const [reqs, setReqs]       = useState([]);

  const load = async () => {
    const [m, r] = await Promise.all([getMetrics(), getRequests({ limit: 8 })]);
    setMetrics(m);
    setReqs(r?.requests || []);
  };

  useEffect(() => { load(); }, []);

  const sla = metrics?.sla_compliance_pct ?? 0;
  const circ = 169.6;
  const offset = circ - (sla / 100) * circ;
  const ringColor = sla >= 90 ? 'var(--success)' : sla >= 70 ? 'var(--warning)' : 'var(--danger)';

  const countMap = {};
  (metrics?.pipeline_stages || []).forEach(s => { countMap[s.status] = s.count; });

  return (
    <div>
      {/* Stat Cards */}
      <div className="grid-4 mb-24">
        {[
          { icon:'📦', val: metrics?.total   ?? '—', label:'Total Requests',  glow:'purple' },
          { icon:'⚙️', val: metrics?.active  ?? '—', label:'In Progress',     glow:'cyan' },
          { icon:'🚀', val: metrics?.deployed ?? '—', label:'Deployed',        glow:'green' },
          { icon:'⏱️', val: `${sla}%`,                label:'SLA Compliance', glow:'red' },
        ].map(({ icon, val, label, glow }) => (
          <div className="stat-card" key={label}>
            <div className={`stat-glow glow-${glow}`}/>
            <span className="stat-icon">{icon}</span>
            <div className="stat-value">{val}</div>
            <div className="stat-label">{label}</div>
          </div>
        ))}
      </div>

      <div className="grid-1-2" style={{alignItems:'start'}}>
        {/* Left col */}
        <div>
          {/* Pipeline */}
          <div className="card mb-16">
            <div className="card-title">Pipeline Flow</div>
            <div className="pipeline-track">
              {STAGE_ORDER.map(s => {
                const count = countMap[s.key] || 0;
                return (
                  <div className="pipeline-stage" key={s.key}>
                    <div className={`stage-box ${count > 0 ? 'active' : ''}`}>
                      <div className="stage-icon">{s.icon}</div>
                      <div className="stage-name">{s.label}</div>
                      <div className="stage-count">{count}</div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* SLA ring */}
          <div className="card">
            <div className="card-title">SLA Compliance</div>
            <div className="flex items-center gap-16">
              <div className="sla-ring">
                <svg width="68" height="68" viewBox="0 0 68 68">
                  <circle className="ring-track" cx="34" cy="34" r="27"/>
                  <circle className="ring-fill" cx="34" cy="34" r="27"
                    strokeDasharray={circ}
                    strokeDashoffset={offset}
                    style={{ stroke: ringColor, transition:'stroke-dashoffset 1.2s ease' }}
                  />
                </svg>
                <div className="sla-ring-label">{sla}%</div>
              </div>
              <div>
                <div style={{fontSize:24,fontWeight:800}}>{sla}%</div>
                <div className="text-muted text-sm">delivered on time</div>
                {metrics?.sla_breached > 0
                  ? <div className="text-xs mt-4" style={{color:'var(--danger)'}}>⚠️ {metrics.sla_breached} breached</div>
                  : <div className="text-xs mt-4" style={{color:'var(--success)'}}>✅ No breaches</div>
                }
              </div>
            </div>
          </div>
        </div>

        {/* Recent */}
        <div className="card">
          <div className="section-header mb-16">
            <div className="card-title" style={{margin:0}}>Recent Activity</div>
            <button className="btn btn-secondary btn-sm" onClick={() => onNav('requests')}>View all</button>
          </div>

          {reqs.length === 0
            ? (
              <div className="empty">
                <span className="empty-icon">📭</span>
                <div className="empty-title">No requests yet</div>
                <div className="empty-desc">Submit your first feature request.</div>
              </div>
            )
            : reqs.map(r => (
              <div key={r.request_id}
                onClick={() => onOpenRequest(r.request_id)}
                style={{
                  display:'flex', alignItems:'center', gap:12, cursor:'pointer',
                  padding:'10px 12px', marginBottom:6,
                  border:'1px solid var(--border)', borderRadius:'var(--radius)',
                  background:'rgba(255,255,255,0.02)', transition:'var(--transition)',
                }}
                onMouseOver={e => e.currentTarget.style.background='var(--bg-hover)'}
                onMouseOut={e  => e.currentTarget.style.background='rgba(255,255,255,0.02)'}
              >
                <div style={{flex:1,minWidth:0}}>
                  <div className="flex items-center gap-8 mb-4">
                    <span className="req-id">{r.request_id}</span>
                    <span className={priorityClass(r.priority)}>{r.priority}</span>
                  </div>
                  <div className="truncate" style={{fontWeight:500,fontSize:13}}>{r.title}</div>
                </div>
                <div>
                  <span className={statusClass(r.status)}>{r.status?.replace(/_/g,' ')}</span>
                </div>
              </div>
            ))
          }
        </div>
      </div>
    </div>
  );
}
