import os
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from backend.config import get_config, save_config, auto_detect_gdrive, PROJECTS_DIR
from backend.services.drive_service import sync_project_to_drive

router = APIRouter(prefix="/api", tags=["config"])

class ConfigUpdateRequest(BaseModel):
    gdrive_path: Optional[str] = None
    hf_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None

class SyncRequest(BaseModel):
    project: Optional[str] = None

@router.get("/config")
def read_config():
    cfg = get_config()
    if not cfg.get("gdrive_path"):
        auto_detect_gdrive()
        cfg = get_config()
    return cfg

@router.post("/config")
def update_config(data: ConfigUpdateRequest):
    cfg = get_config()
    if data.gdrive_path is not None:
        cfg["gdrive_path"] = data.gdrive_path.strip().strip('"').strip("'")
    if data.hf_api_key is not None:
        cfg["hf_api_key"] = data.hf_api_key.strip()
    if data.gemini_api_key is not None:
        cfg["gemini_api_key"] = data.gemini_api_key.strip()
    save_config(cfg)
    return {"success": True, "config": cfg}

@router.post("/sync")
def sync_drive(data: SyncRequest):
    project_name = data.project
    if project_name:
        ok, res = sync_project_to_drive(project_name)
    else:
        ok = True
        res = []
        if os.path.exists(PROJECTS_DIR):
            for p in os.listdir(PROJECTS_DIR):
                if os.path.isdir(os.path.join(PROJECTS_DIR, p)):
                    s_ok, _ = sync_project_to_drive(p)
                    if s_ok:
                        res.append(p)
    return {"success": ok, "result": res}
