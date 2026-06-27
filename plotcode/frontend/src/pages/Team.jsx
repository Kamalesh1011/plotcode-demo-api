import { useEffect, useState } from 'react';
import { getUsers } from '../api';
import { relativeTime } from '../utils';

export default function Team() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getUsers().then(d => { setUsers(d?.users || []); setLoading(false); });
  }, []);

  const roleColors = {
    admin: 'var(--danger)', product_owner: 'var(--primary-light)',
    developer: 'var(--accent)', qa_engineer: 'var(--warning)', requester: 'var(--text-muted)',
  };

  return (
    <div>
      <div className="section-header">
        <div className="section-title">Team Members</div>
        <div className="text-muted text-sm">{users.length} members</div>
      </div>
      <div className="grid-3">
        {loading ? (
          [1,2,3].map(i => <div key={i} className="card"><div className="skeleton" style={{height:100}}/></div>)
        ) : users.length === 0 ? (
          <div className="card" style={{gridColumn:'span 3'}}>
            <div className="empty"><span className="empty-icon">👥</span><div className="empty-title">No team members</div><div className="empty-desc">Users appear after first interaction with the Telegram bot.</div></div>
          </div>
        ) : users.map(u => (
          <div className="card" key={u.telegram_id}>
            <div className="flex items-center gap-12 mb-16">
              <div style={{
                width:40, height:40, borderRadius:'50%',
                background:'linear-gradient(135deg, var(--primary), var(--accent))',
                display:'flex', alignItems:'center', justifyContent:'center',
                fontSize:18, color:'#fff', fontWeight:700,
              }}>{(u.name || 'U')[0].toUpperCase()}</div>
              <div>
                <div style={{fontWeight:700, fontSize:14}}>{u.name || 'Unknown'}</div>
                <span className="badge" style={{background:'rgba(124,58,237,0.1)', color: roleColors[u.role] || 'var(--text-muted)'}}>
                  {u.role}
                </span>
              </div>
            </div>
            <div className="text-muted text-xs">Telegram: {u.telegram_id}</div>
            <div className="text-muted text-xs mt-4">Joined {relativeTime(u.created_at)}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
