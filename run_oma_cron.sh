#!/bin/bash
# OMA-CORE Cron Job — Ejecuta pipeline completo cada hora

PROJECT_DIR="/home/kito/O.M.A.-C.O.R.E."
LOG_FILE="$PROJECT_DIR/logs/cron.log"

# Timestamp
echo "========================================" >> "$LOG_FILE"
echo "$(date): Iniciando OMA-CORE cron job" >> "$LOG_FILE"

cd "$PROJECT_DIR"

# Cargar variables de entorno
export TELEGRAM_BOT_TOKEN=$(grep TELEGRAM_BOT_TOKEN .env | cut -d= -f2)
export TELEGRAM_CHAT_ID=$(grep TELEGRAM_CHAT_ID .env | cut -d= -f2)
export DATABASE_URL="postgresql://oma_user:6o32FDYDomx70doHCJCHAtZSTEw7pG34@dpg-d8rfstb6sc1c73b7oit0-a.virginia-postgres.render.com/oma_core"

# Activar entorno virtual si existe
source venv/bin/activate 2>/dev/null || source .venv/bin/activate 2>/dev/null || true

# Ejecutar pipeline
echo "$(date): Ejecutando oma run..." >> "$LOG_FILE"
python3 -m core.cli.main run >> "$LOG_FILE" 2>&1

# Sincronizar con PostgreSQL
echo "$(date): Sincronizando PostgreSQL..." >> "$LOG_FILE"
python3 migrate_to_postgres.py >> "$LOG_FILE" 2>&1

echo "$(date): Completado" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"
