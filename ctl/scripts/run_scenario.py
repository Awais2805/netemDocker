#!/usr/bin/env python3

import json
import subprocess
import time
from datetime import datetime

VICTIM_IP = "172.30.0.10"
ATTACKER_IP = "172.30.0.99"
WS_IP = "172.30.0.20"
CAP_SECONDS = 200

RUN_TS = datetime.now().strftime("%Y%m%d_%H%M%S")
PCAP = f"/capture/run_{RUN_TS}.pcap"
SCHEDULE = f"/capture/schedule_{RUN_TS}.json"

def dexec(*args, detach=False):
    cmd = ["docker", "exec"] + (["-d"] if detach else []) + list(args)
    subprocess.run(cmd, check=False)

def now():
    return time.time()


def run_attack(family, label, windows):
    print(f"[orchestrator] >>> {family}")
    start = now()
    dexec("attacker", "bash", "/scripts/attacks.sh", family)
    end = now()
    windows.append({
          "label": label,
        "family": family,
        "src_ip": ATTACKER_IP,
        "dst_ip": VICTIM_IP,
        "start_epoch": start,
        "end_epoch": end,
        "start_utc": datetime.fromtimestamp(start).isoformat(),
        "end_utc": datetime.fromtimestamp(end).isoformat(),
    })
    print(f"[orchestrator] <<< {family} (duration: {end - start:.2f}s)")


def main():
    windows = []
    cap_start = now()

    print(f"[orchestrator] capture -> {PCAP} for {CAP_SECONDS}s (eth0)")
    dexec("cap", "timeout", str(CAP_SECONDS), "tcpdump", "-i", "eth0",
          "-w", PCAP, detach=True)
    time.sleep(2)

    print("[orchestrator] benign traffic on ws")
    dexec("ws", "bash", "/scripts/benign.sh", str(CAP_SECONDS - 5), detach=True)

    time.sleep(18)
    run_attack("portscan",   "PortScan",       windows)
    time.sleep(30)
    run_attack("dos",        "DoS-SYN",        windows)
    time.sleep(30)
    run_attack("bruteforce", "SSH-BruteForce", windows)

    remaining = CAP_SECONDS - (now() - cap_start)
    if remaining > 0:
        print(f"[orchestrator] waiting {remaining:.0f}s for capture to finish")
        time.sleep(remaining + 3)

    schedule = {
        "run_ts": RUN_TS,
        "pcap": PCAP,
        "capture_start_epoch": cap_start,
        "capture_end_epoch": now(),
        "victim_ip": VICTIM_IP,
        "attacker_ip": ATTACKER_IP,
        "benign_ip": WS_IP,
        "attack_windows": windows,
    }
    with open(SCHEDULE, "w") as f:
        json.dump(schedule, f, indent=2)
    print(f"[orchestrator] wrote {SCHEDULE} ({len(windows)} windows)")

if __name__ == "__main__":
    main()