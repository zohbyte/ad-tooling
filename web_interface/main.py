from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, status
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.security import APIKeyHeader
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pathlib import Path
from typing import List, Optional
import subprocess
import uvicorn
import os
import re

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = Path(__file__).resolve().parent / "static"
WORKSPACES_ROOT = Path(os.environ.get("WORKSPACES_ROOT", "/workspaces"))
DEFAULT_TEAM = os.environ.get("DEFAULT_TEAM", "exploits")
TULIP_API_BASE = os.environ.get("TULIP_API_BASE", "http://localhost:5000")
GLITCH_API_BASE = os.environ.get("GLITCH_API_BASE", "https://glitch.ad")
GLITCH_NOP_HOST = os.environ.get("GLITCH_NOP_HOST", "10.100.1.1")
API_KEY = os.environ.get("TOOLING_API_KEY", "supersecretkey")
FLAG_REGEX = os.environ.get("FLAG_REGEX", r"[A-Z0-9]{31}=")

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

app = FastAPI(title="AD Tooling Gateway", version="1.1.0")

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class ExploitRunRequest(BaseModel):
    team: str
    workspace: str
    filename: str
    args: Optional[List[str]] = []


class ExploitSaveRequest(BaseModel):
    team: str = DEFAULT_TEAM
    filename: str
    content: str


def verify_api_key(key: Optional[str] = Depends(api_key_header)):
    if key != API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
    return key


def team_path(team: str) -> Path:
    path = (WORKSPACES_ROOT / team).resolve()
    root = WORKSPACES_ROOT.resolve()
    if not str(path).startswith(str(root)):
        raise HTTPException(status_code=403, detail="Invalid team path")
    return path


@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    index = STATIC_DIR / "index.html"
    if not index.exists():
        return HTMLResponse("<h1>Gateway UI missing</h1>", status_code=500)
    return HTMLResponse(index.read_text(encoding="utf-8"))


@app.get("/api/config")
async def public_config():
    return {
        "default_team": DEFAULT_TEAM,
        "nop_host": GLITCH_NOP_HOST,
        "flag_regex": FLAG_REGEX,
        "tulip_url": os.environ.get("TULIP_UI_URL", "http://localhost:3000"),
    }


@app.get("/api/ping")
async def ping(code: Optional[str] = "", api_key: str = Depends(verify_api_key)):
    return {"status": "ok", "code": code}


@app.get("/api/workspaces")
async def list_workspaces(api_key: str = Depends(verify_api_key)):
    if not WORKSPACES_ROOT.exists():
        return []
    return [p.name for p in WORKSPACES_ROOT.iterdir() if p.is_dir()]


@app.get("/api/workspaces/{team}/exploits")
async def list_exploits(team: str, api_key: str = Depends(verify_api_key)):
    path = team_path(team)
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
    return sorted(p.name for p in path.glob("*.py"))


@app.get("/api/workspaces/{team}/exploits/{filename}")
async def get_exploit(team: str, filename: str, api_key: str = Depends(verify_api_key)):
    path = team_path(team) / filename
    if not path.exists() or path.suffix != ".py":
        raise HTTPException(status_code=404, detail="Exploit not found")
    return {"filename": filename, "content": path.read_text(encoding="utf-8")}


@app.put("/api/workspaces/{team}/exploits/{filename}")
async def save_exploit(team: str, filename: str, body: ExploitSaveRequest, api_key: str = Depends(verify_api_key)):
    if not filename.endswith(".py"):
        raise HTTPException(status_code=400, detail="Only .py files allowed")
    path = team_path(team)
    path.mkdir(parents=True, exist_ok=True)
    dest = path / filename
    dest.write_text(body.content, encoding="utf-8")
    return {"status": "ok", "path": str(dest)}


@app.get("/api/exploit-template")
async def get_exploit_template(api_key: str = Depends(verify_api_key)):
    template_path = BASE_DIR / "exploit-template.py"
    if not template_path.exists():
        raise HTTPException(status_code=500, detail="Exploit template missing")
    return {"template": template_path.read_text(encoding="utf-8")}


@app.post("/api/workspaces/{team}/exploits")
async def upload_exploit(team: str, file: UploadFile = File(...), api_key: str = Depends(verify_api_key)):
    path = team_path(team)
    path.mkdir(parents=True, exist_ok=True)

    if not file.filename.endswith(".py"):
        raise HTTPException(status_code=400, detail="Only .py uploads allowed")

    dest = path / file.filename
    contents = await file.read()
    dest.write_bytes(contents)
    return {"status": "ok", "path": str(dest)}


@app.delete("/api/workspaces/{team}/exploits/{filename}")
async def delete_exploit(team: str, filename: str, api_key: str = Depends(verify_api_key)):
    path = team_path(team) / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="Exploit not found")
    path.unlink()
    return {"status": "ok"}


@app.post("/api/exploits/run")
async def run_exploit(request: ExploitRunRequest, api_key: str = Depends(verify_api_key)):
    team_dir = team_path(request.team)
    if request.workspace and request.workspace != request.team:
        team_dir = team_dir / request.workspace
    if not team_dir.exists():
        raise HTTPException(status_code=404, detail="Workspace not found")

    exploit_path = (team_dir / request.filename).resolve()
    if not exploit_path.exists() or exploit_path.suffix != ".py":
        raise HTTPException(status_code=404, detail="Exploit file not found")

    if not str(exploit_path).startswith(str(team_dir.resolve())):
        raise HTTPException(status_code=403, detail="Path traversal attempted")

    cmd = ["python3", str(exploit_path), *request.args]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Exploit execution timed out")

    flags = re.findall(FLAG_REGEX, result.stdout)
    return {
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "flags": flags,
    }


@app.post("/api/tulip/ping")
async def tulip_ping(api_key: str = Depends(verify_api_key)):
    import requests
    try:
        r = requests.get(f"{TULIP_API_BASE}/ping", timeout=5)
        return {"status": r.status_code, "data": r.json() if r.text else {}, "url": f"{TULIP_API_BASE}/ping"}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Tulip API unreachable: {exc}")


@app.get("/api/glitch/flagids")
async def glitch_flagids(api_key: str = Depends(verify_api_key)):
    import requests
    try:
        r = requests.get(f"{GLITCH_API_BASE}/api/flagids", timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Glitch API unreachable: {exc}")


@app.get("/api/glitch/info")
async def glitch_info(api_key: str = Depends(verify_api_key)):
    import requests
    try:
        r = requests.get(f"{GLITCH_API_BASE}/api/info", timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Glitch API unreachable: {exc}")


if __name__ == "__main__":
    uvicorn.run("web_interface.main:app", host="0.0.0.0", port=8000, log_level="info")
