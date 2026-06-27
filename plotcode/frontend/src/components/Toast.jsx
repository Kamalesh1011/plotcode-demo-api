import { useState, useCallback } from 'react';

let _setToasts;

export function ToastContainer() {
  const [toasts, setToasts] = useState([]);
  _setToasts = setToasts;

  const remove = (id) => setToasts(t => t.filter(x => x.id !== id));

  const ICONS = { success:'✅', info:'ℹ️', warning:'⚠️', error:'❌' };

  return (
    <div className="toast-container">
      {toasts.map(t => (
        <div key={t.id} className={`toast ${t.type}`}>
          <span className="toast-icon">{ICONS[t.type] || 'ℹ️'}</span>
          <div style={{flex:1}}>
            <div className="toast-title">{t.title}</div>
            {t.msg && <div className="toast-msg">{t.msg}</div>}
          </div>
          <button className="toast-close" onClick={() => remove(t.id)}>✕</button>
        </div>
      ))}
    </div>
  );
}

let _id = 0;
export function toast(type, title, msg, duration = 5000) {
  if (!_setToasts) return;
  const id = ++_id;
  _setToasts(t => [...t, { id, type, title, msg }]);
  setTimeout(() => _setToasts(t => t.filter(x => x.id !== id)), duration);
}
