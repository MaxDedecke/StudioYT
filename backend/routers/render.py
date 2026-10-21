import os
import time
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from backend.config import PROJECTS_DIR
from backend.services.render_service import start_render_pipeline, RENDER_JOBS
from backend.services.audio_service import analyze_beat_audio

router = APIRouter(prefix="/api", tags=["render"])

class RenderRequest(BaseModel):
    project: str
    mode: Optional[str] = "both"  # "both", "main_only", "short_only"
    short_start: Optional[float] = None
    short_duration: Optional[float] = 30.0

@router.get("/render_status")
def get_render_status():
    now = time.time()
    active_any = False
    snapshot = {}
    for k, v in list(RENDER_JOBS.items()):
        if v.get("active"):
            active_any = True
        elif v.get("finished_at") and (now - v["finished_at"] > 12):
            continue
        snapshot[k] = v
    return {"active_any": active_any, "jobs": snapshot}

@router.post("/render")
def trigger_render(data: RenderRequest):
    p_dir = os.path.join(PROJECTS_DIR, data.project)
    if not os.path.isdir(p_dir):
        raise HTTPException(status_code=400, detail="Project not found")

    analysis = analyze_beat_audio(p_dir, data.project, force=False)
    default_drop = analysis.get("drop_sec", 12.0)
    start_sec = float(data.short_start if data.short_start is not None else default_drop)
    dur_sec = float(data.short_duration or 30.0)

    job = start_render_pipeline(data.project, mode=data.mode or "both", short_start=start_sec, short_duration=dur_sec)
    return {"success": True, "async": True, "job": job}
