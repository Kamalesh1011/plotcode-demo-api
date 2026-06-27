/** Shared helper utilities */

export function relativeTime(iso) {
  if (!iso) return '—';
  const diff = Date.now() - new Date(iso).getTime();
  const m = Math.floor(diff / 60000);
  if (m < 1) return 'just now';
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  return `${Math.floor(h / 24)}d ago`;
}

export function statusClass(status) {
  return `badge status-${status}`;
}

export function priorityClass(p) {
  return `badge badge-${(p || 'P2').toLowerCase()}`;
}

export function slaRemaining(deadline, status) {
  const terminal = ['closed','deployed','rejected'];
  if (!deadline || terminal.includes(status)) return null;
  const hrs = (new Date(deadline).getTime() - Date.now()) / 3600000;
  if (hrs < 0) return { label: '⚠ Overdue', cls: 'danger' };
  if (hrs < 4) return { label: `⏰ ${Math.round(hrs)}h`, cls: 'warning' };
  return { label: `${Math.round(hrs)}h`, cls: 'muted' };
}

export function confColor(v) {
  if (v == null) return 'var(--text-muted)';
  if (v >= 80)  return 'var(--success)';
  if (v >= 60)  return 'var(--warning)';
  return 'var(--danger)';
}

const CHART_DEFAULTS = {
  plugins: {
    legend: { labels: { color: '#94A3B8', font: { family: 'Inter', size: 11 } } }
  },
  scales: {
    x: { ticks:{ color:'#4A5568' }, grid:{ color:'rgba(255,255,255,0.04)' } },
    y: { ticks:{ color:'#4A5568' }, grid:{ color:'rgba(255,255,255,0.04)' } }
  }
};

export { CHART_DEFAULTS };
