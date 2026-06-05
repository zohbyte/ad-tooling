#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
from pathlib import Path

traffic_dir = Path(os.getenv("TULIP_TRAFFIC_DIR", "/traffic"))
dump_pcaps_dir = Path(os.getenv("DUMP_PCAPS", "/traffic"))
tick_length = os.getenv("TICK_LENGTH", 120 * 1000)
flag_lifetime = os.getenv("FLAG_LIFETIME", 5)
start_date = os.getenv("TICK_START", "2018-06-27T13:00:00+02:00")
flag_regex = os.getenv("FLAG_REGEX", r"[A-Z0-9]{31}=")
vm_ip = os.getenv("VM_IP", "10.100.1.1")
game_router_ip = os.getenv("GAME_ROUTER_IP", "10.100.0.1")
visualizer_url = os.getenv("VISUALIZER_URL", "")
auth_password = os.getenv("TULIP_AUTH_PASSWORD", "")
services_file = Path(os.getenv("TULIP_SERVICES_FILE", "/config/services.json"))


def _pseudo_services() -> list[dict]:
    return [
        {"ip": game_router_ip, "port": -1, "name": "game-router"},
        {"ip": vm_ip, "port": -1, "name": "other"},
    ]


def _parse_services_env() -> list[dict]:
    raw = os.getenv("TULIP_SERVICES", "").strip()
    if not raw:
        return []

    services: list[dict] = []
    for line in raw.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        parts = line.split(maxsplit=1)
        addr = parts[0]
        name = parts[1] if len(parts) > 1 else f"service-{addr.split(':')[-1]}"

        if ":" in addr:
            ip, port_str = addr.rsplit(":", 1)
            port = int(port_str)
        else:
            ip = vm_ip
            port = int(addr)

        services.append({"ip": ip, "port": port, "name": name})

    return services


def _parse_services_json() -> list[dict]:
    raw = os.getenv("TULIP_SERVICES_JSON", "").strip()
    if not raw:
        return []
    data = json.loads(raw)
    return [
        {
            "ip": item.get("ip", vm_ip),
            "port": int(item["port"]),
            "name": item["name"],
        }
        for item in data
    ]


def load_user_services() -> list[dict]:
    if not services_file.exists():
        return []
    data = json.loads(services_file.read_text(encoding="utf-8"))
    return [
        {
            "ip": item.get("ip", vm_ip),
            "port": int(item["port"]),
            "name": item["name"],
        }
        for item in data
    ]


def save_user_services(user_services: list[dict]) -> None:
    services_file.parent.mkdir(parents=True, exist_ok=True)
    payload = [
        {"ip": s["ip"], "port": s["port"], "name": s["name"]}
        for s in user_services
        if s["port"] != -1
    ]
    services_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def load_services() -> list[dict]:
    user = load_user_services()
    if user:
        return user + _pseudo_services()

    env_services = _parse_services_json() or _parse_services_env()
    if env_services:
        return env_services + _pseudo_services()

    legacy_helper = """
10.61.5.1:1237 CyberUni 4
10.61.5.1:1236 CyberUni 3
10.61.5.1:1235 CyberUni 1
10.61.5.1:1234 CyberUni 2
10.60.5.1:3003 ClosedSea 1
10.60.5.1:3004 ClosedSea 2
10.62.5.1:5000 Trademark
10.63.5.1:1337 RPN
"""
    legacy = [
        {
            "ip": x.split(" ")[0].split(":")[0],
            "port": int(x.split(" ")[0].split(":")[1]),
            "name": " ".join(x.split(" ")[1:]),
        }
        for x in legacy_helper.strip().split("\n")
    ]
    return legacy + _pseudo_services()


def reload_services() -> list[dict]:
    global services
    services = load_services()
    return services


def list_editable_services() -> list[dict]:
    return [s for s in services if s["port"] != -1]


def add_service(port: int, name: str, ip: str | None = None) -> list[dict]:
    user_services = load_user_services()
    entry = {"ip": ip or vm_ip, "port": port, "name": name.strip()}
    user_services = [s for s in user_services if s["port"] != port]
    user_services.append(entry)
    user_services.sort(key=lambda s: s["port"])
    save_user_services(user_services)
    return reload_services()


def remove_service(port: int) -> list[dict]:
    user_services = [s for s in load_user_services() if s["port"] != port]
    save_user_services(user_services)
    return reload_services()


def resolve_service_tag(ip_dst: str, port_dst: int) -> str:
    for service in services:
        if service["port"] == port_dst and service["port"] != -1:
            if service["ip"] in (ip_dst, vm_ip, game_router_ip):
                return service["name"]

    for service in services:
        if service["ip"] == ip_dst and service["port"] == port_dst:
            return service["name"]

    return "unknown"


services = reload_services()
