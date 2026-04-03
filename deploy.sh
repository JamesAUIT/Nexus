#!/usr/bin/env bash
# Cloud Nexus — Deploy to Debian 13 VM
# Run from repo root. Idempotent where possible.
# No sudo required if Docker Engine + Compose v2 are already installed and this user can run `docker` (e.g. member of `docker` group).
# One-time OS install of Docker (apt): run INSTALL_DOCKER=1 as root, or install Docker manually then use ./deploy.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ---------------------------------------------------------------------------
# Options (override with env or pass after --)
# ---------------------------------------------------------------------------
INSTALL_DOCKER="${INSTALL_DOCKER:-0}"
SKIP_SEED="${SKIP_SEED:-}"
FORCE_ENV_PROMPT="${FORCE_ENV_PROMPT:-}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --install-docker)    INSTALL_DOCKER=1; shift ;;
    --no-install-docker) INSTALL_DOCKER=0; shift ;;
    --skip-seed)         SKIP_SEED=1; shift ;;
    --prompt-env)        FORCE_ENV_PROMPT=1; shift ;;
    *) break ;;
  esac
done

# ---------------------------------------------------------------------------
# 1. Docker + Docker Compose (Debian, root only) + require docker compose
# ---------------------------------------------------------------------------
ensure_docker_compose() {
  if command -v docker &>/dev/null && docker compose version &>/dev/null 2>&1; then
    return 0
  fi
  echo "ERROR: Docker Engine and Compose v2 ('docker compose') are required."
  echo "  Install Docker and add this user to the 'docker' group, or run once as root:"
  echo "    sudo INSTALL_DOCKER=1 $0   # or: sudo $0 --install-docker"
  exit 1
}

install_docker_debian() {
  if command -v docker &>/dev/null && docker compose version &>/dev/null 2>&1; then
    echo "Docker and Docker Compose already present."
    return 0
  fi

  echo "Installing Docker and Docker Compose for Debian..."
  export DEBIAN_FRONTEND=noninteractive

  apt-get update -qq
  apt-get install -y -qq ca-certificates curl

  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc
  chmod a+r /etc/apt/keyrings/docker.asc

  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian $(. /etc/os-release && echo "${VERSION_CODENAME:-bookworm}") stable" \
    | tee /etc/apt/sources.list.d/docker.list > /dev/null

  apt-get update -qq
  apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

  systemctl enable --now docker
  echo "Docker installed."
}

if [[ "$INSTALL_DOCKER" == "1" ]]; then
  if [[ $(id -u) -ne 0 ]]; then
    echo "INSTALL_DOCKER=1 needs root for apt. Skipping package install; using existing Docker."
  elif [[ -f /etc/os-release ]]; then
    source /etc/os-release
    if [[ "${ID:-}" == "debian" ]]; then
      install_docker_debian
    else
      echo "Not Debian (ID=$ID). Skipping apt Docker install. Ensure Docker and 'docker compose' are available."
    fi
  else
    echo "Cannot detect OS. Skipping Docker install."
  fi
fi
ensure_docker_compose

# ---------------------------------------------------------------------------
# 2. .env from .env.example if missing
# ---------------------------------------------------------------------------
if [[ ! -f .env ]]; then
  if [[ ! -f .env.example ]]; then
    echo "ERROR: .env.example not found. Run this script from the Cloud Nexus repo root."
    exit 1
  fi
  cp .env.example .env
  echo "Created .env from .env.example. Edit .env and set POSTGRES_PASSWORD, SECRET_KEY, ENCRYPTION_KEY, ADMIN_PASSWORD."
  if [[ -n "$FORCE_ENV_PROMPT" ]]; then
    echo "Set required secrets (or leave empty to keep placeholders):"
    read -rp "POSTGRES_PASSWORD (or Enter to keep): " p
    [[ -n "$p" ]] && sed -i "s/^POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=$p/" .env
    read -rp "SECRET_KEY (or Enter to keep): " s
    [[ -n "$s" ]] && sed -i "s|^SECRET_KEY=.*|SECRET_KEY=$s|" .env
    read -rp "ENCRYPTION_KEY (or Enter to keep): " e
    [[ -n "$e" ]] && sed -i "s|^ENCRYPTION_KEY=.*|ENCRYPTION_KEY=$e|" .env
    read -rp "ADMIN_PASSWORD (or Enter to keep): " a
    [[ -n "$a" ]] && sed -i "s|^ADMIN_PASSWORD=.*|ADMIN_PASSWORD=$a|" .env
  else
    echo "Generate secrets: openssl rand -hex 32 (for SECRET_KEY and ENCRYPTION_KEY)."
    exit 1
  fi
fi

# ---------------------------------------------------------------------------
# 3. Start stack
# ---------------------------------------------------------------------------
echo "Starting Docker Compose stack..."
docker compose --env-file .env up -d --build

# ---------------------------------------------------------------------------
# 4. Wait for API health
# ---------------------------------------------------------------------------
echo "Waiting for API to be healthy..."
max=60
for i in $(seq 1 "$max"); do
  if docker compose exec -T api curl -sf http://localhost:8000/health &>/dev/null; then
    echo "API is up."
    break
  fi
  if [[ $i -eq $max ]]; then
    echo "API did not become healthy in time."
    exit 1
  fi
  sleep 2
done

# ---------------------------------------------------------------------------
# 5. Migrations
# ---------------------------------------------------------------------------
echo "Running database migrations..."
docker compose run --rm api alembic upgrade head

# ---------------------------------------------------------------------------
# 6. Optional seed
# ---------------------------------------------------------------------------
if [[ -z "$SKIP_SEED" ]]; then
  if grep -q '^DEMO_MODE=true' .env || grep -q '^SEED_DB=1' .env; then
    echo "Running seed (DEMO_MODE or SEED_DB=1)..."
    docker compose run --rm api python -m src.db.seed || true
  else
    echo "Skipping seed (DEMO_MODE not true, SEED_DB not 1). To seed: set DEMO_MODE=true or SEED_DB=1 in .env and run: docker compose run --rm api python -m src.db.seed"
  fi
else
  echo "Seed skipped (--skip-seed)."
fi

echo "Deploy complete. HTTPS (UI + API via nginx): https://localhost:443  (self-signed: use -k with curl or trust cert)"
