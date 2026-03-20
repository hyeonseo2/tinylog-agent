#!/usr/bin/env bash
set -euo pipefail

# TinyLog log monitoring launcher
# Usage:
#   TINYLOG_BACKEND=ollama ./start_tinylog_monitor.sh
#   TINYLOG_FILES="/path/a,/path/b" ./start_tinylog_monitor.sh
# Default backend=none (deterministic mode).

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="${SCRIPT_DIR}/tinylog_monitor.log"
PID_FILE="${SCRIPT_DIR}/tinylog_monitor.pid"

# Optional: override monitor files via env. Comma-separated list.
if [[ -n "${TINYLOG_FILES:-}" ]]; then
  IFS=',' read -r -a MONITOR_FILES <<< "${TINYLOG_FILES}"
else
  MONITOR_FILES=(
    /var/log/syslog
    /var/log/auth.log
    /var/log/kern.log
    /var/log/dmesg
  )
fi

# Filter readable files
EXISTING_FILES=()
for f in "${MONITOR_FILES[@]}"; do
  if [[ -r "$f" ]]; then
    EXISTING_FILES+=("$f")
  fi
done

if (( ${#EXISTING_FILES[@]} == 0 )); then
  echo "No readable log files found. Check permissions and log paths." >&2
  exit 1
fi

BACKEND="${TINYLOG_BACKEND:-none}"
BACKEND_HOST="${TINYLOG_BACKEND_HOST:-http://127.0.0.1:11434}"
BACKEND_MODEL="${TINYLOG_BACKEND_MODEL:-qwen2.5:0.5b}"
TIMEOUT="${TINYLOG_BACKEND_TIMEOUT:-600}"
ROUND="${TINYLOG_REVIEW_ROUNDS:-2}"
WINDOW="${TINYLOG_WINDOW_SECONDS:-120}"
THRESHOLD="${TINYLOG_THRESHOLD:-1}"
COOLDOWN="${TINYLOG_COOLDOWN_SECONDS:-30}"

nohup python3 -u "${SCRIPT_DIR}/main.py" \
  --files "${EXISTING_FILES[@]}" \
  --backend "$BACKEND" \
  --backend-host "$BACKEND_HOST" \
  --backend-model "$BACKEND_MODEL" \
  --backend-timeout "$TIMEOUT" \
  --review-rounds "$ROUND" \
  --window-seconds "$WINDOW" \
  --threshold "$THRESHOLD" \
  --cooldown-seconds "$COOLDOWN" \
  --output json \
  > "$LOG_FILE" 2>&1 &

echo $! > "$PID_FILE"
echo "TinyLog monitor started (pid $(cat "$PID_FILE"))"
echo "Log: $LOG_FILE"
echo "Tracking files: ${EXISTING_FILES[*]}"
