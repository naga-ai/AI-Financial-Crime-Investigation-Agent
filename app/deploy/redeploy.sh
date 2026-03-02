#!/bin/bash
# Quick redeploy: pull latest, rebuild frontend with correct API URL, restart
# Run from EC2: bash /opt/aml-dashboard/app/deploy/redeploy.sh
set -e
cd /opt/aml-dashboard || { echo "Repo not at /opt/aml-dashboard"; exit 1; }
PUBLIC_IP="${1:-$(curl -s --connect-timeout 2 http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo "35.183.1.0")}"
export NEXT_PUBLIC_API_URL="http://${PUBLIC_IP}:8000"
echo "Redeploying with API URL: $NEXT_PUBLIC_API_URL"
git pull
test -f app/.env || cp app/.env.example app/.env
echo "Building frontend (2-3 min)..."
NEXT_PUBLIC_API_URL="$NEXT_PUBLIC_API_URL" sudo -E docker compose -f app/deploy/docker-compose.build.yml build --no-cache frontend
echo "Restarting services..."
sudo docker compose -f app/deploy/docker-compose.build.yml up -d
echo "Done. Frontend: http://${PUBLIC_IP}:3000"
