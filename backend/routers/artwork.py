import os
import threading
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.config import PROJECTS_DIR
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
