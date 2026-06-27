import { useState, useEffect } from 'react';
import { relativeTime } from '../utils';

// Notifications are derived from WebSocket events stored locally
export default function Notifications() {
  const [notifications, setNotifications] = useState(() => {
    const s = localStorage.getItem('plotcode_notifications');
    return s ? JSON.parse(s) : [];
  });

  useEffect(() => {
    // Listen for events via a custom event (App.jsx could dispatch these)
    const handler = (e) => {
      const notif = e.detail;
      setNotifications(prev => {
        const updated = [{ ...notif, id: Date.now(), time: new Date().toISOString() }, ...prev].slice(0, 50);
        localStorage.setItem('plotcode_notifications', JSON.stringify(updated));
        return updated;
      });
    };
    window.addEventListener('plotcode:notification', handler);
    return () => window.removeEventListener('plotcode:notification', handler);
  }, []);

  const clearAll = () => {
    setNotifications([]);
    localStorage.removeItem('plotcode_notifications');
  };

  return (
    <div>
      <div className="section-header">
        <div className="section-title">Notifications</div>
        {notifications.length > 0 && (
          <button className="btn btn-secondary btn-sm" onClick={clearAll}>Clear All</button>
        )}
      </div>
      <div className="card">
        {notifications.length === 0 ? (
          <div className="empty"><span className="empty-icon">🔔</span><div className="empty-title">No notifications</div><div className="empty-desc">Real-time alerts will appear here.</div></div>
        ) : (
          notifications.map(n => (
            <div key={n.id} style={{padding:'12px 0', borderBottom:'1px solid var(--border)', display:'flex', alignItems:'center', gap:12}}>
              <span style={{fontSize:18}}>{n.icon || '🔔'}</span>
              <div style={{flex:1}}>
                <div style={{fontWeight:600, fontSize:13}}>{n.title}</div>
                <div className="text-muted text-sm">{n.message}</div>
              </div>
              <span className="text-muted text-xs">{relativeTime(n.time)}</span>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
