#!/usr/bin/env bash
# deploy.sh — build frontend and restart the backend service
# Run this on the server after pulling new code:
#   cd /opt/fluxo && git pull && bash deploy/deploy.sh

set -e

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FRONTEND_DIR="$REPO_ROOT/frontend"
BACKEND_DIR="$REPO_ROOT/backend"

echo "==> Installing frontend dependencies..."
cd "$FRONTEND_DIR"
npm ci

echo "==> Building frontend into backend/static..."
npm run build

echo "==> Restarting backend service..."
sudo systemctl restart fluxo-backend

echo "==> Waiting for service to come up..."
sleep 5
sudo systemctl status fluxo-backend --no-pager

echo ""
echo "Deploy complete. Site is live at https://fluxo.avinashrajmalaka.in"
echo ""
echo "NOTE: Make sure your Cloudflare tunnel points to http://localhost:8081"
echo "      (not port 80 — that's CasaOS)"
