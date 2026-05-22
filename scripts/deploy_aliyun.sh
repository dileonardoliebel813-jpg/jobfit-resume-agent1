#!/usr/bin/env bash
set -Eeuo pipefail

REPO_URL="https://github.com/dileonardoliebel813-jpg/jobfit-resume-agent1.git"
REPO_DIR="/opt/jobfit-resume-agent1"
BACKEND_DIR="$REPO_DIR/backend"
ENV_FILE="$BACKEND_DIR/.env"
SERVICE_FILE="/etc/systemd/system/jobfit.service"

if [ "$(id -u)" -ne 0 ]; then
  echo "Please run as root: sudo -i"
  exit 1
fi

echo "==> Installing system dependencies"
apt update
apt install -y git python3 python3-venv python3-pip curl

echo "==> Preparing repository"
mkdir -p /opt
if [ ! -d "$REPO_DIR/.git" ]; then
  git clone "$REPO_URL" "$REPO_DIR"
fi

cd "$REPO_DIR"
git fetch origin main
git reset --hard origin/main

if [ ! -f "$ENV_FILE" ]; then
  cat > "$ENV_FILE.example" <<'EOF'
LLM_MODE=real
LLM_PROVIDER=openai
OPENAI_API_KEY=your_real_key_here
OPENAI_BASE_URL=https://mx.free.codesonline.dev
OPENAI_MODEL=gpt-5.4
OPENAI_REVIEW_MODEL=gpt-5.4
OPENAI_WIRE_API=responses
MODEL_REASONING_EFFORT=xhigh
JD_REASONING_EFFORT=medium
PROFILE_REASONING_EFFORT=medium
RESUME_REASONING_EFFORT=xhigh
REVIEW_REASONING_EFFORT=xhigh
DISABLE_RESPONSE_STORAGE=true
LLM_TIMEOUT_SECONDS=180
LLM_MAX_RETRIES=0
EOF
  echo "ERROR: Missing $ENV_FILE"
  echo "A template was created at $ENV_FILE.example"
  echo "Create the real file with: nano $ENV_FILE"
  exit 1
fi

echo "==> Creating Python virtual environment"
cd "$BACKEND_DIR"
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple
python -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

echo "==> Installing systemd service"
cat > "$SERVICE_FILE" <<EOF
[Unit]
Description=JobFit Resume Agent
After=network.target

[Service]
WorkingDirectory=$BACKEND_DIR
EnvironmentFile=$ENV_FILE
ExecStart=$BACKEND_DIR/.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 80
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

pkill -f "uvicorn app.main:app" || true
systemctl daemon-reload
systemctl enable jobfit
systemctl restart jobfit

echo "==> Health check"
sleep 3
systemctl --no-pager --full status jobfit || true
curl -fsS http://127.0.0.1/health
echo
echo "==> Done. Open: http://39.96.11.186/?v=deploy"
