#!/usr/bin/env bash
# Benign generator (varied): N workers hit differently-sized pages and run
# varied SSH commands, so benign traffic isn't a single archetype.
# Use: benign.sh [DURATION] [WORKERS]

set -u

VICTIM="${VICTIM:-172.30.0.10}"
DURATION="${1:-60}"
WORKERS="${2:-4}"
SSH_USER="victimuser"
SSH_PASS="password123"

PATHS=("/" "/pages/p1k.html" "/pages/p4k.html" "/pages/p16k.html" \
       "/pages/p64k.html" "/pages/p256k.html" "/missing" "/nope" "/admin")
SSH_CMDS=("uptime" "ls -la /" "cat /etc/hostname" "id" "df -h" \
          "ps aux" "ls -R /etc 2>/dev/null | head -n 200" "whoami")

worker() {
    local id="$1"
    local end=$(( $(date +%s) + DURATION ))
    while [ "$(date +%s)" -lt "$end" ]; do
        roll=$(( RANDOM % 100 ))
        if [ "$roll" -lt 85 ]; then
            p="${PATHS[$RANDOM % ${#PATHS[@]}]}"
            code=$(curl -s -o /dev/null -w '%{http_code}' "http://${VICTIM}${p}")
            echo "[benign w${id}] GET ${p} -> ${code}"
        else
            c="${SSH_CMDS[$RANDOM % ${#SSH_CMDS[@]}]}"
            out=$(sshpass -p "$SSH_PASS" ssh -o StrictHostKeyChecking=no \
                  -o ConnectTimeout=5 "${SSH_USER}@${VICTIM}" "$c" 2>/dev/null | head -n1)
            echo "[benign w${id}] SSH(${c%% *}) -> ${out:-<no output>}"
        fi
        sleep "0.$(( RANDOM % 18 + 3 ))"
    done
}

echo "[benign] targeting $VICTIM for ${DURATION}s with ${WORKERS} workers (varied content)"
for i in $(seq 1 "$WORKERS"); do
    worker "$i" &
done
wait
echo "[benign] done"
