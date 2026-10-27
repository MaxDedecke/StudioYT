import os
import threading
import subprocess
from fastapi import APIRouter, HTTPException, UploadFile, File, Query, Form
from pydantic import BaseModel
from typing import Optional
from backend.config import PROJECTS_DIR, FFMPEG_PATH
from backend.services.artwork_service import assign_unique_artwork, analyze_artwork_and_build_loop_prompt
from backend.services.thumbnail_service import generate_brand_thumbnails
from backend.services.drive_service import sync_project_to_drive

router = APIRouter(prefix="/api", tags=["artwork"])

class RegenerateArtworkRequest(BaseModel):
    project: str

class AnalyzeArtworkRequest(BaseModel):
    project: str

@router.post("/regenerate_artwork")
def regenerate_artwork(data: RegenerateArtworkRequest):
    project_name = data.project
    p_dir = os.path.join(PROJECTS_DIR, project_name)
    if not os.path.isdir(p_dir):
        raise HTTPException(status_code=400, detail="Project not found")

    try:
        prompt_text = assign_unique_artwork(p_dir, project_name, force_new=True)
        try:
            generate_brand_thumbnails(p_dir)
        except Exception as e:
            print(f"Warning: could not regenerate thumbnails: {e}")
        with open(os.path.join(p_dir, "gemini_prompt.txt"), "w", encoding="utf-8") as f:
            f.write(prompt_text)
        threading.Thread(target=sync_project_to_drive, args=(project_name,), daemon=True).start()
        return {"success": True, "project": project_name, "prompt_text": prompt_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze_artwork")
def analyze_artwork(data: AnalyzeArtworkRequest):
    project_name = data.project
    p_dir = os.path.join(PROJECTS_DIR, project_name)
    art_file = os.path.join(p_dir, "artwork.jpg")
    if not os.path.isfile(art_file):
        raise HTTPException(status_code=400, detail="Artwork not found")

    try:
        prompt_text = analyze_artwork_and_build_loop_prompt(art_file)
        with open(os.path.join(p_dir, "gemini_prompt.txt"), "w", encoding="utf-8") as f:
            f.write(prompt_text)
        threading.Thread(target=sync_project_to_drive, args=(project_name,), daemon=True).start()
        return {"success": True, "project": project_name, "prompt_text": prompt_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload_artwork")
async def upload_artwork(
    file: UploadFile = File(...),
    project: Optional[str] = Query(None),
    project_form: Optional[str] = Form(None, alias="project")
):
    project_name = project or project_form
    if not project_name:
        raise HTTPException(status_code=400, detail="Project parameter missing")

    p_dir = os.path.join(PROJECTS_DIR, project_name)
    if not os.path.isdir(p_dir):
        raise HTTPException(status_code=400, detail="Project not found")

    content = await file.read()
    ext = os.path.splitext(file.filename or "")[1] or ".jpg"
    temp_art = os.path.join(p_dir, f"_temp_upload_art{ext}")
    final_art = os.path.join(p_dir, "artwork.jpg")

    try:
        with open(temp_art, "wb") as f:
            f.write(content)

        # Standardize to pristine JPEG
        cmd = [
            FFMPEG_PATH, "-y",
            "-i", temp_art,
            "-q:v", "2",
            final_art
        ]
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20)
        if proc.returncode != 0 or not os.path.isfile(final_art):
            raise RuntimeError("FFmpeg konnte das hochgeladene Artwork nicht konvertieren")

        # 1. Regenerate brand thumbnails from new artwork
        try:
            generate_brand_thumbnails(p_dir)
        except Exception as e:
            print(f"Warning: could not regenerate thumbnails: {e}")

        # 2. Analyze new image with Gemini Vision to craft tailored micro-movements loop prompt
        prompt_text = ""
        try:
            prompt_text = analyze_artwork_and_build_loop_prompt(final_art)
            with open(os.path.join(p_dir, "gemini_prompt.txt"), "w", encoding="utf-8") as f:
                f.write(prompt_text)
            prompt_mtime_file = os.path.join(p_dir, "thumbnails", "_prompt_art_mtime.txt")
            with open(prompt_mtime_file, "w", encoding="utf-8") as f:
                f.write(str(os.path.getmtime(final_art)))
        except Exception as e:
            print(f"Warning: vision prompt analysis: {e}")

        # 3. Synchronize to cloud drive (Google Drive / OneDrive)
        threading.Thread(target=sync_project_to_drive, args=(project_name,), daemon=True).start()

        mtime = int(os.path.getmtime(final_art))
        return {
            "success": True,
            "project": project_name,
            "prompt_text": prompt_text,
            "artwork_mtime": mtime
        }
    finally:
        if os.path.isfile(temp_art):
            try:
                os.remove(temp_art)
            except Exception:
                pass

