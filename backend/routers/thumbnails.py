import os
import threading
from fastapi import APIRouter, HTTPException, Query, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional
from backend.config import PROJECTS_DIR
from backend.services.thumbnail_service import (
    thumbnail_state,
    select_variant,
    generate_brand_thumbnails,
    save_custom_thumbnail,
    delete_custom_thumbnail,
)
from backend.services.drive_service import sync_project_to_drive

router = APIRouter(prefix="/api", tags=["thumbnails"])

class GenerateThumbnailsRequest(BaseModel):
    project: str
    brand_tag: Optional[str] = "prodbyjmd"
    artist: Optional[str] = None

class SelectThumbnailRequest(BaseModel):
    project: str
    file: str

@router.get("/thumbnails")
def get_thumbnails(project: str = Query(...)):
    p_dir = os.path.join(PROJECTS_DIR, project)
    if not os.path.isdir(p_dir):
        raise HTTPException(status_code=400, detail="Project not found")

    state = thumbnail_state(p_dir, project)
    if not state.get("variants") and os.path.isfile(os.path.join(p_dir, "artwork.jpg")):
        generate_brand_thumbnails(p_dir, brand_tag="prodbyjmd")
        state = thumbnail_state(p_dir, project)

    return state

@router.post("/generate_thumbnails")
def generate_thumbnails(data: GenerateThumbnailsRequest):
    project_name = data.project
    p_dir = os.path.join(PROJECTS_DIR, project_name)
    if not os.path.isdir(p_dir):
        raise HTTPException(status_code=400, detail="Project not found")

    brand_tag = (data.brand_tag or data.artist or "prodbyjmd").strip()
    variants = generate_brand_thumbnails(p_dir, brand_tag=brand_tag)
    threading.Thread(target=sync_project_to_drive, args=(project_name,), daemon=True).start()
    return {"success": True, "brand_tag": brand_tag, "variants": variants}

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

@router.post("/upload_thumbnail")
async def upload_thumbnail(
    file: UploadFile = File(...),
    project: Optional[str] = Query(None),
    project_form: Optional[str] = Form(None, alias="project")
):
    project_name = project or project_form
    if not project_name:
        raise HTTPException(status_code=400, detail="Project parameter is missing")

    p_dir = os.path.join(PROJECTS_DIR, project_name)
    if not os.path.isdir(p_dir):
        raise HTTPException(status_code=400, detail="Project not found")

    content = await file.read()
    ext = os.path.splitext(file.filename or "")[1] or ".jpg"

    res = save_custom_thumbnail(p_dir, content, ext)
    if not res:
        raise HTTPException(status_code=500, detail="Fehler beim Verarbeiten des Thumbnails")

    threading.Thread(target=sync_project_to_drive, args=(project_name,), daemon=True).start()
    return {"success": True, "selected_src": res, "state": thumbnail_state(p_dir, project_name)}

@router.post("/delete_custom_thumbnail")
def remove_custom_thumbnail(data: SelectThumbnailRequest):
    project_name = data.project
    p_dir = os.path.join(PROJECTS_DIR, project_name)
    if not os.path.isdir(p_dir):
        raise HTTPException(status_code=400, detail="Project not found")

    delete_custom_thumbnail(p_dir)
    threading.Thread(target=sync_project_to_drive, args=(project_name,), daemon=True).start()
    return {"success": True, "state": thumbnail_state(p_dir, project_name)}
