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

echo "==> Pulling latest code..."
cd "$REPO_ROOT"
git pull

echo "==> Restarting backend service..."
sudo systemctl restart fluxo-backend

echo "Deploy complete."
