#!/usr/bin/env bash
# Memory watchdog — guarantees a render can never freeze macOS.
# Polls system-wide free memory; if it stays critically low, kills the LTX
# render processes (graceful TERM, then KILL). Worst case the render aborts;
# the Mac stays responsive.
#
# Usage: mem_guard.sh [THRESHOLD_PCT] [LOGFILE]
set -u
THRESH="${1:-10}"          # kill if free% stays below this
LOG="${2:-/tmp/mem_guard.log}"
PATTERNS=("inference.py" "cinematic-pipeline/pipeline.py")
low=0
: > "$LOG"
echo "$(date +%H:%M:%S) watchdog start thresh=${THRESH}%" >> "$LOG"

running() { for p in "${PATTERNS[@]}"; do pgrep -f "$p" >/dev/null 2>&1 && return 0; done; return 1; }

# wait up to 30s for the render to appear
for _ in $(seq 1 10); do running && break; sleep 3; done

while running; do
  free=$(memory_pressure 2>/dev/null | awk -F': ' '/free percentage/{gsub(/%/,"",$2);print $2}')
  sw=$(sysctl -n vm.swapusage 2>/dev/null | awk '{print $7}')
  echo "$(date +%H:%M:%S) free=${free:-?}% swap=${sw:-?}" >> "$LOG"
  if [ -n "${free:-}" ] && [ "$free" -lt "$THRESH" ]; then
    low=$((low+1))
    echo "$(date +%H:%M:%S) low streak=$low (free=${free}%)" >> "$LOG"
    if [ "$low" -ge 2 ]; then
      echo "$(date +%H:%M:%S) CRITICAL — killing render to protect macOS" >> "$LOG"
      for p in "${PATTERNS[@]}"; do pkill -TERM -f "$p" 2>/dev/null; done
      sleep 4
      for p in "${PATTERNS[@]}"; do pkill -KILL -f "$p" 2>/dev/null; done
      break
    fi
  else
    low=0
  fi
  sleep 3
done
echo "$(date +%H:%M:%S) watchdog exit" >> "$LOG"
