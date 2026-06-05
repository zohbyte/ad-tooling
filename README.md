# AD Tooling

Attack-Defense CTF toolkit for **Glitch** vulnbox deployments: **Tulip** traffic analysis + **Gateway** exploit management UI.

## Glitch vulnbox quick start

On your vulnbox (`ssh root@vulnbox.glitch.ad`):

```bash
git clone <this-repo> /opt/ad-tooling
cd /opt/ad-tooling/tulip
cp .env.glitch.example .env
```

Edit `.env`:

1. Set `TEAM_ID` and `VM_IP` (`10.100.<TEAM_ID>.1`)
2. Set `TICK_START` when the game opens
3. Set `TULIP_AUTH_PASSWORD` (Tulip is **not** password-protected unless you set this)
4. Set `TOOLING_API_KEY` for the exploit gateway

**Live capture is the default** — no PCAP directory needed. The `pcap-bridge` container runs `tcpdump` on the host and streams to Tulip via PCAP-over-IP.

Add services from inside Tulip: click **Services** in the header, enter `port` + `name` as you discover them. No `.env` service list required.

Start the full stack:

```bash
chmod +x start-glitch.sh
./start-glitch.sh
```

| URL | Purpose |
|-----|---------|
| `:3000` | Tulip — search traffic, diff flows, export exploits |
| `:8000` | Gateway UI — edit/run exploits, load flagids |

### Traffic capture

**Live (default):** `pcap-bridge` captures on the vulnbox host and streams to Tulip. Optional BPF filter:

```bash
PCAP_BRIDGE_BPF="host 10.100.42.1"   # your vulnbox IP in .env
```

**File mode (fallback):** clear `PCAP_OVER_IP` and set `TRAFFIC_DIR_HOST` to a PCAP dump directory.

### Exploits

Put exploits in `/root/exploits` (mounted as the gateway workspace). Format:

```bash
python3 exploit.py <host> <flagid>
```

Test against NOP from the gateway UI (default host `10.100.1.1`) or on the vulnbox:

```bash
glitch exploit test /root/exploits/exploit.py servicename
glitch exploit throw /root/exploits/exploit.py servicename
```

The gateway UI is for editing and manual testing; `glitch exploit throw` handles automated throwing.

## Components

| Component | Path | Role |
|-----------|------|------|
| Tulip | `tulip/` | PCAP ingest, flag/flagid tagging, traffic search |
| Gateway | `web_interface/` | Exploit editor, runner, Glitch flagid loader |
| Template | `exploit-template.py` | Glitch-compatible exploit scaffold |

## Configuration reference

### Game (Glitch defaults)

| Variable | Default | Meaning |
|----------|---------|---------|
| `TICK_LENGTH` | `120000` | 120s ticks (ms) |
| `FLAG_LIFETIME` | `5` | flags expire after 5 ticks |
| `FLAG_REGEX` | `[A-Z0-9]{31}=` | Glitch flag format |
| `GAME_ROUTER_IP` | `10.100.0.1` | all inbound traffic appears from here |
| `VM_IP` | `10.100.<TEAM_ID>.1` | your vulnbox |
| `FLAGID_ENDPOINT` | `https://glitch.ad/api/flagids` | scoreboard flagids |
| `GLITCH_NOP_HOST` | `10.100.1.1` | NOP team for testing |

### Services

Add via the Tulip UI (**Services** button) or optionally via `TULIP_SERVICES` in `.env`. Stored in `/config/services.json` and persists across restarts.

### Authentication

| Component | Default | How to protect |
|-----------|---------|----------------|
| **Tulip** | Open, no login | Set `TULIP_AUTH_PASSWORD` in `.env` |
| **Gateway** | API key required | Set `TOOLING_API_KEY` in `.env` |

### Converters

Enabled in `docker-compose.glitch.yml` (converters on by default):

| Variable | Example | Meaning |
|----------|---------|---------|
| `CONVERTER_DEFAULT` | `b64decode` | apply to all service ports |
| `TULIP_CONVERTERS` | `8080:b64decode;3000:websockets,b64decode` | per-port pipelines |

## Local development

```bash
cd tulip && cp .env.example .env && docker compose up
```

Gateway only:

```bash
pip install -r web_interface/requirements.txt
export TOOLING_API_KEY=supersecretkey
python -m uvicorn web_interface.main:app --host 0.0.0.0 --port 8000
```

## API

Gateway endpoints (header: `X-API-Key`):

- `GET /` — web UI
- `GET /api/config` — public UI config
- `GET /api/workspaces/{team}/exploits` — list exploits
- `PUT /api/workspaces/{team}/exploits/{file}` — save exploit
- `POST /api/exploits/run` — run with `{team, workspace, filename, args}`
- `GET /api/glitch/flagids` — proxy scoreboard flagids
- `POST /api/tulip/ping` — Tulip health check
