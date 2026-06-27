import { useEffect, useState } from 'react';
import { getUsers, updateRole } from '../api';
import { relativeTime } from '../utils';
import { toast } from '../components/Toast';

const ROLES = ['admin','product_owner','developer','qa_engineer','requester'];
const PERMS = [
  'submit_request','approve_request','reject_request',
  'approve_plan','reject_plan','merge_pr',
  'approve_qa','fail_qa','approve_prod','manage_users',
];
const MATRIX = {
  admin:         new Set(['*']),
  product_owner: new Set(['submit_request','approve_request','reject_request','approve_plan','reject_plan','approve_qa']),
  developer:     new Set(['submit_request','approve_plan','reject_plan','merge_pr']),
  qa_engineer:   new Set(['submit_request','approve_qa','fail_qa']),
  requester:     new Set(['submit_request']),
};

const has = (role, perm) => MATRIX[role]?.has('*') || MATRIX[role]?.has(perm);

export default function RBAC() {
  const [users,   setUsers]   = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getUsers().then(d => { setUsers(d?.users || []); setLoading(false); });
  }, []);

  const handleRoleChange = async (telegramId, role) => {
    const ok = await updateRole(telegramId, role);
    if (ok) {
      toast('success', '✅ Role Updated', `Now ${role}`);
      setUsers(u => u.map(x => x.telegram_id === telegramId ? { ...x, role } : x));
    } else {
      toast('error', '❌ Failed', 'Could not update role.');
    }
  };

  return (
    <div>
      <div className="section-header">
        <div className="section-title">Role-Based Access Control</div>
      </div>

      {/* Permission Matrix */}
      <div className="card mb-16">
        <div className="card-title">Permission Matrix</div>
        <div className="table-wrap">
          <table className="doc-table">
            <thead>
              <tr>
                <th>Permission</th>
                {ROLES.map(r => <th key={r}>{r.replace(/_/g,' ')}</th>)}
              </tr>
            </thead>
            <tbody>
              {PERMS.map(perm => (
                <tr key={perm}>
                  <td className="font-mono text-xs" style={{color:'var(--accent)'}}>{perm}</td>
                  {ROLES.map(role => (
                    <td key={role} style={{textAlign:'center'}}>
                      {has(role, perm) ? '✅' : <span className="text-muted">—</span>}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Users */}
      <div className="card">
        <div className="card-title">Users</div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Name</th><th>Telegram ID</th><th>Role</th>
                <th>Active</th><th>Joined</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                [1,2].map(i => <tr key={i}><td colSpan={5}>
                  <div className="skeleton" style={{height:36,margin:'4px 0'}}/>
                </td></tr>)
              ) : users.length === 0 ? (
                <tr><td colSpan={5}>
                  <div className="empty">
                    <span className="empty-icon">👥</span>
                    <div className="empty-title">No users yet</div>
                    <div className="empty-desc">Users appear after first Telegram bot interaction.</div>
                  </div>
                </td></tr>
              ) : users.map(u => (
                <tr key={u.telegram_id}>
                  <td style={{fontWeight:600}}>{u.name || '—'}</td>
                  <td><span className="req-id">{u.telegram_id}</span></td>
                  <td>
                    <select
                      value={u.role}
                      onChange={e => handleRoleChange(u.telegram_id, e.target.value)}
                      style={{
                        background:'var(--bg-input)', border:'1px solid var(--border)',
                        borderRadius:'var(--radius-sm)', color:'var(--text-primary)',
                        fontSize:12, padding:'4px 8px', outline:'none', fontFamily:'inherit',
                      }}
                    >
                      {ROLES.map(r => <option key={r} value={r}>{r}</option>)}
                    </select>
                  </td>
                  <td>
                    <span style={{color: u.is_active ? 'var(--success)' : 'var(--danger)'}}>●</span>
                  </td>
                  <td className="text-muted text-xs">{relativeTime(u.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
