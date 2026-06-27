import { useEffect, useRef, useState } from 'react';
import { getMetrics } from '../api';
import { CHART_DEFAULTS } from '../utils';

let Chart;
const loadChart = async () => {
  if (!Chart) {
    const mod = await import('https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js');
    Chart = window.Chart;
  }
  return Chart;
};

function ChartCanvas({ id, type, data, options }) {
  const canvasRef = useRef(null);
  const chartRef  = useRef(null);

  useEffect(() => {
    let chart;
    loadChart().then((C) => {
      if (!canvasRef.current) return;
      if (chartRef.current) chartRef.current.destroy();
      chartRef.current = new C(canvasRef.current, { type, data, options });
    });
    return () => { chartRef.current?.destroy(); };
  }, [JSON.stringify(data)]);

  return <canvas ref={canvasRef}/>;
}

export default function Metrics() {
  const [m, setM] = useState(null);

  useEffect(() => {
    getMetrics().then(setM);
    // Load chart.js script
    if (!document.querySelector('script[data-chartjs]')) {
      const s = document.createElement('script');
      s.src = 'https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js';
      s.dataset.chartjs = true;
      document.head.appendChild(s);
    }
  }, []);

  const vol7d     = m?.volume_7d || [];
  const stages    = m?.pipeline_stages || [];
  const prio      = m?.priority_distribution || [];
  const agentPerf = m?.agent_performance || [];

  const PCOLS = { P0:'#EF4444',P1:'#F59E0B',P2:'#3B82F6',P3:'#10B981' };
  const DCOLS = [
    'rgba(124,58,237,0.7)','rgba(6,182,212,0.7)','rgba(16,185,129,0.7)',
    'rgba(245,158,11,0.7)','rgba(239,68,68,0.7)','rgba(59,130,246,0.7)',
    'rgba(168,85,247,0.7)','rgba(52,211,153,0.7)',
  ];

  return (
    <div>
      <div className="section-header">
        <div className="section-title">Analytics & Metrics</div>
      </div>

      {!m ? (
        <div className="grid-2">
          {[1,2,3,4].map(i => <div key={i} className="card"><div className="skeleton" style={{height:200}}/></div>)}
        </div>
      ) : (
        <>
          <div className="grid-2 mb-16">
            <div className="card">
              <div className="card-title">Request Volume (Last 7 Days)</div>
              <div className="chart-box">
                {vol7d.length ? (
                  <ChartCanvas type="bar"
                    data={{
                      labels: vol7d.map(v => v.date),
                      datasets:[{
                        label:'Requests',
                        data: vol7d.map(v => v.count),
                        backgroundColor:'rgba(124,58,237,0.55)',
                        borderColor:'rgba(124,58,237,0.9)',
                        borderWidth:1, borderRadius:4,
                      }]
                    }}
                    options={{...CHART_DEFAULTS, responsive:true, maintainAspectRatio:false}}
                  />
                ) : <div className="empty"><span className="empty-icon">📊</span><div className="empty-title">No data yet</div></div>}
              </div>
            </div>
            <div className="card">
              <div className="card-title">Status Distribution</div>
              <div className="chart-box">
                {stages.length ? (
                  <ChartCanvas type="doughnut"
                    data={{
                      labels: stages.map(s => s.status),
                      datasets:[{
                        data: stages.map(s => s.count),
                        backgroundColor: DCOLS,
                        borderWidth:0,
                      }]
                    }}
                    options={{
                      responsive:true, maintainAspectRatio:false,
                      plugins:{legend:{position:'right',labels:{color:'#94A3B8',font:{size:11}}}}
                    }}
                  />
                ) : <div className="empty"><span className="empty-icon">📊</span><div className="empty-title">No data yet</div></div>}
              </div>
            </div>
          </div>

          <div className="grid-2">
            <div className="card">
              <div className="card-title">Priority Breakdown</div>
              <div className="chart-box">
                {prio.length ? (
                  <ChartCanvas type="bar"
                    data={{
                      labels: prio.map(p => p.priority),
                      datasets:[{
                        label:'Count', data:prio.map(p => p.count),
                        backgroundColor: prio.map(p => PCOLS[p.priority] || '#94A3B8'),
                        borderRadius:4,
                      }]
                    }}
                    options={{
                      ...CHART_DEFAULTS, responsive:true, maintainAspectRatio:false,
                      plugins:{legend:{display:false}}
                    }}
                  />
                ) : <div className="empty"><span className="empty-icon">📊</span><div className="empty-title">No data yet</div></div>}
              </div>
            </div>

            <div className="card">
              <div className="card-title">Agent Performance</div>
              {agentPerf.length === 0 ? (
                <div className="empty">
                  <span className="empty-icon">🤖</span>
                  <div className="empty-title">No agent runs yet</div>
                </div>
              ) : (
                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>Agent</th><th>Calls</th><th>Tokens↑</th>
                        <th>Avg ms</th><th>Success</th><th>Conf.</th>
                      </tr>
                    </thead>
                    <tbody>
                      {agentPerf.map(a => (
                        <tr key={a._id}>
                          <td style={{fontWeight:600}}>{a._id}</td>
                          <td>{a.total_calls}</td>
                          <td>{(a.total_tokens_in||0).toLocaleString()}</td>
                          <td>{Math.round(a.avg_latency_ms||0)}</td>
                          <td>{Math.round((a.success_rate||0)*100)}%</td>
                          <td>{a.avg_confidence ? `${Math.round(a.avg_confidence)}%` : '—'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
