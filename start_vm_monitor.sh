#!/usr/bin/env bash
set -euo pipefail

# TinyLog 실시간 모니터링 런처
# 사용법:
#   TINYLOG_BACKEND=ollama ./start_vm_monitor.sh
# 기본은 backend=none(순수 rule 기반)입니다.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="${SCRIPT_DIR}/tinylog_monitor.log"
PID_FILE="${SCRIPT_DIR}/tinylog_monitor.pid"

MONITOR_FILES=(
  /var/log/syslog
  /var/log/auth.log
  /var/log/kern.log
  /var/log/dmesg
)

# 사용 가능한 파일만 필터링
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
THRESHOLD="${TINYLOG_THRESHOLD:-3}"
COOLDOWN="${TINYLOG_COOLDOWN_SECONDS:-180}"

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
