import { useEffect, useState, useCallback } from 'react';
import { getRequests, searchRequests } from '../api';
import { relativeTime, statusClass, priorityClass, slaRemaining } from '../utils';

const STATUS_FILTERS = [
  { label:'All',       val:null },
  { label:'Submitted', val:'submitted' },
  { label:'Approved',  val:'approved' },
  { label:'CI',        val:'ci_running' },
  { label:'PR Open',   val:'pr_open' },
  { label:'Deployed',  val:'deployed' },
  { label:'Closed',    val:'closed' },
];

export default function Requests({ onOpenRequest }) {
  const [reqs,     setReqs]     = useState([]);
  const [loading,  setLoading]  = useState(true);
  const [filter,   setFilter]   = useState(null);
  const [priority, setPriority] = useState('');
  const [service,  setService]  = useState('');
  const [services, setServices] = useState([]);
  const [search,   setSearch]   = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    let data;
    if (search.length >= 2) {
      data = await searchRequests(search);
      setReqs(data?.results || []);
    } else {
      data = await getRequests({ status: filter, priority, service, limit: 200 });
      setReqs(data?.requests || []);
    }
    setLoading(false);
  }, [filter, priority, service, search]);

  useEffect(() => { load(); }, [load]);

  // Extract unique services
  useEffect(() => {
    getRequests({ limit: 500 }).then(d => {
      const svcs = [...new Set((d?.requests || []).map(r => r.affected_service).filter(Boolean))];
      setServices(svcs);
    });
  }, []);

  // Debounced search
  useEffect(() => {
    const t = setTimeout(() => load(), 400);
    return () => clearTimeout(t);
  }, [search]);

  const exportAudit = () => {
    window.open('/api/audit/export?format=csv', '_blank');
  };

  return (
    <div>
      <div className="section-header">
        <div className="section-title">Feature Requests <span className="text-muted text-sm">({reqs.length})</span></div>
        <div className="flex gap-8">
          <button className="btn btn-secondary btn-sm" onClick={exportAudit}>⬇ Export Audit</button>
        </div>
      </div>

      {/* Filters */}
      <div className="filters">
        {STATUS_FILTERS.map(f => (
          <button key={f.label} className={`chip ${filter === f.val ? 'active' : ''}`}
            onClick={() => setFilter(f.val)}>
            {f.label}
          </button>
        ))}
        <select className="filter-select" value={priority} onChange={e => setPriority(e.target.value)}>
          <option value="">All Priorities</option>
          {['P0','P1','P2','P3'].map(p => <option key={p} value={p}>{p}</option>)}
        </select>
        <select className="filter-select" value={service} onChange={e => setService(e.target.value)}>
          <option value="">All Services</option>
          {services.map(s => <option key={s} value={s}>{s}</option>)}
        </select>
        {/* Search inline */}
        <div className="search-box" style={{width:200,marginLeft:'auto'}}>
          <span>🔍</span>
          <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search…"/>
        </div>
      </div>

      <div className="card">
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Request ID</th>
                <th>Title</th>
                <th>Priority</th>
                <th>Status</th>
                <th>Service</th>
                <th>Requester</th>
                <th>SLA</th>
                <th>Created</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                [1,2,3].map(i => (
                  <tr key={i}><td colSpan={8}>
                    <div className="skeleton" style={{height:36,margin:'4px 0'}}/>
                  </td></tr>
                ))
              ) : reqs.length === 0 ? (
                <tr><td colSpan={8}>
                  <div className="empty">
                    <span className="empty-icon">📭</span>
                    <div className="empty-title">No requests found</div>
                    <div className="empty-desc">Try clearing filters.</div>
                  </div>
                </td></tr>
              ) : reqs.map(r => {
                const sla = slaRemaining(r.sla_deadline, r.status);
                return (
                  <tr key={r.request_id} onClick={() => onOpenRequest(r.request_id)}>
                    <td><span className="req-id">{r.request_id}</span></td>
                    <td>
                      <span className="truncate" style={{maxWidth:200,display:'block'}}>{r.title}</span>
                    </td>
                    <td><span className={priorityClass(r.priority)}>{r.priority}</span></td>
                    <td><span className={statusClass(r.status)}>{r.status?.replace(/_/g,' ')}</span></td>
                    <td className="text-muted text-sm">{r.affected_service || '—'}</td>
                    <td className="text-muted text-sm">{r.requester_name || '—'}</td>
                    <td>
                      {sla ? (
                        <span className="text-xs" style={{
                          color: sla.cls === 'danger' ? 'var(--danger)'
                               : sla.cls === 'warning' ? 'var(--warning)'
                               : 'var(--text-muted)'
                        }}>{sla.label}</span>
                      ) : <span className="text-muted text-xs">—</span>}
                    </td>
                    <td className="text-muted text-xs">{relativeTime(r.created_at)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
