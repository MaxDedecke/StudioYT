import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.config import PROJECTS_DIR
from backend.services.metadata_service import generate_metadata_markdown
from backend.services.drive_service import sync_project_to_drive

router = APIRouter(prefix="/api", tags=["metadata"])

class MetadataRequest(BaseModel):
    project: str

class SaveMetadataRequest(BaseModel):
    project: str
    metadata_text: str

@router.post("/regenerate_metadata")
def regenerate_metadata(data: MetadataRequest):
    project_name = data.project
    p_dir = os.path.join(PROJECTS_DIR, project_name)
    if not os.path.isdir(p_dir):
        raise HTTPException(status_code=400, detail="Project not found")

    meta_text = generate_metadata_markdown(project_name, p_dir=p_dir, force_refresh=True)
    with open(os.path.join(p_dir, "metadata.md"), "w", encoding="utf-8") as f:
        f.write(meta_text)

    try:
        sync_project_to_drive(project_name)
    except Exception:
        pass

    return {"success": True, "project": project_name, "metadata_text": meta_text}

@router.post("/save_metadata")
def save_metadata(data: SaveMetadataRequest):
    project_name = data.project
    p_dir = os.path.join(PROJECTS_DIR, project_name)
    if not os.path.isdir(p_dir):
        raise HTTPException(status_code=400, detail="Project not found")

    with open(os.path.join(p_dir, "metadata.md"), "w", encoding="utf-8") as f:
        f.write(data.metadata_text)

    try:
        sync_project_to_drive(project_name)
    except Exception:
        pass

    return {"success": True, "project": project_name}
