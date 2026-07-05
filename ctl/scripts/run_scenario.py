#!/usr/bin/env python3
"""Seeded, parameterized netem generator — produces independent draws for the
cross-run test. Same attack families as run A; the seed randomizes ordering,
gap timing, benign worker count, and per-attack parameters. Run B = a seed you
did not use for A (e.g. --seed 2)."""

import argparse
import json
import random
import subprocess
import time
from datetime import datetime

VICTIM_IP = "172.30.0.10"
ATTACKER_IP = "172.30.0.99"
WS_IP = "172.30.0.20"

CAP_SECONDS = 2700
END_MARGIN = 150
GAP_MIN, GAP_MAX = 45, 120     # randomized benign-only gap per bout

ROTATION = [
    ("portscan",     "PortScan"),
    ("dos_syn",      "DoS-SYN"),
    ("bruteforce",   "SSH-BruteForce"),
    ("portscan_svc", "PortScan-Svc"),
    ("dos_slow",     "DoS-Slowloris"),
]


def params_for(family, rng):
    if family == "dos_syn":
        return {"DOS_COUNT": str(rng.choice([1500, 2000, 2500, 3000, 3500])),
                "DOS_INTERVAL": "u" + str(rng.choice([300, 400, 500, 600, 800]))}
    if family == "dos_slow":
        return {"SLOW_SOCKETS": str(rng.choice([100, 150, 200, 300])),
                "SLOW_SLEEP": str(rng.choice([10, 15, 20])),
                "SLOW_DURATION": str(rng.choice([30, 40, 50, 60]))}
    if family == "portscan":
        return {"SCAN_PORTS": rng.choice(["1-1024", "1-2048", "20-1000", "1-500,3000-4000"])}
    if family == "portscan_svc":
        return {"SCAN_PORTS": rng.choice(["21,22,80,443,3306,8080",
                                          "22,80,443,8000,8080,9000",
                                          "21,22,25,80,110,443"])}
    if family == "bruteforce":
        return {"WORDLIST": "/scripts/passwords_b.txt"}
    return {}


def dexec(*args, detach=False, env=None):
    cmd = ["docker", "exec"] + (["-d"] if detach else [])
    for k, v in (env or {}).items():
        cmd += ["-e", f"{k}={v}"]
    cmd += list(args)
    subprocess.run(cmd, check=False)


def now():
    return time.time()


def run_attack(family, label, env, windows):
    print(f"[orchestrator] >>> {family} {env}")
    start = now()
    dexec("attacker", "bash", "/scripts/attacks.sh", family, VICTIM_IP, env=env)
    end = now()
    windows.append({
        "label": label, "family": family,
        "src_ip": ATTACKER_IP, "dst_ip": VICTIM_IP, "params": env,
        "start_epoch": start, "end_epoch": end,
        "start_utc": datetime.fromtimestamp(start).isoformat(),
        "end_utc": datetime.fromtimestamp(end).isoformat(),
    })
    print(f"[orchestrator] <<< {family} ({end - start:.2f}s)")


def main():
    ap = argparse.ArgumentParser(description="netem seeded generator")
    ap.add_argument("--seed", type=int, required=True,
                    help="run seed; use a value NOT used for run A (e.g. 2)")
    ap.add_argument("--cap_seconds", type=int, default=CAP_SECONDS)
    args = ap.parse_args()
    rng = random.Random(args.seed)

    windows = []
    cap_start = now()
    workers = rng.choice([3, 4, 5])

    run_ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    pcap = f"/capture/run_{run_ts}.pcap"
    schedule_path = f"/capture/schedule_{run_ts}.json"

    print(f"[orchestrator] seed={args.seed} cap={args.cap_seconds}s workers={workers}")
    print(f"[orchestrator] capture -> {pcap}")
    # generous safety cap only; tcpdump is stopped explicitly when the run ends
    dexec("cap", "timeout", "14400", "tcpdump", "-i", "eth0",
          "-w", pcap, detach=True)
    time.sleep(2)

    print(f"[orchestrator] benign bed on ws ({workers} workers, streaming)")
    benign_proc = subprocess.Popen(
        ["docker", "exec", "ws", "bash", "/scripts/benign.sh",
         str(args.cap_seconds - 5), str(workers)])

    time.sleep(rng.randint(GAP_MIN, GAP_MAX))

    queue, i = [], 0
    while now() - cap_start < args.cap_seconds - END_MARGIN:
        if not queue:
            queue = ROTATION[:]
            rng.shuffle(queue)
        family, label = queue.pop()
        run_attack(family, label, params_for(family, rng), windows)
        i += 1
        if now() - cap_start < args.cap_seconds - END_MARGIN:
            time.sleep(rng.randint(GAP_MIN, GAP_MAX))

    remaining = args.cap_seconds - (now() - cap_start)
    if remaining > 0:
        print(f"[orchestrator] {i} bouts done; waiting {remaining:.0f}s for capture")
        time.sleep(remaining + 3)

    if benign_proc.poll() is None:
        benign_proc.terminate()

    # stop capture cleanly (SIGINT lets tcpdump flush + close the pcap)
    print("[orchestrator] stopping capture")
    dexec("cap", "pkill", "-INT", "tcpdump")
    time.sleep(3)

    schedule = {
        "run_ts": run_ts, "seed": args.seed, "pcap": pcap,
        "capture_start_epoch": cap_start, "capture_end_epoch": now(),
        "victim_ip": VICTIM_IP, "attacker_ip": ATTACKER_IP, "benign_ip": WS_IP,
        "attack_windows": windows,
    }
    with open(schedule_path, "w") as f:
        json.dump(schedule, f, indent=2)
    print(f"[orchestrator] wrote {schedule_path} ({len(windows)} windows)")


if __name__ == "__main__":
    main()
