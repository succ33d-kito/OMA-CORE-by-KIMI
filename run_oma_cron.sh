#!/bin/bash
# OMA-CORE Cron Job — Ejecuta pipeline completo cada hora
# Secrets are loaded from .env or the host environment.
# Never hardcode DATABASE_URL, TELEGRAM_BOT_TOKEN, API keys, or passwords here.

set -euo pipefail

PROJECT_DIR="/home/kito/O.M.A.-C.O.R.E."
LOG_DIR="$PROJECT_DIR/logs"
LOG_FILE="$LOG_DIR/cron.log"

mkdir -p "$LOG_DIR"

echo "========================================" >> "$LOG_FILE"
echo "$(date): Iniciando OMA-CORE cron job" >> "$LOG_FILE"

cd "$PROJECT_DIR"

# Load local environment variables if .env exists.
# .env must remain untracked and listed in .gitignore.
if [ -f ".env" ]; then
  set -a
  source ".env"
  set +a
fi

# Activate virtual environment if available.
if [ -f "venv/bin/activate" ]; then
  source "venv/bin/activate"
elif [ -f ".venv/bin/activate" ]; then
  source ".venv/bin/activate"
fi

PYTHON_BIN="${PYTHON_BIN:-python3}"

# Run pipeline.
echo "$(date): Ejecutando oma run..." >> "$LOG_FILE"
"$PYTHON_BIN" -m core.cli.main run >> "$LOG_FILE" 2>&1

# Sync with PostgreSQL only if DATABASE_URL exists.
if [ -n "${DATABASE_URL:-}" ]; then
  echo "$(date): Sincronizando PostgreSQL..." >> "$LOG_FILE"
  "$PYTHON_BIN" migrate_to_postgres.py >> "$LOG_FILE" 2>&1
else
  echo "$(date): DATABASE_URL no configurado; saltando sincronización PostgreSQL." >> "$LOG_FILE"
fi

echo "$(date): Completado" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"
