#!/usr/bin/env python3
"""Stream live tcpdump capture to Tulip's PCAP-over-IP listener."""

import argparse
import socket
import subprocess
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description="PCAP-over-IP live capture bridge")
    parser.add_argument("--listen", default="0.0.0.0:1337", help="host:port to listen on")
    parser.add_argument("--interface", default="any", help="tcpdump interface")
    parser.add_argument("--bpf", default="", help="optional tcpdump BPF filter")
    args = parser.parse_args()

    host, port_str = args.listen.rsplit(":", 1)
    port = int(port_str)

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((host, port))
    sock.listen(8)
    print(f"PCAP-over-IP listening on {host}:{port}", flush=True)

    while True:
        conn, addr = sock.accept()
        print(f"Client connected from {addr}", flush=True)
        cmd = ["tcpdump", "-i", args.interface, "-w", "-", "-U", "--immediate-mode"]
        if args.bpf:
            cmd.extend(["-f", args.bpf])
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            assert proc.stdout is not None
            while True:
                chunk = proc.stdout.read(65536)
                if not chunk:
                    break
                conn.sendall(chunk)
        except (BrokenPipeError, ConnectionResetError):
            pass
        finally:
            proc.terminate()
            try:
                proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                proc.kill()
            conn.close()
            print(f"Client disconnected from {addr}", flush=True)


if __name__ == "__main__":
    sys.exit(main())
