#!/usr/bin/env sh
set -eu

FLAGS="./assembler -http-session-tracking -skipchecksum"

if [ -n "${PCAP_OVER_IP:-}" ]; then
  echo "Live capture mode: PCAP-over-IP -> ${PCAP_OVER_IP}"
  FLAGS="${FLAGS} -pcap-over-ip ${PCAP_OVER_IP}"
else
  echo "PCAP file mode: watching ${TRAFFIC_DIR_DOCKER:-/traffic}"
  FLAGS="${FLAGS} -dir ${TRAFFIC_DIR_DOCKER:-/traffic}"
fi

exec ${FLAGS}
