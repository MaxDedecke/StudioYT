import os
import subprocess
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from backend.config import PROJECTS_DIR

router = APIRouter(prefix="/api", tags=["system"])

class OpenFolderRequest(BaseModel):
    project: Optional[str] = None

@router.post("/open_folder")
def open_folder(data: OpenFolderRequest):
    project_name = data.project
    p_dir = os.path.join(PROJECTS_DIR, project_name) if project_name else PROJECTS_DIR
    subprocess.Popen(f'explorer.exe "{p_dir}"')
    return {"success": True}

@router.get("/health")
def health():
    return {"status": "ok", "app": "FLYT Studio Platform"}
