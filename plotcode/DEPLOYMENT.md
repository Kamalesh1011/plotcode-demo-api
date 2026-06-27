# Plotcode — Deployment Guide (All on Vercel, No Docker)

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    ALL-ON-VERCEL DEPLOYMENT                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ONE VERCEL PROJECT                                                  │
│  ├── Frontend (React + Vite)                                        │
│  │   → Built from frontend/ directory                               │
│  │   → Served as static files via CDN                               │
│  │   → URL: https://plotcode.vercel.app                             │
│  │                                                                  │
│  ├── Backend (FastAPI Python Serverless)                            │
│  │   → Entry point: api/index.py                                    │
│  │   → Routes /api/* → Python serverless function                   │
│  │   → 1024MB RAM, 60s timeout                                      │
│  │                                                                  │
│  └── MongoDB Atlas (External)                                       │
│      → Connected via MONGODB_URI env var                            │
│      → Free M0 tier (512MB)                                         │
│                                                                      │
│  Vercel Limitations (handled):                                      │
│  ├── No WebSocket → Frontend uses polling fallback                  │
│  ├── Read-only filesystem → File uploads stored in MongoDB          │
│  ├── 60s timeout → Agent execution may need optimization            │
│  └── Cold starts → First request ~2s slower                         │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

## Step-by-Step Deployment

### Step 1: Push to GitHub
```bash
cd D:/dubai-project1/plotcode
git init
git add .
git commit -m "Initial commit — Plotcode platform"
git remote add origin https://github.com/YOUR_USERNAME/plotcode.git
git push -u origin main
```

### Step 2: Create Vercel Project
1. Go to https://vercel.com → **Add New** → **Project**
2. Import your GitHub repo (`plotcode`)
3. Vercel will auto-detect the config from `vercel.json`

### Step 3: Configure Environment Variables
In Vercel project settings → **Environment Variables**, add ALL of these:

```env
# Database (Required)
MONGODB_URI=mongodb+srv://your_connection_string
MONGODB_DB=plotcode_db

# Auth (Required)
JWT_SECRET=generate_with_python_secrets_token_hex_32
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your_secure_password
ADMIN_EMAIL=admin@plotcode.com

# LLM (Required)
OPENROUTER_API_KEY=your_openrouter_key
DEFAULT_LLM_MODEL=openai/gpt-4o
CHAT_LLM_MODEL=openai/gpt-4o-mini

# GitHub API (Required)
GITHUB_TOKEN=your_github_personal_access_token
GITHUB_ORG=your_org_name
GITHUB_DEFAULT_REPO=your_default_repo

# GitHub OAuth (Required)
GITHUB_CLIENT_ID=your_github_oauth_client_id
GITHUB_CLIENT_SECRET=your_github_oauth_secret
GITHUB_OAUTH_REDIRECT_URI=https://plotcode.vercel.app/auth/github/callback

# Google OAuth (Optional)
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_OAUTH_REDIRECT_URI=https://plotcode.vercel.app/auth/google/callback

# Telegram (Optional)
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_ADMIN_CHAT_ID=your_chat_id
```

### Step 4: Deploy
Click **Deploy**. Vercel will:
1. Run `cd frontend && npm install && npm run build` (builds React)
2. Install Python dependencies from `requirements.txt`
3. Deploy `api/index.py` as a serverless function
4. Serve frontend as static files
5. Route `/api/*` to the Python backend

Your app will be live at: `https://plotcode.vercel.app`

### Step 5: Update OAuth Callback URLs

**GitHub OAuth App** (https://github.com/settings/developers):
- Homepage URL: `https://plotcode.vercel.app`
- Authorization callback URL: `https://plotcode.vercel.app/auth/github/callback`

**Google OAuth** (https://console.cloud.google.com → Credentials):
- Authorized JavaScript origin: `https://plotcode.vercel.app`
- Authorized redirect URI: `https://plotcode.vercel.app/auth/google/callback`

### Step 6: MongoDB Atlas IP Whitelist
1. Go to https://cloud.mongodb.com → Network Access
2. Add `0.0.0.0/0` (allow access from anywhere — Vercel uses dynamic IPs)

---

## File Structure

```
plotcode/
├── api/
│   └── index.py              ← Vercel Python serverless entry point
├── agents/                   ← Backend code (FastAPI app)
│   ├── api.py                ← Main FastAPI application
│   ├── shared/               ← Shared utilities (auth, state, git, llm)
│   ├── middleware/            ← Auth middleware
│   ├── prompts/              ← Agent prompt templates
│   └── requirements.txt      ← Backend-specific deps (for local dev)
├── frontend/                 ← Frontend code (React + Vite)
│   ├── src/
│   ├── package.json
│   └── vercel.json           ← Frontend-only Vercel config (not used in monorepo)
├── requirements.txt          ← Root Python deps (Vercel reads this)
├── vercel.json               ← Root Vercel config (frontend + backend)
└── .env.example              ← Environment variable template
```

---

## How It Works on Vercel

### Request Routing
```
Browser request
    │
    ├── /api/requests      → Python serverless function (api/index.py)
    ├── /auth/login        → Python serverless function
    ├── /chat              → Python serverless function
    ├── /upload            → Python serverless function
    ├── /assets/index.js   → Static file (frontend/dist/assets/)
    └── /overview          → index.html (SPA routing)
```

### Real-time Events (WebSocket Fallback)
Vercel doesn't support WebSocket connections. The frontend automatically falls back to **polling**:
- Tries WebSocket first
- If it fails (Vercel), switches to polling every 5 seconds
- Fetches recent request updates from `/api/requests`
- Works seamlessly — user sees "Live" status either way

### File Uploads
Vercel's filesystem is read-only (except `/tmp`). File uploads are stored in **MongoDB**:
- Small text files: stored as UTF-8 strings
- Binary files: stored as base64-encoded strings
- On VPS (if you switch later): falls back to disk storage automatically

---

## Local Development

```bash
# Terminal 1 — Backend
cd plotcode/agents
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp ../.env.example .env  # Edit with your values
python -m uvicorn api:app --host 0.0.0.0 --port 8001 --reload

# Terminal 2 — Frontend
cd plotcode/frontend
npm install
npm run dev
# → http://localhost:5173
```

---

## Vercel Limitations & Workarounds

| Limitation | Impact | Workaround |
|-----------|--------|------------|
| No WebSocket | No real-time push | Frontend polls API every 5s |
| Read-only filesystem | Can't save files to disk | Files stored in MongoDB |
| 60s function timeout | Long agent tasks may timeout | Agents run in background; results polled |
| Cold starts (~2s) | First request slower | Vercel keeps functions warm for ~5min |
| No SSH server | Can't host git repos | Use GitHub as git backend |
| No background processes | Telegram bot can't run | Run bot on a separate VPS or service |

---

## Custom Domain (Optional)
1. Vercel → Settings → Domains
2. Add your domain (e.g. `plotcode.yourcompany.com`)
3. Add DNS records as instructed
4. Update OAuth callback URLs to use your domain

---

## Troubleshooting

### "Module not found" error in Python function
- Ensure all dependencies are in root `requirements.txt` (not just `agents/requirements.txt`)
- Vercel reads `requirements.txt` from the project root

### Frontend can't reach backend
- Check that `vercel.json` rewrites are correct
- The frontend uses `/api` as the base URL (same origin on Vercel)
- No `VITE_API_URL` env var needed when deployed on Vercel

### OAuth redirect fails
- Callback URL must be `https://yourdomain.vercel.app/auth/github/callback`
- Must match EXACTLY what's in GitHub/Google OAuth settings

### MongoDB connection fails
- Add `0.0.0.0/0` to MongoDB Atlas IP whitelist
- Check `MONGODB_URI` env var is set in Vercel

### Function timeout (502 error)
- Vercel free plan: 10s timeout
- Vercel Pro plan: 60s timeout
- Agent execution may exceed this — consider running agents on a separate service

### File upload fails
- Ensure file is < 10MB
- Vercel has a 4.5MB request body limit on free plan
- For larger files, use Vercel Pro or a separate upload service
