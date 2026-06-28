#!/bin/bash
# install_local_oma_launcher.sh
# Safely aligns /usr/local/bin/oma with /home/kito/O.M.A.-C.O.R.E.
# Requires sudo for writing to /usr/local/bin/oma.
# Idempotent: creates a backup before overwriting.

set -euo pipefail

REPO_DIR="/home/kito/O.M.A.-C.O.R.E."
LAUNCHER_PATH="/usr/local/bin/oma"

if [ ! -d "$REPO_DIR" ]; then
    echo "ERROR: Repo directory $REPO_DIR does not exist."
    exit 1
fi

# --- Backup existing launcher ---
if [ -f "$LAUNCHER_PATH" ]; then
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP="${LAUNCHER_PATH}.backup_${TIMESTAMP}"
    echo "[install] Backing up $LAUNCHER_PATH -> $BACKUP"
    cp "$LAUNCHER_PATH" "$BACKUP"
    chmod 644 "$BACKUP"
fi

# --- Write new launcher ---
NEW_LAUNCHER=$(cat <<'OMALAUNCHER'
#!/bin/bash
# O.M.A.-C.O.R.E. Launcher — installed by install_local_oma_launcher.sh
PROJECT="/home/kito/O.M.A.-C.O.R.E."
cd "$PROJECT"

# Activate virtual environment if available
if [ -f "$PROJECT/.venv/bin/activate" ]; then
    source "$PROJECT/.venv/bin/activate"
elif [ -f "$PROJECT/venv/bin/activate" ]; then
    source "$PROJECT/venv/bin/activate"
fi

echo "[oma] Project: $PROJECT"
exec python -m core.cli.main "$@"
OMALAUNCHER
)

echo "$NEW_LAUNCHER" > "$LAUNCHER_PATH"
chmod 755 "$LAUNCHER_PATH"

echo "[install] ✓ Launcher updated: $LAUNCHER_PATH"
echo "[install]   Target: $REPO_DIR"
echo "[install]   Backup: $(ls -t ${LAUNCHER_PATH}.backup_* 2>/dev/null | head -1)"

# --- Also update run_oma_cron.sh if it still points to old location ---
CRON_SCRIPT="$REPO_DIR/run_oma_cron.sh"
if [ -f "$CRON_SCRIPT" ]; then
    OLD_PROJECT_LINE='PROJECT_DIR="/home/kito/Projects/OMA-CORE by KIMI"'
    NEW_PROJECT_LINE='PROJECT_DIR="/home/kito/O.M.A.-C.O.R.E."'
    if grep -q "$OLD_PROJECT_LINE" "$CRON_SCRIPT"; then
        sed -i "s|$OLD_PROJECT_LINE|$NEW_PROJECT_LINE|g" "$CRON_SCRIPT"
        echo "[install] ✓ Updated PROJECT_DIR in $CRON_SCRIPT"
    else
        echo "[install]   $CRON_SCRIPT already points to correct repo (or unrecognized path)"
    fi
fi

echo "[install] Done."
echo "[install] Run 'oma run' to test (will execute from current repo)."
