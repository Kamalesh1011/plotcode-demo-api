#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
# Plotcode Git Server — Direct VPS Setup (No Docker)
# 
# Installs directly on the VPS:
#   - Git (bare repos)
#   - OpenSSH (git push/clone via SSH)
#   - Nginx (git smart HTTP)
#   - Python + FastAPI (backend API)
#   - Node.js (frontend build)
#   - PM2 (process manager)
#
# Run on: Ubuntu 22.04 / 24.04 VPS (DigitalOcean, EC2, Linode)
# Usage:  bash vps-setup.sh
# ═══════════════════════════════════════════════════════════════════════════════

set -e

echo "╔══════════════════════════════════════════════════╗"
echo "║   Plotcode — Direct VPS Setup (No Docker)       ║"
echo "╚══════════════════════════════════════════════════╝"

VPS_IP=$(hostname -I | awk '{print $1}')

# ─── 1. System Update ─────────────────────────────────────────────────────────
echo "📦 Updating system..."
apt-get update -qq && apt-get upgrade -y -qq

# ─── 2. Install Dependencies ──────────────────────────────────────────────────
echo "🔧 Installing Git, SSH, Nginx, Python, Node..."
apt-get install -y -qq \
    git openssh-server nginx fcgiwrap \
    python3 python3-pip python3-venv \
    curl ufw build-essential

# Node.js 20 LTS
if ! command -v node &> /dev/null || [ "$(node -v | cut -d. -f1 | tr -d v)" -lt 18 ]; then
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
    apt-get install -y -qq nodejs
fi

# PM2 (process manager)
npm install -g pm2

# ─── 3. Create Git User ───────────────────────────────────────────────────────
echo "👤 Creating 'git' user..."
if ! id -u git &> /dev/null; then
    useradd -m -s /usr/bin/git-shell git
    mkdir -p /home/git/.ssh
    touch /home/git/.ssh/authorized_keys
    chmod 700 /home/git/.ssh
    chmod 600 /home/git/.ssh/authorized_keys
    chown -R git:git /home/git/.ssh
fi

# ─── 4. Create Repository Directory ───────────────────────────────────────────
echo "📁 Creating repository directory..."
mkdir -p /repos
chown -R git:git /repos

# ─── 5. SSH Configuration ─────────────────────────────────────────────────────
echo "🔐 Configuring SSH for git..."
SSHD_CONFIG="/etc/ssh/sshd_config"
if ! grep -q "Match User git" "$SSHD_CONFIG"; then
    cat >> "$SSHD_CONFIG" << 'EOF'

# ─── Plotcode Git Server ──────────────────────────────────
Match User git
    ForceCommand git-shell
    PasswordAuthentication no
    X11Forwarding no
    AllowTcpForwarding no
    PermitTunnel no
EOF
    systemctl restart sshd
fi

# ─── 6. Firewall ──────────────────────────────────────────────────────────────
echo "🛡️  Configuring firewall..."
ufw allow 22/tcp     # SSH
ufw allow 80/tcp     # HTTP
ufw allow 443/tcp    # HTTPS
ufw allow 8001/tcp   # Backend API
ufw --force enable

# ─── 7. Git Smart HTTP (Nginx + fcgiwrap) ─────────────────────────────────────
echo "🌐 Configuring Nginx for git smart HTTP..."
cat > /etc/nginx/sites-available/git << 'NGINX'
server {
    listen 80;
    server_name _;

    # Git smart HTTP — clone/push via HTTPS
    location ~ ^/git(/.*)$ {
        auth_basic "Git Access";
        auth_basic_user_file /etc/nginx/.htpasswd;

        client_max_body_size 0;

        include fastcgi_params;
        fastcgi_param SCRIPT_FILENAME /usr/lib/git-core/git-http-backend;
        fastcgi_param GIT_HTTP_EXPORT_ALL "";
        fastcgi_param GIT_PROJECT_ROOT /repos;
        fastcgi_param PATH_INFO $1;
        fastcgi_pass unix:/var/run/fcgiwrap.socket;
    }

    # Frontend (React build)
    location / {
        root /var/www/plotcode;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # API proxy
    location /api/ {
        proxy_pass http://127.0.0.1:8001/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # WebSocket proxy
    location /ws/ {
        proxy_pass http://127.0.0.1:8001/ws/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Health check
    location /health {
        return 200 "ok";
        add_header Content-Type text/plain;
    }
}
NGINX

ln -sf /etc/nginx/sites-available/git /etc/nginx/sites-enabled/git
rm -f /etc/nginx/sites-enabled/default
systemctl restart nginx
systemctl enable fcgiwrap

# ─── 8. Create First Repository ───────────────────────────────────────────────
echo "📦 Creating sample repository..."
if [ ! -d /repos/plotcode-demo.git ]; then
    git init --bare /repos/plotcode-demo.git
    chown -R git:git /repos/plotcode-demo.git
    echo "✅ Created: /repos/plotcode-demo.git"
fi

# ─── 9. Clone Plotcode Project ────────────────────────────────────────────────
echo "� Cloning Plotcode project..."
mkdir -p /opt/plotcode
if [ ! -d /opt/plotcode/agents ]; then
    cd /opt
    if [ -d plotcode/.git ]; then
        cd plotcode && git pull
    else
        echo "⚠️  Please clone your repo manually:"
        echo "   cd /opt && git clone https://github.com/YOUR_USERNAME/plotcode.git"
    fi
fi

# ─── 10. Set Up Backend (Python venv) ─────────────────────────────────────────
echo "🐍 Setting up Python backend..."
cd /opt/plotcode/agents
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate

# ─── 11. Set Up Frontend (Node build) ─────────────────────────────────────────
echo "⚛️  Building frontend..."
cd /opt/plotcode/frontend
npm install
# Set API URL to same server (Nginx proxies /api to backend)
export VITE_API_URL=/api
npm run build

# Copy build to Nginx serve directory
mkdir -p /var/www/plotcode
cp -r dist/* /var/www/plotcode/
echo "✅ Frontend built and copied to /var/www/plotcode"

# ─── 12. Create .env file ─────────────────────────────────────────────────────
echo "📝 Creating .env template..."
if [ ! -f /opt/plotcode/agents/.env ]; then
    cp /opt/plotcode/.env.example /opt/plotcode/agents/.env
    echo "⚠️  Edit /opt/plotcode/agents/.env with your real values!"
fi

# ─── 13. PM2 Process Manager ──────────────────────────────────────────────────
echo "🚀 Setting up PM2 process manager..."
cat > /opt/plotcode/ecosystem.config.js << 'PM2'
module.exports = {
  apps: [{
    name: 'plotcode-backend',
    cwd: '/opt/plotcode/agents',
    script: 'venv/bin/uvicorn',
    args: 'api:app --host 0.0.0.0 --port 8001',
    env: {
      PORT: 8001
    },
    max_restarts: 10,
    restart_delay: 3000,
  }]
};
PM2

pm2 delete plotcode-backend 2>/dev/null || true
pm2 start /opt/plotcode/ecosystem.config.js
pm2 save
pm2 startup systemd -y

# ─── 14. Summary ──────────────────────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║   ✅ Setup Complete!                                         ║"
echo "╠══════════════════════════════════════════════════════════════╣"
echo "║                                                              ║"
echo "║   🌐 Frontend:     http://$VPS_IP                          ║"
echo "║   🔌 Backend API:  http://$VPS_IP:8001                     ║"
echo "║   📦 Git SSH:      git@$VPS_IP:/repos/repo.git            ║"
echo "║   📦 Git HTTP:     http://$VPS_IP/git/repo.git             ║"
echo "║                                                              ║"
echo "║   📁 Repos:        /repos/                                   ║"
echo "║   🐍 Backend:      /opt/plotcode/agents/                     ║"
echo "║   ⚛️  Frontend:     /var/www/plotcode/                        ║"
echo "║   📝 Config:       /opt/plotcode/agents/.env                 ║"
echo "║                                                              ║"
echo "║   Next steps:                                                ║"
echo "║   1. Edit .env:                                              ║"
echo "║      nano /opt/plotcode/agents/.env                          ║"
echo "║      pm2 restart plotcode-backend                            ║"
echo "║                                                              ║"
echo "║   2. Add SSH keys for git access:                            ║"
echo "║      echo 'ssh-rsa AAA...' >> /home/git/.ssh/authorized_keys║"
echo "║                                                              ║"
echo "║   3. Set HTTP auth for git:                                  ║"
echo "║      apt install apache2-utils                               ║"
echo "║      htpasswd -c /etc/nginx/.htpasswd <username>             ║"
echo "║                                                              ║"
echo "║   4. Create new git repo:                                    ║"
echo "║      git init --bare /repos/myrepo.git                       ║"
echo "║      chown -R git:git /repos/myrepo.git                      ║"
echo "║                                                              ║"
echo "║   5. Check status:                                           ║"
echo "║      pm2 status                                              ║"
echo "║      pm2 logs plotcode-backend                               ║"
echo "║                                                              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
