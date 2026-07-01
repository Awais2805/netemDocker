#!/usr/bin/env bash
# Benign traffic generator script: uses paced HTTP browsing + occasional SSH logins 
# against the victim. Goal is to generate a realistic benign traffic baseline in the capture. 

set -u

VICTIM="${VICTIM:-172.30.0.10}"
DURATION="${1:-60}"  
SSH_USER="victimuser"
SSH_PASS="password123"

PATHS=("/" "/index.html" "/index.nginx-debian.html" "/about" "/contact" "/missing")

end=$(( $(date +%s) + DURATION ))
echo "[bengin] targeting victim at $VICTIM for $DURATION seconds"

while [ "$(date +%s)" -lt "$end" ]; do
    roll=$(( RANDOM % 100 ))
    if [ "$roll" -lt 85 ]; then                       # ~85% HTTP GETs
        p="${PATHS[$RANDOM % ${#PATHS[@]}]}"
        code=$(curl -s -o /dev/null -w '%{http_code}' "http://${VICTIM}${p}")
        echo "[benign] GET ${p} -> ${code}"
    else                                              # ~15% SSH logins
        out=$(sshpass -p "$SSH_PASS" ssh -o StrictHostKeyChecking=no \
              -o ConnectTimeout=5 "${SSH_USER}@${VICTIM}" \
              'uptime; ls /' 2>/dev/null | head -n1)
        echo "[benign] SSH login -> ${out:-<no output>}"
    fi
    sleep "0.$(( RANDOM % 18 + 3 ))"     # sleep for 0.3-2.0 seconds between requests - pacing enforcer             
done

echo "[benign] done"