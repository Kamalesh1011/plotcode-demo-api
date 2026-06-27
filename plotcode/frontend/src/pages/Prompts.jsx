import { useEffect, useState } from 'react';
import { getPrompts } from '../api';
import { relativeTime } from '../utils';

const AGENTS = [
  { value:'',                label:'All Agents' },
  { value:'analysis_agent',  label:'Analysis' },
  { value:'coder_agent',     label:'Coder' },
  { value:'validation_agent',label:'Validation' },
  { value:'pr_agent',        label:'PR' },
  { value:'deployment_agent',label:'Deployment' },
  { value:'monitoring_agent',label:'Monitoring' },
];

export default function Prompts() {
  const [logs,    setLogs]    = useState([]);
  const [loading, setLoading] = useState(true);
  const [agent,   setAgent]   = useState('');

  const load = async (ag = agent) => {
    setLoading(true);
    const d = await getPrompts({ agent_name: ag || undefined, limit: 50 });
    setLogs(d?.logs || []);
    setLoading(false);
  };

  useEffect(() => { load(); }, [agent]);

  return (
    <div>
      <div className="section-header">
        <div className="section-title">Prompt Explorer</div>
        <select className="filter-select" value={agent} onChange={e => setAgent(e.target.value)}>
          {AGENTS.map(a => <option key={a.value} value={a.value}>{a.label}</option>)}
        </select>
      </div>

      {loading ? (
        [1,2,3].map(i => <div key={i} className="skeleton" style={{height:90,marginBottom:8,borderRadius:10}}/>)
      ) : logs.length === 0 ? (
        <div className="empty">
          <span className="empty-icon">🧠</span>
          <div className="empty-title">No prompts logged</div>
          <div className="empty-desc">Prompts appear after agents run on a request.</div>
        </div>
      ) : (
        logs.map((p, i) => {
          const conf = p.confidence_score != null ? Math.round(p.confidence_score) : null;
          const confColor = conf == null ? null : conf >= 80 ? 'var(--success)' : conf >= 60 ? 'var(--warning)' : 'var(--danger)';
          return (
            <div className="prompt-entry" key={i}>
              <div className="prompt-meta">
                <span className="badge status-approved">{p.agent_name}</span>
                <span className="token-pill">↑{p.tokens_input||0} ↓{p.tokens_output||0} tokens</span>
                <span className="token-pill">{p.latency_ms||0}ms</span>
                {conf != null && (
                  <span className="badge" style={{background:'rgba(16,185,129,0.1)',color:confColor}}>
                    {conf}% conf.
                  </span>
                )}
                <span className="text-muted text-xs" style={{marginLeft:'auto'}}>{relativeTime(p.created_at)}</span>
              </div>
              <div className="flex items-center gap-8 mb-4">
                <span className="req-id">{p.request_id}</span>
                {p.prompt_version && (
                  <span className="token-pill">{p.prompt_version}</span>
                )}
                {p.model && (
                  <span className="text-xs text-muted font-mono">{p.model}</span>
                )}
              </div>
              <div className="prompt-preview">
                {(p.prompt_preview || '').trim() || '—'}
              </div>
            </div>
          );
        })
      )}
    </div>
  );
}
