import { useEffect, useState } from 'react';
import { getAgents } from '../api';
import { relativeTime, confColor } from '../utils';

const AGENT_META = {
  analysis:   { icon:'🧠', desc:'Repo analysis & implementation planning',   grad:'var(--primary),var(--accent)' },
  coding:     { icon:'💻', desc:'Code generation & feature branch management', grad:'var(--accent),var(--info)' },
  validation: { icon:'🔬', desc:'CI failure diagnosis & auto-fix loop',       grad:'var(--warning),var(--danger)' },
  pr:         { icon:'🔀', desc:'Pull request creation & review response',    grad:'var(--info),var(--primary)' },
  deployment: { icon:'🚀', desc:'Staging & production deployment triggers',   grad:'var(--success),var(--accent)' },
  monitoring: { icon:'📡', desc:'Health checks, SLA tracking, retrospective', grad:'var(--danger),var(--warning)' },
};

export default function Agents() {
  const [agents, setAgents] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getAgents().then(d => { setAgents(d?.agents || []); setLoading(false); });
  }, []);

  return (
    <div>
      <div className="section-header">
        <div className="section-title">AI Agents</div>
        <div className="text-muted text-sm">Confidence from last run · all models via OpenRouter</div>
      </div>

      {loading ? (
        <div className="grid-3">
          {[1,2,3,4,5,6].map(i => (
            <div className="card" key={i}>
              <div className="skeleton" style={{height:120}}/>
            </div>
          ))}
        </div>
      ) : (
        <div className="grid-3">
          {agents.map(a => {
            const meta = AGENT_META[a.name] || { icon:'🤖', desc:'', grad:'var(--primary),var(--accent)' };
            const conf = a.avg_confidence != null ? Math.round(a.avg_confidence) : null;
            return (
              <div className="agent-card" key={a.name}>
                <div className="flex items-center justify-between">
                  <div className="agent-icon" style={{ background: `linear-gradient(135deg,${meta.grad})` }}>
                    {meta.icon}
                  </div>
                  <span className="badge" style={{
                    background:'rgba(16,185,129,0.1)',
                    color: a.status === 'ready' ? 'var(--success)' : 'var(--warning)',
                    fontSize:10
                  }}>
                    ● {a.status}
                  </span>
                </div>
                <div className="agent-name">
                  {a.name.replace(/_/g,' ').replace(/\b\w/g,c=>c.toUpperCase())} Agent
                </div>
                <div className="agent-desc">{meta.desc}</div>
                {a.last_run_at
                  ? <div className="text-sm text-muted">Last run {relativeTime(a.last_run_at)}</div>
                  : <div className="text-sm text-muted" style={{fontStyle:'italic'}}>No runs yet</div>
                }
                {a.model && (
                  <div className="text-xs font-mono mt-4" style={{color:'var(--accent)'}}>{a.model}</div>
                )}
                {conf != null && (
                  <div className="conf-wrap">
                    <div className="conf-bar">
                      <div className="conf-fill" style={{width:`${conf}%`}}/>
                    </div>
                    <div className="conf-labels">
                      <span>Confidence</span>
                      <span style={{color: confColor(conf)}}>{conf}%</span>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
