#!/bin/bash
# =============================================================================
# AWS EC2 Setup Script
# Deploys the AML Investigation Command Center on a fresh Amazon Linux 2023 / Ubuntu instance.
#
# Usage:
#   1. Launch EC2 (t3.small, 20GB, security group: TCP 8501 open)
#   2. SSH in and run:  bash aws-setup.sh <YOUR_GITHUB_REPO_URL>
#   3. Access dashboard at http://<PUBLIC_IP>:8501
# =============================================================================

set -euo pipefail

REPO_URL="${1:-}"
APP_DIR="/opt/aml-dashboard"

if [ -z "$REPO_URL" ]; then
    echo "Usage: bash aws-setup.sh <GITHUB_REPO_URL>"
    echo "Example: bash aws-setup.sh https://github.com/youruser/wealthsimple-aml-agent.git"
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

# Create .env (no API keys needed for demo)
echo "[3/6] Configuring environment..."
if [ ! -f .env ]; then
    cp .env.example .env
fi

# Build and start
echo "[4/6] Building Docker image (this takes 2-3 minutes)..."
sudo docker compose up --build -d

# Wait for health
echo "[5/6] Waiting for services to start..."
for i in {1..30}; do
    if curl -s http://localhost:8501/_stcore/health > /dev/null 2>&1; then
        break
    fi
    sleep 2
    echo "  Waiting... ($((i*2))s)"
done

# Get public IP
echo "[6/6] Getting public IP..."
PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo "YOUR_EC2_PUBLIC_IP")

echo ""
echo "============================================"
echo "  DEPLOYMENT COMPLETE"
echo "============================================"
echo ""
echo "  Dashboard URL:  http://${PUBLIC_IP}:8501"
echo ""
echo "  Share this URL with Wealthsimple reviewers."
echo "  They can click 'Run Pipeline' to see the"
echo "  full AI investigation system in action."
echo ""
echo "  Services running:"
echo "    - Streamlit dashboard (port 8501)"
echo "    - Redis cache (port 6379)"
echo ""
echo "  To check logs:  sudo docker compose logs -f"
echo "  To stop:        sudo docker compose down"
echo "============================================"
