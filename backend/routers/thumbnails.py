import os
import threading
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from backend.config import PROJECTS_DIR, get_config
from backend.services.thumbnail_service import thumbnail_state, start_job, select_variant
from backend.services.drive_service import sync_project_to_drive

router = APIRouter(prefix="/api", tags=["thumbnails"])

class GenerateThumbnailsRequest(BaseModel):
    project: str
    artist: Optional[str] = ""
    count: Optional[int] = 4

class SelectThumbnailRequest(BaseModel):
    project: str
    file: str

@router.get("/thumbnails")
def get_thumbnails(project: str = Query(...)):
    p_dir = os.path.join(PROJECTS_DIR, project)
    if not os.path.isdir(p_dir):
        raise HTTPException(status_code=400, detail="Project not found")
    return thumbnail_state(p_dir, project)

@router.post("/generate_thumbnails")
def generate_thumbnails(data: GenerateThumbnailsRequest):
    project_name = data.project
    p_dir = os.path.join(PROJECTS_DIR, project_name)
    if not os.path.isdir(p_dir):
        raise HTTPException(status_code=400, detail="Project not found")

    artist = (data.artist or "").strip()
    if not artist:
        artist = thumbnail_state(p_dir, project_name).get("default_artist", "")

    count = max(1, min(6, int(data.count or 4)))
    cfg = get_config()
    gemini_key = cfg.get("gemini_api_key", "").strip() or os.environ.get("GEMINI_API_KEY", "").strip()
    hf_key = cfg.get("hf_api_key", "").strip() or os.environ.get("HF_TOKEN", "").strip()

    job = start_job(project_name, p_dir, artist, count, gemini_key, hf_key)
    return {"success": True, "job": job}

@router.post("/select_thumbnail")
def select_thumbnail(data: SelectThumbnailRequest):
    project_name = data.project
    p_dir = os.path.join(PROJECTS_DIR, project_name)
    if not os.path.isdir(p_dir):
        raise HTTPException(status_code=400, detail="Project not found")

    if not select_variant(p_dir, data.file):
        raise HTTPException(status_code=400, detail="Thumbnail not found")

    threading.Thread(target=sync_project_to_drive, args=(project_name,), daemon=True).start()
    return {"success": True}
