# Tulip Services

Traffic analysis backend for AD CTF tooling. Ingests PCAPs, stores flows in TimescaleDB, exposes a Flask REST API.

## Architecture

```
PCAP dir ──► assembler (Go) ──► TimescaleDB
                │                    ▲
                ├── converters (Python child processes)
                └── flag/flagid tagging

eve.json ──► enricher (Go) ──► Suricata signature tags

flagids.py ──► scoreboard API ──► flag_id table

Flask API (webservice.py) ◄── React frontend
```

## Docker services

| Service | Role |
|---------|------|
| `timescale` | TimescaleDB with Tulip schema |
| `assembler` | PCAP watcher, TCP/UDP reassembly, tagging |
| `enricher` | Suricata `eve.json` → flow signatures |
| `suricata` | PCAP replay IDS (Glitch overlay only) |
| `api` | Flask REST API |
| `frontend` | React UI on port 3000 |
| `flagids` | Scoreboard flagid scraper |
| `gateway` | Exploit management UI on port 8000 |

## API endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/ping` | Health check |
| `POST` | `/query` | Search flows (regex, IP, port, time, tags) |
| `GET` | `/flow/<id>` | Full flow with items |
| `GET` | `/services` | Service list from config |
| `GET` | `/tick_info` | CTF tick configuration |
| `GET` | `/stats` | Per-tick statistics |
| `GET` | `/tags` | Available tags |
| `POST` | `/star` | Star/unstar a flow |
| `GET` | `/to_python_request/<id>` | Export as Python requests |
| `GET` | `/to_pwn/<id>` | Export as pwntools |

## Configuration

Environment variables (see `.env.glitch.example` for Glitch defaults):

- `TULIP_SERVICES` — `port name` lines for service tagging
- `VM_IP`, `GAME_ROUTER_IP` — Glitch network layout
- `FLAG_REGEX`, `TICK_START`, `TICK_LENGTH`, `FLAG_LIFETIME`
- `CONVERTER_DEFAULT`, `TULIP_CONVERTERS` — protocol decoder pipelines
- `FLAGID_ENDPOINT`, `FLAGID_SCRAPE`, `FLAGID_MODE` — flagid ingestion

Service definitions are loaded in `api/configurations.py` from env at startup.

## Glitch deployment

```bash
cp .env.glitch.example .env
./start-glitch.sh
```

Uses `docker-compose.yml` + `docker-compose.glitch.yml` overlay which enables converters, Suricata, and Glitch flagid scraping.
