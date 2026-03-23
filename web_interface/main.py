from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
from pathlib import Path
from typing import List, Optional
import subprocess
import uvicorn
import os

BASE_DIR = Path(__file__).resolve().parent.parent
WORKSPACES_ROOT = Path(os.environ.get("WORKSPACES_ROOT", "/root/workspaces"))
TULIP_API_BASE = os.environ.get("TULIP_API_BASE", "http://localhost:3000/api")
API_KEY = os.environ.get("TOOLING_API_KEY", "supersecretkey")

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

app = FastAPI(title="AD Tooling Gateway", version="1.0.0")

class ExploitRunRequest(BaseModel):
    team: str
    workspace: str
    filename: str
    args: Optional[List[str]] = []


def verify_api_key(key: Optional[str] = Depends(api_key_header)):
    if key != API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
    return key


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
    team_path = WORKSPACES_ROOT / team
    if not team_path.exists():
        raise HTTPException(status_code=404, detail="Team workspace not found")
    return [p.name for p in team_path.glob("*.py")]


@app.get("/api/exploit-template")
async def get_exploit_template(api_key: str = Depends(verify_api_key)):
    template_path = BASE_DIR / "exploit-template.py"
    if not template_path.exists():
        raise HTTPException(status_code=500, detail="Exploit template missing")
    return {"template": template_path.read_text(encoding="utf-8")}


@app.post("/api/workspaces/{team}/exploits")
async def upload_exploit(team: str, file: UploadFile = File(...), api_key: str = Depends(verify_api_key)):
    team_path = WORKSPACES_ROOT / team
    team_path.mkdir(parents=True, exist_ok=True)

    if not file.filename.endswith(".py"):
        raise HTTPException(status_code=400, detail="Only .py uploads allowed")

    dest = team_path / file.filename
    contents = await file.read()
    dest.write_bytes(contents)
    return {"status": "ok", "path": str(dest)}


@app.post("/api/exploits/run")
async def run_exploit(request: ExploitRunRequest, api_key: str = Depends(verify_api_key)):
    team_path = WORKSPACES_ROOT / request.team / request.workspace
    if not team_path.exists():
        raise HTTPException(status_code=404, detail="Workspace not found")

    exploit_path = (team_path / request.filename).resolve()
    if not exploit_path.exists() or exploit_path.suffix != ".py":
        raise HTTPException(status_code=404, detail="Exploit file not found")

    if not str(exploit_path).startswith(str(team_path)):
        raise HTTPException(status_code=403, detail="Path traversal attempted")

    cmd = ["python", str(exploit_path), *request.args]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    except subprocess.TimeoutExpired as exc:
        raise HTTPException(status_code=504, detail="Exploit execution timed out")

    return {
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


@app.post("/api/tulip/ping")
async def tulip_ping(api_key: str = Depends(verify_api_key)):
    import requests
    try:
        r = requests.get(f"{TULIP_API_BASE}/ping", timeout=5)
        return {"status": r.status_code, "data": r.json() if r.text else {}, "url": f"{TULIP_API_BASE}/ping"}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Tulip API unreachable: {exc}")


if __name__ == "__main__":
    uvicorn.run("web_interface.main:app", host="0.0.0.0", port=8000, log_level="info")
