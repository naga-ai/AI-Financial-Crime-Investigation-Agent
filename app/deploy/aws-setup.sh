#!/bin/bash
# =============================================================================
# AWS EC2 Setup Script
# Deploys the AML Investigation stack (Next.js frontend + FastAPI API + Redis).
#
# Usage:
#   1. Launch EC2 (e.g. t3.small, 20GB). Security group: TCP 3000, 8000 open.
#   2. SSH in and run:  bash app/deploy/aws-setup.sh <GITHUB_REPO_URL>
#   3. Open frontend at http://<PUBLIC_IP>:3000
# =============================================================================

set -euo pipefail

REPO_URL="${1:-}"
APP_DIR="/opt/aml-dashboard"
COMPOSE_FILE="app/deploy/docker-compose.build.yml"

if [ -z "$REPO_URL" ]; then
    echo "Usage: bash app/deploy/aws-setup.sh <GITHUB_REPO_URL>"
    echo "Example: bash app/deploy/aws-setup.sh https://github.com/youruser/wealthsimple-aml-agent.git"
    exit 1
fi

echo "============================================"
echo "  AML Investigation Agent -- AWS Deployment"
echo "============================================"

# Detect OS and install Docker
echo "[1/6] Installing Docker..."
if command -v apt-get &> /dev/null; then
    sudo apt-get update -y
    sudo apt-get install -y docker.io docker-compose-plugin git
    sudo systemctl enable docker
    sudo systemctl start docker
elif command -v yum &> /dev/null; then
    sudo yum update -y
    sudo yum install -y docker git
    sudo systemctl enable docker
    sudo systemctl start docker
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi
sudo usermod -aG docker "$USER"

# Clone repo
echo "[2/6] Cloning repository..."
sudo rm -rf "$APP_DIR"
sudo git clone "$REPO_URL" "$APP_DIR"
sudo chown -R "$USER:$USER" "$APP_DIR"
cd "$APP_DIR"

# Create .env in app dir if missing
echo "[3/6] Configuring environment..."
if [ ! -f app/.env ]; then
    [ -f app/.env.example ] && cp app/.env.example app/.env || touch app/.env
fi

# Public IP for frontend API URL (browser will call EC2:8000)
PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo "localhost")
export NEXT_PUBLIC_API_URL="http://${PUBLIC_IP}:8000"

# Build and start (builds API + frontend on this host; no GHCR needed)
echo "[4/6] Building and starting containers (this may take several minutes)..."
sudo -E docker compose -f "$COMPOSE_FILE" up --build -d

# Wait for API health
echo "[5/6] Waiting for services to start..."
for i in {1..30}; do
    if curl -sf http://localhost:8000/api/health > /dev/null 2>&1; then
        break
    fi
    sleep 2
    echo "  Waiting... ($((i*2))s)"
done

echo "[6/6] Ready."

echo ""
echo "============================================"
echo "  DEPLOYMENT COMPLETE"
echo "============================================"
echo ""
echo "  Frontend:  http://${PUBLIC_IP}:3000"
echo "  API:       http://${PUBLIC_IP}:8000"
echo ""
echo "  Services:"
echo "    - Next.js frontend (port 3000)"
echo "    - FastAPI API (port 8000)"
echo "    - Redis (port 6379, internal)"
echo ""
echo "  Logs:   sudo docker compose -f $COMPOSE_FILE logs -f"
echo "  Stop:   sudo docker compose -f $COMPOSE_FILE down"
echo "============================================"
