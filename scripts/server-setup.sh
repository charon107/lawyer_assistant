#!/bin/bash
# LPA Review App — Server one-time setup
# Run as root on Ubuntu 24.04:  bash server-setup.sh

set -e

echo "=== Installing Docker ==="
if ! command -v docker &>/dev/null; then
    curl -fsSL https://get.docker.com | bash
    apt install -y docker-compose-plugin
fi

echo "=== Cloning repository ==="
REPO_URL="https://github.com/charon107/lawyer_assistant.git"
APP_DIR="/opt/lpa_review_app"

if [ -d "$APP_DIR" ]; then
    echo "App directory exists, pulling latest..."
    cd "$APP_DIR"
    git pull
else
    git clone "$REPO_URL" "$APP_DIR"
fi

echo "=== Setting up backend .env ==="
cd "$APP_DIR/backend"
if [ ! -f .env ]; then
    cp .env.example .env
    echo ">>> WARNING: Edit /opt/lpa_review_app/backend/.env with real values! <<"
fi

echo ""
echo "=== Setup complete ==="
echo ""
echo "Next steps:"
echo "  1. Edit /opt/lpa_review_app/backend/.env with production secrets"
echo "  2. Run:  cd /opt/lpa_review_app && docker compose up -d"
echo ""
echo "For production with pre-built images (after GitHub Actions is configured):"
echo "  cd /opt/lpa_review_app && docker compose -f docker-compose.prod.yml up -d"
