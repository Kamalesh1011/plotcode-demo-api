import { useState, useEffect, useRef } from 'react';

const PIPELINE_STEPS = [
  { icon: '📝', label: 'Submit',   color: '#7C3AED' },
  { icon: '🧠', label: 'AI Plan',  color: '#06B6D4' },
  { icon: '💻', label: 'Code',     color: '#10B981' },
  { icon: '⚙️', label: 'CI/CD',   color: '#F59E0B' },
  { icon: '🔀', label: 'PR',       color: '#3B82F6' },
  { icon: '🚀', label: 'Deploy',   color: '#EF4444' },
];

const FEATURES = [
  {
    icon: '🧠',
    title: 'AI-Powered Analysis',
    desc: 'GPT-4o analyses your codebase, identifies impacted files, generates a detailed implementation plan — with a confidence score.',
    grad: 'linear-gradient(135deg,#7C3AED,#9F67FF)',
  },
  {
    icon: '🔄',
    title: 'Auto CI/CD Loop',
    desc: 'Validation agent reads CI failure logs, diagnoses the root cause, and applies fixes automatically — up to 3 retries, zero manual effort.',
    grad: 'linear-gradient(135deg,#06B6D4,#3B82F6)',
  },
  {
    icon: '👥',
    title: 'Human-in-the-Loop',
    desc: 'Every critical decision — plan approval, PR merge, QA sign-off, prod deploy — requires explicit human approval via Telegram or the dashboard.',
    grad: 'linear-gradient(135deg,#10B981,#06B6D4)',
  },
  {
    icon: '📡',
    title: 'Real-Time Dashboard',
    desc: 'WebSocket-powered live feed. Watch requests flow through 14 SDLC stages in real time with full audit trail and SLA tracking.',
    grad: 'linear-gradient(135deg,#F59E0B,#EF4444)',
  },
  {
    icon: '🔐',
    title: 'Role-Based Access',
    desc: 'Five roles — admin, product owner, developer, QA engineer, requester — each with granular permissions across all 14 pipeline stages.',
    grad: 'linear-gradient(135deg,#EF4444,#7C3AED)',
  },
  {
    icon: '☁️',
    title: 'MongoDB Atlas Native',
    desc: 'Serverless MongoDB Atlas with full-text search, aggregation pipelines for metrics, SLA breach tracking, and indexed audit logs.',
    grad: 'linear-gradient(135deg,#7C3AED,#06B6D4)',
  },
];

const STATS = [
  { value: '14', label: 'SDLC Stages', suffix: '' },
  { value: '6',  label: 'AI Agents',   suffix: '' },
  { value: '25', label: 'Features',    suffix: '+' },
  { value: '0',  label: 'Manual CI Steps', suffix: '' },
];

function useCountUp(target, duration = 1500, start = false) {
  const [count, setCount] = useState(0);
  useEffect(() => {
    if (!start) return;
    let startTime;
    const step = (timestamp) => {
      if (!startTime) startTime = timestamp;
      const progress = Math.min((timestamp - startTime) / duration, 1);
      setCount(Math.floor(progress * target));
      if (progress < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  }, [target, duration, start]);
  return count;
}

function AnimatedStat({ value, label, suffix, animate }) {
  const num = useCountUp(parseInt(value), 1200, animate);
  return (
    <div style={{ textAlign: 'center' }}>
      <div style={{
        fontSize: 48, fontWeight: 800, letterSpacing: -2,
        background: 'linear-gradient(135deg,#7C3AED,#06B6D4)',
        WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
        lineHeight: 1,
      }}>
        {animate ? num : value}{suffix}
      </div>
      <div style={{ fontSize: 13, color: 'rgba(255,255,255,0.5)', marginTop: 6, fontWeight: 500 }}>
        {label}
      </div>
    </div>
  );
}

export default function Landing({ onGetStarted }) {
  const [statsVisible, setStatsVisible] = useState(false);
  const [activePipe, setActivePipe]     = useState(0);
  const statsRef = useRef(null);

  // Pipeline animation
  useEffect(() => {
    const t = setInterval(() => setActivePipe(p => (p + 1) % PIPELINE_STEPS.length), 900);
    return () => clearInterval(t);
  }, []);

  // Intersection observer for stats counter
  useEffect(() => {
    const obs = new IntersectionObserver(([e]) => { if (e.isIntersecting) setStatsVisible(true); }, { threshold: 0.4 });
    if (statsRef.current) obs.observe(statsRef.current);
    return () => obs.disconnect();
  }, []);

  return (
    <div style={{ minHeight: '100vh', overflowY: 'auto', overflowX: 'hidden', background: '#030B14' }}>

      {/* ── Ambient glows ── */}
      <div style={{
        position: 'fixed', inset: 0, pointerEvents: 'none', zIndex: 0,
        background: `
          radial-gradient(ellipse 80% 50% at 15% 10%, rgba(124,58,237,0.18) 0%, transparent 60%),
          radial-gradient(ellipse 60% 40% at 85% 80%, rgba(6,182,212,0.12) 0%, transparent 55%)
        `,
      }}/>

      {/* ── Navbar ── */}
      <nav style={{
        position: 'sticky', top: 0, zIndex: 100,
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '14px 48px',
        background: 'rgba(3,11,20,0.85)',
        backdropFilter: 'blur(20px)',
        borderBottom: '1px solid rgba(255,255,255,0.06)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{
            width: 34, height: 34, borderRadius: 8,
            background: 'linear-gradient(135deg,#7C3AED,#06B6D4)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: 17, flexShrink: 0,
          }}>⚡</div>
          <span style={{ fontWeight: 800, fontSize: 18, letterSpacing: -0.5 }}>Plotcode</span>
          <span style={{
            fontSize: 10, fontWeight: 600, letterSpacing: 2,
            color: '#7C3AED', border: '1px solid rgba(124,58,237,0.4)',
            padding: '2px 8px', borderRadius: 99, textTransform: 'uppercase',
          }}>Beta</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <button onClick={onGetStarted} style={{
            padding: '8px 20px', borderRadius: 8, fontSize: 13, fontWeight: 600,
            background: 'none', border: '1px solid rgba(255,255,255,0.12)',
            color: 'rgba(255,255,255,0.7)', cursor: 'pointer',
            transition: 'all 0.2s',
          }}
            onMouseOver={e => e.target.style.borderColor = 'rgba(124,58,237,0.6)'}
            onMouseOut={e  => e.target.style.borderColor = 'rgba(255,255,255,0.12)'}
          >
            Sign In
          </button>
          <button onClick={onGetStarted} style={{
            padding: '8px 20px', borderRadius: 8, fontSize: 13, fontWeight: 600,
            background: 'linear-gradient(135deg,#7C3AED,#5B21B6)',
            border: 'none', color: '#fff', cursor: 'pointer',
            boxShadow: '0 2px 16px rgba(124,58,237,0.45)',
            transition: 'all 0.2s',
          }}
            onMouseOver={e => e.currentTarget.style.transform = 'translateY(-1px)'}
            onMouseOut={e  => e.currentTarget.style.transform = 'translateY(0)'}
          >
            Get Started →
          </button>
        </div>
      </nav>

      {/* ── Hero ── */}
      <section style={{
        position: 'relative', zIndex: 1,
        maxWidth: 900, margin: '0 auto',
        padding: '100px 24px 80px',
        textAlign: 'center',
      }}>
        {/* Badge */}
        <div style={{
          display: 'inline-flex', alignItems: 'center', gap: 8,
          background: 'rgba(124,58,237,0.12)', border: '1px solid rgba(124,58,237,0.3)',
          borderRadius: 99, padding: '6px 16px', marginBottom: 28,
          fontSize: 12, fontWeight: 600, color: '#9F67FF',
          animation: 'fadeInUp 0.6s ease both',
        }}>
          <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#10B981', boxShadow: '0 0 6px #10B981', display: 'inline-block' }}/>
          AI-Assisted Software Delivery · 14-Stage SDLC Pipeline
        </div>

        {/* Headline */}
        <h1 style={{
          fontSize: 'clamp(36px, 6vw, 72px)',
          fontWeight: 800, lineHeight: 1.08,
          letterSpacing: -2.5, marginBottom: 22,
          animation: 'fadeInUp 0.7s 0.1s ease both',
        }}>
          Ship Features Faster<br/>
          <span style={{
            background: 'linear-gradient(135deg,#7C3AED,#06B6D4,#10B981)',
            WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
          }}>
            With AI at the Wheel
          </span>
        </h1>

        <p style={{
          fontSize: 18, color: 'rgba(255,255,255,0.55)', lineHeight: 1.7,
          maxWidth: 600, margin: '0 auto 40px',
          animation: 'fadeInUp 0.7s 0.2s ease both',
        }}>
          Plotcode orchestrates your entire delivery pipeline — from Telegram feature request
          to production deploy — using specialized AI agents with human approval checkpoints.
        </p>

        <div style={{
          display: 'flex', gap: 12, justifyContent: 'center', flexWrap: 'wrap',
          animation: 'fadeInUp 0.7s 0.3s ease both',
        }}>
          <button onClick={onGetStarted} style={{
            padding: '14px 32px', borderRadius: 10, fontSize: 15, fontWeight: 700,
            background: 'linear-gradient(135deg,#7C3AED,#5B21B6)',
            border: 'none', color: '#fff', cursor: 'pointer',
            boxShadow: '0 4px 24px rgba(124,58,237,0.5)',
            transition: 'all 0.2s', display: 'flex', alignItems: 'center', gap: 8,
          }}
            onMouseOver={e => { e.currentTarget.style.transform='translateY(-2px)'; e.currentTarget.style.boxShadow='0 8px 32px rgba(124,58,237,0.6)'; }}
            onMouseOut={e  => { e.currentTarget.style.transform='translateY(0)';    e.currentTarget.style.boxShadow='0 4px 24px rgba(124,58,237,0.5)'; }}
          >
            🚀 Open Dashboard
          </button>
          <a href="http://localhost:8001/api/docs" target="_blank" rel="noreferrer" style={{
            padding: '14px 32px', borderRadius: 10, fontSize: 15, fontWeight: 700,
            background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.12)',
            color: 'rgba(255,255,255,0.8)', cursor: 'pointer', textDecoration: 'none',
            transition: 'all 0.2s',
          }}
            onMouseOver={e => { e.currentTarget.style.background='rgba(255,255,255,0.1)'; }}
            onMouseOut={e  => { e.currentTarget.style.background='rgba(255,255,255,0.06)'; }}
          >
            📖 API Docs
          </a>
        </div>
      </section>

      {/* ── Pipeline Visualizer ── */}
      <section style={{
        position: 'relative', zIndex: 1,
        maxWidth: 900, margin: '0 auto 100px',
        padding: '0 24px',
      }}>
        <div style={{
          background: 'rgba(8,20,38,0.9)', backdropFilter: 'blur(16px)',
          border: '1px solid rgba(255,255,255,0.07)',
          borderRadius: 20, padding: '32px 28px',
          position: 'relative', overflow: 'hidden',
        }}>
          {/* Top bar dots */}
          <div style={{ display:'flex', gap:6, marginBottom:24 }}>
            {['#EF4444','#F59E0B','#10B981'].map(c => (
              <div key={c} style={{ width:10,height:10,borderRadius:'50%',background:c,opacity:0.7 }}/>
            ))}
            <span style={{ marginLeft:8,fontSize:11,color:'rgba(255,255,255,0.25)',fontFamily:'monospace' }}>
              plotcode-pipeline // live
            </span>
          </div>

          {/* Stage Track */}
          <div style={{ display:'flex', alignItems:'center', gap:0, overflow:'hidden' }}>
            {PIPELINE_STEPS.map((s, i) => (
              <div key={s.label} style={{ flex:1, display:'flex', flexDirection:'column', alignItems:'center', position:'relative' }}>
                {/* Connector line */}
                {i < PIPELINE_STEPS.length - 1 && (
                  <div style={{
                    position:'absolute', left:'50%', top:22,
                    width:'100%', height:2,
                    background: i < activePipe
                      ? 'linear-gradient(90deg,#7C3AED,#06B6D4)'
                      : 'rgba(255,255,255,0.06)',
                    transition:'background 0.4s ease',
                    zIndex:0,
                  }}/>
                )}
                {/* Node */}
                <div style={{
                  width:44, height:44, borderRadius:12,
                  background: i <= activePipe ? s.color : 'rgba(255,255,255,0.05)',
                  display:'flex', alignItems:'center', justifyContent:'center',
                  fontSize:20, zIndex:1, flexShrink:0,
                  boxShadow: i === activePipe ? `0 0 20px ${s.color}60` : 'none',
                  transition:'all 0.4s ease',
                  transform: i === activePipe ? 'scale(1.15)' : 'scale(1)',
                  border: i === activePipe ? `2px solid ${s.color}` : '2px solid transparent',
                }}>
                  {s.icon}
                </div>
                <div style={{
                  fontSize:10, fontWeight:600, marginTop:8,
                  color: i <= activePipe ? '#fff' : 'rgba(255,255,255,0.3)',
                  letterSpacing:0.5, textTransform:'uppercase',
                  transition:'color 0.4s ease',
                }}>
                  {s.label}
                </div>
              </div>
            ))}
          </div>

          {/* Status line */}
          <div style={{ marginTop:20, padding:'10px 16px', background:'rgba(0,0,0,0.3)', borderRadius:8 }}>
            <span style={{ fontFamily:'monospace', fontSize:11, color:'#10B981' }}>▶ </span>
            <span style={{ fontFamily:'monospace', fontSize:11, color:'rgba(255,255,255,0.5)' }}>
              agent/{PIPELINE_STEPS[activePipe]?.label.toLowerCase().replace('/','_')}_agent
            </span>
            <span style={{ fontFamily:'monospace', fontSize:11, color:'rgba(255,255,255,0.3)' }}>
              {' '}· processing REQ-2026-0042
            </span>
          </div>
        </div>
      </section>

      {/* ── Stats ── */}
      <section ref={statsRef} style={{
        position:'relative', zIndex:1,
        maxWidth:800, margin:'0 auto 100px', padding:'0 24px',
      }}>
        <div style={{
          display:'grid', gridTemplateColumns:'repeat(4,1fr)', gap:32,
          background:'rgba(8,20,38,0.8)', backdropFilter:'blur(12px)',
          border:'1px solid rgba(255,255,255,0.07)',
          borderRadius:20, padding:'40px 32px',
        }}>
          {STATS.map(s => (
            <AnimatedStat key={s.label} {...s} animate={statsVisible}/>
          ))}
        </div>
      </section>

      {/* ── Features ── */}
      <section style={{
        position:'relative', zIndex:1,
        maxWidth:1100, margin:'0 auto 100px', padding:'0 24px',
      }}>
        <div style={{ textAlign:'center', marginBottom:56 }}>
          <div style={{ fontSize:11, fontWeight:700, letterSpacing:4, color:'#7C3AED', textTransform:'uppercase', marginBottom:12 }}>
            Capabilities
          </div>
          <h2 style={{ fontSize:'clamp(28px,4vw,44px)', fontWeight:800, letterSpacing:-1.5, marginBottom:14 }}>
            Everything the pipeline needs
          </h2>
          <p style={{ fontSize:16, color:'rgba(255,255,255,0.45)', maxWidth:500, margin:'0 auto' }}>
            Six specialized agents, each an expert at one stage of the software delivery lifecycle.
          </p>
        </div>

        <div style={{ display:'grid', gridTemplateColumns:'repeat(3,1fr)', gap:16 }}>
          {FEATURES.map(f => (
            <div key={f.title}
              style={{
                background:'rgba(10,24,45,0.9)', backdropFilter:'blur(12px)',
                border:'1px solid rgba(255,255,255,0.06)',
                borderRadius:16, padding:'24px 22px',
                transition:'all 0.25s', cursor:'default',
              }}
              onMouseOver={e => {
                e.currentTarget.style.transform='translateY(-3px)';
                e.currentTarget.style.borderColor='rgba(124,58,237,0.25)';
                e.currentTarget.style.boxShadow='0 8px 32px rgba(0,0,0,0.4)';
              }}
              onMouseOut={e => {
                e.currentTarget.style.transform='translateY(0)';
                e.currentTarget.style.borderColor='rgba(255,255,255,0.06)';
                e.currentTarget.style.boxShadow='none';
              }}
            >
              <div style={{
                width:44, height:44, borderRadius:10,
                background:f.grad, display:'flex', alignItems:'center',
                justifyContent:'center', fontSize:20, marginBottom:14,
              }}>
                {f.icon}
              </div>
              <div style={{ fontWeight:700, fontSize:15, marginBottom:8 }}>{f.title}</div>
              <div style={{ fontSize:13, color:'rgba(255,255,255,0.45)', lineHeight:1.7 }}>{f.desc}</div>
            </div>
          ))}
        </div>
      </section>

      {/* ── CTA Banner ── */}
      <section style={{
        position:'relative', zIndex:1,
        maxWidth:900, margin:'0 auto 80px', padding:'0 24px',
      }}>
        <div style={{
          background:'linear-gradient(135deg,rgba(124,58,237,0.25),rgba(6,182,212,0.15))',
          border:'1px solid rgba(124,58,237,0.3)',
          borderRadius:24, padding:'56px 48px',
          textAlign:'center', position:'relative', overflow:'hidden',
        }}>
          <div style={{
            position:'absolute', top:-40, left:-40, width:200, height:200,
            borderRadius:'50%', background:'rgba(124,58,237,0.15)', filter:'blur(40px)',
          }}/>
          <div style={{
            position:'absolute', bottom:-40, right:-40, width:200, height:200,
            borderRadius:'50%', background:'rgba(6,182,212,0.1)', filter:'blur(40px)',
          }}/>
          <div style={{ position:'relative' }}>
            <h2 style={{ fontSize:'clamp(24px,4vw,38px)', fontWeight:800, letterSpacing:-1, marginBottom:14 }}>
              Ready to automate delivery?
            </h2>
            <p style={{ fontSize:16, color:'rgba(255,255,255,0.5)', marginBottom:32 }}>
              Sign in as admin and start submitting feature requests.
            </p>
            <button onClick={onGetStarted} style={{
              padding:'14px 40px', borderRadius:10, fontSize:16, fontWeight:700,
              background:'linear-gradient(135deg,#7C3AED,#5B21B6)',
              border:'none', color:'#fff', cursor:'pointer',
              boxShadow:'0 4px 24px rgba(124,58,237,0.5)',
              transition:'all 0.2s',
            }}
              onMouseOver={e => { e.currentTarget.style.transform='translateY(-2px)'; }}
              onMouseOut={e  => { e.currentTarget.style.transform='translateY(0)'; }}
            >
              Enter Dashboard →
            </button>
          </div>
        </div>
      </section>

      {/* ── Footer ── */}
      <footer style={{
        position:'relative', zIndex:1,
        borderTop:'1px solid rgba(255,255,255,0.06)',
        padding:'24px 48px',
        display:'flex', alignItems:'center', justifyContent:'space-between',
      }}>
        <div style={{ display:'flex', alignItems:'center', gap:8 }}>
          <div style={{
            width:24, height:24, borderRadius:5,
            background:'linear-gradient(135deg,#7C3AED,#06B6D4)',
            display:'flex', alignItems:'center', justifyContent:'center', fontSize:12,
          }}>⚡</div>
          <span style={{ fontSize:13, fontWeight:700 }}>Plotcode</span>
          <span style={{ fontSize:12, color:'rgba(255,255,255,0.25)' }}>· AI Delivery Automation v3.0</span>
        </div>
        <div style={{ fontSize:12, color:'rgba(255,255,255,0.25)' }}>
          MongoDB Atlas · OpenRouter · FastAPI · React
        </div>
      </footer>

      <style>{`
        @keyframes fadeInUp {
          from { opacity:0; transform:translateY(16px); }
          to   { opacity:1; transform:translateY(0); }
        }
        @media(max-width:768px) {
          nav { padding: 12px 20px !important; }
          section { padding-left: 16px !important; padding-right: 16px !important; }
          div[style*="repeat(3,1fr)"] { grid-template-columns: 1fr !important; }
          div[style*="repeat(4,1fr)"] { grid-template-columns: repeat(2,1fr) !important; }
        }
      `}</style>
    </div>
  );
}
