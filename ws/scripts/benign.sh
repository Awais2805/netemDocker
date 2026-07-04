#!/usr/bin/env bash
# Benign traffic generator script: uses paced HTTP browsing + occasional SSH logins 
# against the victim. Goal is to generate a realistic benign traffic baseline in the capture. 

set -u

VICTIM="${VICTIM:-172.30.0.10}"
DURATION="${1:-60}"
WORKERS="${2:-4}"
SSH_USER="victimuser"
SSH_PASS="password123"

PATHS=("/" "/index.html" "/index.nginx-debian.html" "/about" "/contact" "/missing")

worker() {
    local id="$1"
    local end=$(( $(date +%s) + DURATION ))
    while [ "$(date +%s)" -lt "$end" ]; do
        roll=$(( RANDOM % 100 ))
        if [ "$roll" -lt 85 ]; then                       # ~85% HTTP GETs
            p="${PATHS[$RANDOM % ${#PATHS[@]}]}"
            code=$(curl -s -o /dev/null -w '%{http_code}' "http://${VICTIM}${p}")
            echo "[benign w${id}] GET ${p} -> ${code}"
        else                                              # ~15% SSH logins
            out=$(sshpass -p "$SSH_PASS" ssh -o StrictHostKeyChecking=no \
                  -o ConnectTimeout=5 "${SSH_USER}@${VICTIM}" \
                  'uptime; ls /' 2>/dev/null | head -n1)
            echo "[benign w${id}] SSH -> ${out:-<no output>}"
        fi
        sleep "0.$(( RANDOM % 18 + 3 ))"                  # 0.3-2.0s pacing
    done
}

echo "[benign] targeting $VICTIM for ${DURATION}s with ${WORKERS} workers"
for i in $(seq 1 "$WORKERS"); do
    worker "$i" &
done
wait
echo "[benign] done"