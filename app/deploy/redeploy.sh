#!/bin/bash
# Quick redeploy: pull latest, rebuild frontend with correct API URL, restart
# Run from EC2: bash /opt/aml-dashboard/app/deploy/redeploy.sh
set -e
cd /opt/aml-dashboard || { echo "Repo not at /opt/aml-dashboard"; exit 1; }
PUBLIC_IP="${1:-$(curl -s --connect-timeout 2 http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo "35.183.1.0")}"
echo "Redeploying (Frontend: http://${PUBLIC_IP}:3000, API: http://${PUBLIC_IP}:8000)"
git pull
test -f app/.env || cp app/.env.example app/.env
echo "Building frontend (2-3 min)..."
# Use api:8000 for SSR; client derives from window.location in browser
sudo docker compose -f app/deploy/docker-compose.build.yml build --no-cache frontend
echo "Restarting services..."
sudo docker compose -f app/deploy/docker-compose.build.yml up -d
echo "Done. Frontend: http://${PUBLIC_IP}:3000"
