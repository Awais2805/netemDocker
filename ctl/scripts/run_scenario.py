#!/usr/bin/env python3

import json
import subprocess
import time
from datetime import datetime

VICTIM_IP = "172.30.0.10"
ATTACKER_IP = "172.30.0.99"
WS_IP = "172.30.0.20"

CAP_SECONDS = 2700          # ~45 min capture
BENIGN_WORKERS = 4          # concurrent benign loops -> dense benign bed
GAP_SECONDS = 75            # benign-only spacing between attack bouts
SLOW_DURATION = 45          # slowloris bout length (seconds)
END_MARGIN = 150            # stop launching attacks this long before capture ends

# Diverse attack variants, cycled until the capture window runs out.
ROTATION = [
    ("portscan",     "PortScan"),
    ("dos_syn",      "DoS-SYN"),
    ("bruteforce",   "SSH-BruteForce"),
    ("portscan_svc", "PortScan-Svc"),
    ("dos_slow",     "DoS-Slowloris"),
]

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
    dexec("attacker", "bash", "/scripts/attacks.sh", family,
          VICTIM_IP, str(SLOW_DURATION))
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
    print(f"[orchestrator] <<< {family} ({end - start:.2f}s)")


def main():
    windows = []
    cap_start = now()

    print(f"[orchestrator] capture -> {PCAP} for {CAP_SECONDS}s (eth0)")
    dexec("cap", "timeout", str(CAP_SECONDS), "tcpdump", "-i", "eth0",
          "-w", PCAP, detach=True)
    time.sleep(2)

    # Benign bed: launched non-detached so its per-request lines stream to this
    # terminal alongside the [orchestrator]/[attack] output, while the attack
    # loop below keeps running concurrently.
    print(f"[orchestrator] benign bed on ws ({BENIGN_WORKERS} workers, streaming)")
    benign_proc = subprocess.Popen(
        ["docker", "exec", "ws", "bash", "/scripts/benign.sh",
         str(CAP_SECONDS - 5), str(BENIGN_WORKERS)])

    # let the benign bed establish before the first attack
    time.sleep(GAP_SECONDS)

    i = 0
    while now() - cap_start < CAP_SECONDS - END_MARGIN:
        family, label = ROTATION[i % len(ROTATION)]
        run_attack(family, label, windows)
        i += 1
        if now() - cap_start < CAP_SECONDS - END_MARGIN:
            time.sleep(GAP_SECONDS)          # benign-only gap before next bout

    remaining = CAP_SECONDS - (now() - cap_start)
    if remaining > 0:
        print(f"[orchestrator] {i} attack bouts done; "
              f"waiting {remaining:.0f}s for capture to finish")
        time.sleep(remaining + 3)

    if benign_proc.poll() is None:
        benign_proc.terminate()

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
