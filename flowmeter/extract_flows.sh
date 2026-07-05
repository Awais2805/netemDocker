#!/usr/bin/env bash
# Extract CIC-style flows from a netem pcap using the flowmeter image.
# Lives in netemDocker/flowmeter/ but is location-independent (resolves the
# capture dir relative to itself). Output flows_<ts>.csv is keyed to the pcap's
# run timestamp so it pairs with schedule_<ts>.json and flows_labeled_<ts>.csv.
#
#   bash flowmeter/extract_flows.sh                         # newest run_*.pcap
#   bash flowmeter/extract_flows.sh capture/run_<ts>.pcap   # a specific pcap

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CAP_DIR="$(cd "${CAP_DIR:-$SCRIPT_DIR/../capture}" && pwd)"
IMAGE="${FLOWMETER_IMAGE:-flowmeter:latest}"

if [ "${1:-}" != "" ]; then
    PCAP_PATH="$1"
else
    PCAP_PATH="$(ls -t "${CAP_DIR}"/run_*.pcap 2>/dev/null | head -1 || true)"
fi
[ -n "${PCAP_PATH:-}" ] || { echo "[extract] no pcap found in ${CAP_DIR}/" >&2; exit 1; }
[ -f "$PCAP_PATH" ] || { echo "[extract] not a file: ${PCAP_PATH}" >&2; exit 1; }

PCAP="$(basename "$PCAP_PATH")"
TS="${PCAP#run_}"; TS="${TS%.pcap}"
OUT="flows_${TS}.csv"

echo "[extract] pcap  : ${PCAP}"
echo "[extract] image : ${IMAGE}"
echo "[extract] out   : ${CAP_DIR}/${OUT}"

docker run --rm -v "${CAP_DIR}:/capture" "$IMAGE" \
    cicflowmeter -f "/capture/${PCAP}" -c "/capture/${OUT}"

rows="$(( $(wc -l < "${CAP_DIR}/${OUT}") - 1 ))"
echo "[extract] done: ${rows} flows -> ${CAP_DIR}/${OUT}"
