import os
import shutil
import urllib.parse
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from backend.config import PROJECTS_DIR, TRASH_DIR, get_config, save_config
from backend.services.audio_service import analyze_beat_audio
from backend.services.artwork_service import assign_unique_artwork
from backend.services.metadata_service import generate_metadata_markdown
from backend.services.render_service import start_render_pipeline, RENDER_JOBS
from backend.services.drive_service import sync_project_to_drive, is_project_backed_up
from backend.database import scan_and_sync_projects, get_all_projects, mark_project_completed, delete_project_record

router = APIRouter(prefix="/api", tags=["projects"])

class CompleteProjectRequest(BaseModel):
    project: str

class DeleteProjectRequest(BaseModel):
    project: str

@router.get("/projects")
def list_projects(include_completed: bool = False):
    # Scan filesystem and sync into SQLite
    scan_and_sync_projects(analyze_beat_audio, is_project_backed_up)
    records = get_all_projects(include_completed=include_completed)
    
    # Enhance records with live memory render jobs and prompt/metadata texts
    for p in records:
        name = p["name"]
        p_dir = os.path.join(PROJECTS_DIR, name)
        p["render_job"] = RENDER_JOBS.get(name)
        
        # Format duration string
        dur_sec = p.get("duration_sec", 0.0) or 0.0
        dur_m = int(dur_sec // 60)
        dur_s = int(dur_sec % 60)
        p["duration_str"] = f"{dur_m}:{dur_s:02d}" if dur_sec > 0 else "--:--"
        
        # Read prompt & metadata
        p["prompt_text"] = ""
        prompt_file = os.path.join(p_dir, "gemini_prompt.txt")
        if os.path.exists(prompt_file):
            try:
                with open(prompt_file, "r", encoding="utf-8") as f:
                    p["prompt_text"] = f.read()
            except Exception:
                pass
                
        p["metadata_text"] = ""
        meta_file = os.path.join(p_dir, "metadata.md")
        if os.path.exists(meta_file):
            try:
                with open(meta_file, "r", encoding="utf-8") as f:
                    p["metadata_text"] = f.read()
            except Exception:
                pass
                
    return records

@router.post("/upload_mp3")
async def upload_mp3(file: UploadFile = File(...), name: Optional[str] = Query(None)):
    raw_filename = name or file.filename or "beat.mp3"
    filename = urllib.parse.unquote(raw_filename)
    base_name = os.path.splitext(filename)[0]
    safe_name = "".join([c for c in base_name if c.isalnum() or c in ("-", "_")]).strip()
    if not safe_name:
        safe_name = f"beat_{len(os.listdir(PROJECTS_DIR)) + 1}"

    cfg = get_config()
    completed = cfg.get("completed_projects", [])
    if safe_name in completed:
        completed.remove(safe_name)
        cfg["completed_projects"] = completed
        save_config(cfg)

    p_dir = os.path.join(PROJECTS_DIR, safe_name)
    os.makedirs(p_dir, exist_ok=True)

    mp3_path = os.path.join(p_dir, "beat.mp3")
    content = await file.read()
    with open(mp3_path, "wb") as f:
        f.write(content)

    # 1. Assign Artwork
    prompt_text = assign_unique_artwork(p_dir, safe_name, force_new=False)
    with open(os.path.join(p_dir, "gemini_prompt.txt"), "w", encoding="utf-8") as f:
        f.write(prompt_text)

    # 2. Generate Audio Analysis & Metadata
    meta_text = generate_metadata_markdown(safe_name, p_dir=p_dir, force_refresh=True)
    with open(os.path.join(p_dir, "metadata.md"), "w", encoding="utf-8") as f:
        f.write(meta_text)

    # 3. Initial Cloud Sync
    try:
        sync_project_to_drive(safe_name)
    except Exception:
        pass

    # 4. Sync into DB
    scan_and_sync_projects(analyze_beat_audio, is_project_backed_up)

    return {"success": True, "project": safe_name}

@router.post("/upload_video")
async def upload_video(file: UploadFile = File(...), project: str = Query(...)):
    p_dir = os.path.join(PROJECTS_DIR, project)
    if not os.path.isdir(p_dir):
        raise HTTPException(status_code=400, detail="Project not found")

    content = await file.read()
    target_path = os.path.join(p_dir, "video_loop.mp4")
    with open(target_path, "wb") as f:
        f.write(content)

    analysis = analyze_beat_audio(p_dir, project, force=False)
    drop_start = analysis.get("drop_sec", 12.0)

    job = start_render_pipeline(project, mode="both", short_start=drop_start, short_duration=30.0)
    return {"success": True, "async": True, "job": job}

@router.post("/complete_project")
def complete_project(data: CompleteProjectRequest):
    project_name = data.project
    p_dir = os.path.join(PROJECTS_DIR, project_name)
    if not os.path.exists(p_dir):
        raise HTTPException(status_code=400, detail="Project not found")

    try:
        sync_project_to_drive(project_name)
    except Exception:
        pass

    cfg = get_config()
    comp = cfg.get("completed_projects", [])
    if project_name not in comp:
        comp.append(project_name)
        cfg["completed_projects"] = comp
        save_config(cfg)

    mark_project_completed(project_name, True)
    return {"success": True, "project": project_name}

@router.post("/delete_project")
def delete_project(data: DeleteProjectRequest):
    project_name = data.project
    p_dir = os.path.join(PROJECTS_DIR, project_name)
    if os.path.exists(p_dir):
        try:
            sync_project_to_drive(project_name)
        except Exception:
            pass

        dest_trash = os.path.join(TRASH_DIR, project_name)
        if os.path.exists(dest_trash):
            shutil.rmtree(dest_trash, ignore_errors=True)
        shutil.move(p_dir, dest_trash)

    delete_project_record(project_name)
    return {"success": True, "message": "Projekt archiviert."}
