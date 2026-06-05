#!/usr/bin/env sh
set -eu

set -- ./assembler -http-session-tracking -skipchecksum

if [ -n "${PCAP_OVER_IP:-}" ]; then
  echo "Live capture mode: PCAP-over-IP -> ${PCAP_OVER_IP}"
  set -- "$@" -pcap-over-ip "${PCAP_OVER_IP}"
else
  echo "PCAP file mode: watching ${TRAFFIC_DIR_DOCKER:-/traffic}"
  set -- "$@" -dir "${TRAFFIC_DIR_DOCKER:-/traffic}"
fi

exec "$@"
