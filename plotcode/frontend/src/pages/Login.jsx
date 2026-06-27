import { useState } from 'react';
import { getHealth, login, register, getGitHubOAuthUrl, getGoogleOAuthUrl } from '../api';
import { toast } from '../components/Toast';

export default function Login({ onLogin, onBack }) {
  const [mode, setMode] = useState('login'); // 'login' | 'register'
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [email, setEmail] = useState('');
  const [name, setName] = useState('');
  const [showPass, setShowPass] = useState(false);
  const [loading, setLoading] = useState(false);
  const [shake, setShake] = useState(false);
  const [focused, setFocused] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    // Verify backend is reachable
    const health = await getHealth();

    if (!health) {
      toast('error', '❌ Backend Unreachable', 'Make sure the API is running on port 8001.');
      setLoading(false);
      return;
    }

    if (mode === 'register') {
      // Register new account
      const result = await register({ username, password, email, name });
      if (result && result.user) {
        toast('success', '✅ Account Created!', `Welcome ${result.user.name || result.user.username}!`);
        setTimeout(() => onLogin(result.user), 600);
      } else {
        setShake(true);
        toast('error', '❌ Registration Failed', 'Username may already exist.');
        setTimeout(() => setShake(false), 600);
      }
    } else {
      // Login with existing account
      const result = await login(username, password);
      if (result && result.user) {
        toast('success', '✅ Welcome back!', `Loading your dashboard…`);
        setTimeout(() => onLogin(result.user), 600);
      } else {
        setShake(true);
        toast('error', '❌ Invalid Credentials', 'Check your username and password.');
        setTimeout(() => setShake(false), 600);
      }
    }
    setLoading(false);
  };

  const handleGitHubLogin = async () => {
    const data = await getGitHubOAuthUrl();
    if (data?.url) {
      window.location.href = data.url;
    } else {
      toast('error', '❌ GitHub OAuth Not Configured', 'Set GITHUB_CLIENT_ID in backend .env');
    }
  };

  const handleGoogleLogin = async () => {
    const data = await getGoogleOAuthUrl();
    if (data?.url) {
      window.location.href = data.url;
    } else {
      toast('error', '❌ Google OAuth Not Configured', 'Set GOOGLE_CLIENT_ID in backend .env');
    }
  };

  return (
    <div style={{
      minHeight: '100vh', display: 'flex', flexDirection: 'column',
      background: '#030B14', overflow: 'hidden', position: 'relative',
    }}>

      {/* Ambient glows */}
      <div style={{
        position: 'fixed', inset: 0, pointerEvents: 'none',
        background: `
          radial-gradient(ellipse 70% 50% at 15% 20%,  rgba(124,58,237,0.2) 0%, transparent 60%),
          radial-gradient(ellipse 50% 40% at 85% 80%, rgba(6,182,212,0.14) 0%, transparent 55%)
        `,
      }} />

      {/* Grid pattern */}
      <div style={{
        position: 'fixed', inset: 0, pointerEvents: 'none', opacity: 0.03,
        backgroundImage: `
          linear-gradient(rgba(255,255,255,0.5) 1px, transparent 1px),
          linear-gradient(90deg, rgba(255,255,255,0.5) 1px, transparent 1px)
        `,
        backgroundSize: '40px 40px',
      }} />

      {/* Back button */}
      <div style={{ position: 'absolute', top: 20, left: 24, zIndex: 10 }}>
        <button onClick={onBack} style={{
          display: 'flex', alignItems: 'center', gap: 6,
          background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.1)',
          borderRadius: 8, padding: '7px 14px', color: 'rgba(255,255,255,0.6)',
          fontSize: 13, fontWeight: 500, cursor: 'pointer',
          transition: 'all 0.2s', fontFamily: 'inherit',
        }}
          onMouseOver={e => e.currentTarget.style.background = 'rgba(255,255,255,0.1)'}
          onMouseOut={e => e.currentTarget.style.background = 'rgba(255,255,255,0.06)'}
        >
          ← Back
        </button>
      </div>

      {/* Main layout — split */}
      <div style={{
        flex: 1, display: 'grid',
        gridTemplateColumns: '1fr 1fr',
        minHeight: '100vh',
        position: 'relative', zIndex: 1,
      }}>

        {/* Left — Branding panel */}
        <div style={{
          display: 'flex', flexDirection: 'column',
          justifyContent: 'center', padding: '80px 60px',
          borderRight: '1px solid rgba(255,255,255,0.05)',
        }}>
          {/* Logo */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 48 }}>
            <div style={{
              width: 48, height: 48, borderRadius: 12,
              background: 'linear-gradient(135deg,#7C3AED,#06B6D4)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: 24, boxShadow: '0 8px 24px rgba(124,58,237,0.4)',
            }}>⚡</div>
            <div>
              <div style={{ fontWeight: 800, fontSize: 22, letterSpacing: -0.5 }}>Plotcode</div>
              <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.4)', letterSpacing: 2, textTransform: 'uppercase' }}>
                AI Delivery Platform
              </div>
            </div>
          </div>

          <h1 style={{
            fontSize: 40, fontWeight: 800, lineHeight: 1.15,
            letterSpacing: -1.5, marginBottom: 16,
          }}>
            Welcome back<br />
            <span style={{
              background: 'linear-gradient(135deg,#7C3AED,#06B6D4)',
              WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
            }}>
              to the control centre
            </span>
          </h1>

          <p style={{
            fontSize: 15, color: 'rgba(255,255,255,0.45)', lineHeight: 1.75,
            marginBottom: 48, maxWidth: 380,
          }}>
            Manage your AI-powered delivery pipeline, review feature requests,
            monitor agents, and ship faster — all from one dashboard.
          </p>

          {/* Feature bullets */}
          {[
            { icon: '🧠', text: '6 AI Agents — analysis, coding, CI, PR, deploy, monitoring' },
            { icon: '👥', text: 'Human-in-the-loop at every critical decision point' },
            { icon: '📡', text: 'Real-time WebSocket dashboard with full audit trail' },
          ].map(f => (
            <div key={f.text} style={{
              display: 'flex', alignItems: 'flex-start', gap: 12,
              marginBottom: 14,
            }}>
              <div style={{
                width: 32, height: 32, borderRadius: 8, flexShrink: 0,
                background: 'rgba(124,58,237,0.15)', border: '1px solid rgba(124,58,237,0.2)',
                display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 15,
              }}>{f.icon}</div>
              <div style={{ fontSize: 13, color: 'rgba(255,255,255,0.5)', lineHeight: 1.6, paddingTop: 6 }}>
                {f.text}
              </div>
            </div>
          ))}

          {/* API status badge */}
          <div style={{
            display: 'inline-flex', alignItems: 'center', gap: 8, marginTop: 32,
            background: 'rgba(16,185,129,0.08)', border: '1px solid rgba(16,185,129,0.2)',
            borderRadius: 99, padding: '6px 14px', width: 'fit-content',
          }}>
            <span style={{ width: 7, height: 7, borderRadius: '50%', background: '#10B981', boxShadow: '0 0 6px #10B981', display: 'inline-block', animation: 'blink2 2s infinite' }} />
            <span style={{ fontSize: 12, color: '#10B981', fontWeight: 600 }}>API Running · localhost:8001</span>
          </div>
        </div>

        {/* Right — Login form */}
        <div style={{
          display: 'flex', flexDirection: 'column',
          justifyContent: 'center', alignItems: 'center',
          padding: '80px 60px',
        }}>
          <div style={{
            width: '100%', maxWidth: 400,
            animation: shake ? 'shake 0.5s ease' : 'none',
          }}>
            <div style={{ marginBottom: 32 }}>
              <div style={{ fontSize: 24, fontWeight: 800, marginBottom: 6 }}>
                {mode === 'login' ? 'Sign in' : 'Create Account'}
              </div>
              <div style={{ fontSize: 13, color: 'rgba(255,255,255,0.4)' }}>
                {mode === 'login' ? 'Admin access · All permissions' : 'Register to access the dashboard'}
              </div>
            </div>

            <form onSubmit={handleSubmit}>

              {/* Name (register only) */}
              {mode === 'register' && (
                <div style={{ marginBottom: 16 }}>
                  <label style={{
                    display: 'block', fontSize: 12, fontWeight: 600,
                    color: 'rgba(255,255,255,0.5)', marginBottom: 7, letterSpacing: 0.3,
                  }}>
                    FULL NAME
                  </label>
                  <div style={{
                    display: 'flex', alignItems: 'center', gap: 10,
                    background: 'rgba(14,28,52,0.8)',
                    border: `1px solid ${focused === 'name' ? 'rgba(124,58,237,0.6)' : 'rgba(255,255,255,0.08)'}`,
                    borderRadius: 10, padding: '12px 14px',
                    transition: 'all 0.2s',
                    boxShadow: focused === 'name' ? '0 0 0 3px rgba(124,58,237,0.15)' : 'none',
                  }}>
                    <span style={{ fontSize: 16, opacity: 0.5 }}>😊</span>
                    <input
                      type="text"
                      value={name}
                      onChange={e => setName(e.target.value)}
                      onFocus={() => setFocused('name')}
                      onBlur={() => setFocused(null)}
                      placeholder="John Doe"
                      required
                      style={{
                        flex: 1, background: 'none', border: 'none', outline: 'none',
                        color: '#F0F6FF', fontSize: 14, fontFamily: 'inherit',
                      }}
                    />
                  </div>
                </div>
              )}

              {/* Email (register only) */}
              {mode === 'register' && (
                <div style={{ marginBottom: 16 }}>
                  <label style={{
                    display: 'block', fontSize: 12, fontWeight: 600,
                    color: 'rgba(255,255,255,0.5)', marginBottom: 7, letterSpacing: 0.3,
                  }}>
                    EMAIL
                  </label>
                  <div style={{
                    display: 'flex', alignItems: 'center', gap: 10,
                    background: 'rgba(14,28,52,0.8)',
                    border: `1px solid ${focused === 'email' ? 'rgba(124,58,237,0.6)' : 'rgba(255,255,255,0.08)'}`,
                    borderRadius: 10, padding: '12px 14px',
                    transition: 'all 0.2s',
                    boxShadow: focused === 'email' ? '0 0 0 3px rgba(124,58,237,0.15)' : 'none',
                  }}>
                    <span style={{ fontSize: 16, opacity: 0.5 }}>✉️</span>
                    <input
                      type="email"
                      value={email}
                      onChange={e => setEmail(e.target.value)}
                      onFocus={() => setFocused('email')}
                      onBlur={() => setFocused(null)}
                      placeholder="you@example.com"
                      required
                      style={{
                        flex: 1, background: 'none', border: 'none', outline: 'none',
                        color: '#F0F6FF', fontSize: 14, fontFamily: 'inherit',
                      }}
                    />
                  </div>
                </div>
              )}

              {/* Username */}
              <div style={{ marginBottom: 16 }}>
                <label style={{
                  display: 'block', fontSize: 12, fontWeight: 600,
                  color: 'rgba(255,255,255,0.5)', marginBottom: 7, letterSpacing: 0.3,
                }}>
                  USERNAME
                </label>
                <div style={{
                  display: 'flex', alignItems: 'center', gap: 10,
                  background: 'rgba(14,28,52,0.8)',
                  border: `1px solid ${focused === 'user' ? 'rgba(124,58,237,0.6)' : 'rgba(255,255,255,0.08)'}`,
                  borderRadius: 10, padding: '12px 14px',
                  transition: 'all 0.2s',
                  boxShadow: focused === 'user' ? '0 0 0 3px rgba(124,58,237,0.15)' : 'none',
                }}>
                  <span style={{ fontSize: 16, opacity: 0.5 }}>👤</span>
                  <input
                    type="text"
                    value={username}
                    onChange={e => setUsername(e.target.value)}
                    onFocus={() => setFocused('user')}
                    onBlur={() => setFocused(null)}
                    placeholder="admin"
                    autoComplete="username"
                    required
                    style={{
                      flex: 1, background: 'none', border: 'none', outline: 'none',
                      color: '#F0F6FF', fontSize: 14, fontFamily: 'inherit',
                    }}
                  />
                </div>
              </div>

              {/* Password */}
              <div style={{ marginBottom: 24 }}>
                <label style={{
                  display: 'block', fontSize: 12, fontWeight: 600,
                  color: 'rgba(255,255,255,0.5)', marginBottom: 7, letterSpacing: 0.3,
                }}>
                  PASSWORD
                </label>
                <div style={{
                  display: 'flex', alignItems: 'center', gap: 10,
                  background: 'rgba(14,28,52,0.8)',
                  border: `1px solid ${focused === 'pass' ? 'rgba(124,58,237,0.6)' : 'rgba(255,255,255,0.08)'}`,
                  borderRadius: 10, padding: '12px 14px',
                  transition: 'all 0.2s',
                  boxShadow: focused === 'pass' ? '0 0 0 3px rgba(124,58,237,0.15)' : 'none',
                }}>
                  <span style={{ fontSize: 16, opacity: 0.5 }}>🔑</span>
                  <input
                    type={showPass ? 'text' : 'password'}
                    value={password}
                    onChange={e => setPassword(e.target.value)}
                    onFocus={() => setFocused('pass')}
                    onBlur={() => setFocused(null)}
                    placeholder="••••••••••••"
                    autoComplete="current-password"
                    required
                    style={{
                      flex: 1, background: 'none', border: 'none', outline: 'none',
                      color: '#F0F6FF', fontSize: 14, fontFamily: 'inherit',
                    }}
                  />
                  <button type="button" onClick={() => setShowPass(s => !s)} style={{
                    background: 'none', border: 'none', cursor: 'pointer',
                    color: 'rgba(255,255,255,0.4)', fontSize: 14, padding: 0,
                    transition: 'color 0.2s',
                  }}>
                    {showPass ? '🙈' : '👁️'}
                  </button>
                </div>

              </div>

              {/* Submit */}
              <button type="submit" disabled={loading} style={{
                width: '100%', padding: '14px', borderRadius: 10,
                fontSize: 15, fontWeight: 700, border: 'none', cursor: loading ? 'wait' : 'pointer',
                background: loading
                  ? 'rgba(124,58,237,0.5)'
                  : 'linear-gradient(135deg,#7C3AED,#5B21B6)',
                color: '#fff',
                boxShadow: loading ? 'none' : '0 4px 20px rgba(124,58,237,0.45)',
                transition: 'all 0.25s', fontFamily: 'inherit',
                display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
              }}
                onMouseOver={e => { if (!loading) e.currentTarget.style.transform = 'translateY(-1px)'; }}
                onMouseOut={e => { e.currentTarget.style.transform = 'translateY(0)'; }}
              >
                {loading ? (
                  <>
                    <span style={{ display: 'inline-block', width: 14, height: 14, border: '2px solid rgba(255,255,255,0.4)', borderTopColor: '#fff', borderRadius: '50%', animation: 'spin 0.7s linear infinite' }} />
                    {mode === 'login' ? 'Verifying…' : 'Creating…'}
                  </>
                ) : (
                  mode === 'login' ? '⚡ Enter Dashboard' : '✨ Create Account'
                )}
              </button>

              {/* Login / Register toggle */}
              <div style={{ textAlign: 'center', marginTop: 16, fontSize: 12, color: 'rgba(255,255,255,0.4)' }}>
                {mode === 'login' ? (
                  <>Don't have an account?{' '}
                    <button type="button" onClick={() => { setMode('register'); setPassword(''); }}
                      style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#9F67FF', fontWeight: 600, fontFamily: 'inherit', fontSize: 12 }}>
                      Register here
                    </button>
                  </>
                ) : (
                  <>Already have an account?{' '}
                    <button type="button" onClick={() => setMode('login')}
                      style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#9F67FF', fontWeight: 600, fontFamily: 'inherit', fontSize: 12 }}>
                      Sign in
                    </button>
                  </>
                )}
              </div>

              {/* Divider */}
              <div style={{ display: 'flex', alignItems: 'center', gap: 12, margin: '20px 0' }}>
                <div style={{ flex: 1, height: 1, background: 'rgba(255,255,255,0.08)' }} />
                <span style={{ fontSize: 11, color: 'rgba(255,255,255,0.3)' }}>or</span>
                <div style={{ flex: 1, height: 1, background: 'rgba(255,255,255,0.08)' }} />
              </div>

              {/* GitHub OAuth */}
              <button type="button" onClick={handleGitHubLogin} style={{
                width: '100%', padding: '12px', borderRadius: 10,
                fontSize: 14, fontWeight: 600, cursor: 'pointer',
                background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.12)',
                color: '#F0F6FF', transition: 'all 0.2s', fontFamily: 'inherit',
                display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 10,
                marginBottom: 10,
              }}
                onMouseOver={e => e.currentTarget.style.background = 'rgba(255,255,255,0.1)'}
                onMouseOut={e => e.currentTarget.style.background = 'rgba(255,255,255,0.06)'}
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 .5C5.37.5 0 5.78 0 12.29c0 5.21 3.44 9.63 8.21 11.19.6.11.82-.26.82-.58 0-.29-.01-1.04-.02-2.05-3.34.72-4.04-1.59-4.04-1.59-.55-1.38-1.34-1.75-1.34-1.75-1.09-.74.08-.73.08-.73 1.21.09 1.84 1.23 1.84 1.23 1.07 1.8 2.81 1.28 3.5.98.11-.77.42-1.28.76-1.58-2.67-.3-5.47-1.31-5.47-5.84 0-1.29.47-2.34 1.23-3.17-.12-.3-.53-1.52.12-3.16 0 0 1-.32 3.3 1.21.96-.26 1.98-.39 3-.4 1.02.01 2.04.14 3 .4 2.28-1.53 3.28-1.21 3.28-1.21.65 1.64.24 2.86.12 3.16.77.83 1.23 1.88 1.23 3.17 0 4.54-2.81 5.53-5.49 5.83.43.36.81 1.08.81 2.18 0 1.58-.01 2.85-.01 3.24 0 .32.22.7.83.58C20.57 21.91 24 17.5 24 12.29 24 5.78 18.63.5 12 .5z" />
                </svg>
                Continue with GitHub
              </button>

              {/* Google OAuth */}
              <button type="button" onClick={handleGoogleLogin} style={{
                width: '100%', padding: '12px', borderRadius: 10,
                fontSize: 14, fontWeight: 600, cursor: 'pointer',
                background: '#fff', border: '1px solid #dadce0',
                color: '#3c4043', transition: 'all 0.2s', fontFamily: 'inherit',
                display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 10,
              }}
                onMouseOver={e => e.currentTarget.style.boxShadow = '0 1px 3px rgba(60,64,67,0.3)'}
                onMouseOut={e => e.currentTarget.style.boxShadow = 'none'}
              >
                <svg width="18" height="18" viewBox="0 0 24 24">
                  <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                  <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                  <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
                  <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
                </svg>
                Continue with Google
              </button>
            </form>

            {/* Divider info */}
            <div style={{
              marginTop: 28, padding: 16,
              background: 'rgba(124,58,237,0.07)',
              border: '1px solid rgba(124,58,237,0.15)',
              borderRadius: 10,
            }}>
              <div style={{ fontSize: 11, fontWeight: 600, color: 'rgba(124,58,237,0.8)', marginBottom: 6 }}>
                🔐 ADMIN ROLE PERMISSIONS
              </div>
              <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.35)', lineHeight: 1.7 }}>
                Full pipeline access · User management · Production deploys · Audit export · All 14 SDLC stages
              </div>
            </div>
          </div>
        </div>
      </div>

      <style>{`
        @keyframes blink2 {
          0%,100% { opacity:1; transform:scale(1); }
          50%      { opacity:0.4; transform:scale(1.3); }
        }
        @keyframes shake {
          0%,100% { transform:translateX(0); }
          15%      { transform:translateX(-8px); }
          30%      { transform:translateX(8px); }
          45%      { transform:translateX(-6px); }
          60%      { transform:translateX(6px); }
          75%      { transform:translateX(-3px); }
          90%      { transform:translateX(3px); }
        }
        @keyframes spin {
          to { transform:rotate(360deg); }
        }
        @media(max-width:768px) {
          div[style*="repeat(2,1fr)"] { grid-template-columns:1fr !important; }
        }
      `}</style>
    </div>
  );
}
