#!/bin/bash
# Memory monitoring script for mini-swe-agent evaluation
# Logs system memory, swap, and Docker container memory every 5 seconds
#
# Usage: ./monitor_memory.sh [output_log_file]
# Default: /home/sailorjoe6/work/swebench/runs/memory-monitor-$(date +%Y%m%d-%H%M%S).log

set -e

LOG_FILE="${1:-/home/sailorjoe6/work/swebench/runs/memory-monitor-$(date +%Y%m%d-%H%M%S).log}"
INTERVAL=5

mkdir -p "$(dirname "$LOG_FILE")"

echo "=== Memory Monitor Started ===" | tee "$LOG_FILE"
echo "PID: $$" | tee -a "$LOG_FILE"
echo "Log file: $LOG_FILE" | tee -a "$LOG_FILE"
echo "Interval: ${INTERVAL}s" | tee -a "$LOG_FILE"
echo "Started at: $(date '+%Y-%m-%d %H:%M:%S')" | tee -a "$LOG_FILE"
echo "---" | tee -a "$LOG_FILE"

while true; do
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

    # Get memory info
    MEM_INFO=$(free -h | grep Mem | awk '{printf "Total:%s Used:%s Free:%s Available:%s", $2, $3, $4, $7}')
    SWAP_INFO=$(free -h | grep Swap | awk '{printf "SwapUsed:%s SwapFree:%s", $3, $4}')

    # Get memory percentage
    MEM_PCT=$(free | grep Mem | awk '{printf "%.1f%%", $3/$2*100}')

    # Count Docker containers (running and total)
    DOCKER_RUNNING=$(docker ps -q 2>/dev/null | wc -l || echo "0")
    DOCKER_TOTAL=$(docker ps -aq 2>/dev/null | wc -l || echo "0")

    # Get Docker memory usage for running containers (first 5)
    DOCKER_MEM=$(docker stats --no-stream --format '{{.Name}}={{.MemUsage}}' 2>/dev/null | head -5 | tr '\n' ' ' || echo "none")

    # Log entry
    echo "$TIMESTAMP | Mem($MEM_PCT): $MEM_INFO | $SWAP_INFO | Docker: $DOCKER_RUNNING/$DOCKER_TOTAL | $DOCKER_MEM" >> "$LOG_FILE"

    # Also output to stderr for live monitoring
    echo "$TIMESTAMP | Mem($MEM_PCT)" >&2

    sleep $INTERVAL
done
