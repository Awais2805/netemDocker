#!/usr/bin/env python3

import csv
import glob
import json
import os
import sys
from datetime import datetime, timezone


def latest(pattern):
    files = sorted(glob.glob(pattern))
    if not files:
        sys.exit(f"no files matching {pattern}")
    return files[-1]


def parse_ts(s):
    return (datetime.strptime(s.strip(), "%Y-%m-%d %H:%M:%S")
            .replace(tzinfo=timezone.utc).timestamp())


def main():
    cap = sys.argv[1] if len(sys.argv) > 1 else "/capture"
    schedule_path = latest(os.path.join(cap, "schedule_*.json"))

    with open(schedule_path, "r") as f:
        schedule = json.load(f)

    # Tie flows/labelled filenames to this run's timestamp so every artefact
    # (pcap / schedule / flows / labelled) shares one <ts> and no run overwrites
    # another. run_ts is written by run_scenario; fall back to the filename.
    ts = schedule.get("run_ts")
    if not ts:
        base = os.path.basename(schedule_path)
        ts = base[len("schedule_"):-len(".json")]

    flows_path = os.path.join(cap, f"flows_{ts}.csv")
    out_path = os.path.join(cap, f"flows_labeled_{ts}.csv")

    attacker = schedule["attacker_ip"]
    windows = schedule["attack_windows"]
    print(f"[Label] schedule : {os.path.basename(schedule_path)}")
    print(f"[Label] flows    : {os.path.basename(flows_path)}")
    print(f"[Label] attacker : {attacker} ({len(windows)} windows)")

    if not os.path.exists(flows_path):
        sys.exit(f"[Label] ABORT: {flows_path} not found — extract this run's pcap first")

    def family_for(ts):
        for w in windows:
            if w["start_epoch"] <= ts <= w["end_epoch"]:
                return w["label"]
        return min(windows, key=lambda w: abs(ts - (w["start_epoch"] + w["end_epoch"]) / 2))["label"]

    counts, n = {}, 0
    with open(flows_path, newline="") as fin, open(out_path, "w", newline="") as fout:
        reader = csv.DictReader(fin)
        writer = csv.DictWriter(fout, fieldnames=reader.fieldnames + ["Family", "Label"])
        writer.writeheader()
        for row in reader:
            n += 1
            if attacker in (row["src_ip"], row["dst_ip"]):
                row["Family"] = family_for(parse_ts(row["timestamp"]))
                row["Label"] = "malicious"
            else:
                row["Family"] = "Benign"
                row["Label"] = "Benign"
            writer.writerow(row)
            counts[row["Family"]] = counts.get(row["Family"], 0) + 1

    print(f"[Label] wrote {out_path} ({n} flows)")
    print("[Label] class balance:")
    for k in sorted(counts):
        print(f"{k:16s} {counts[k]:7d} ({100*counts[k] / n:5.1f}%)")


if __name__ == "__main__":
    main()
