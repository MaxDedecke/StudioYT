import os
import shutil
from typing import Tuple, List, Union
from backend.config import PROJECTS_DIR, get_config

def sync_project_to_drive(project_name: str) -> Tuple[bool, Union[List[str], str]]:
    cfg = get_config()
    gdrive = cfg.get("gdrive_path", "").strip().strip('"').strip("'")
    if not gdrive or not os.path.exists(gdrive):
        return False, "Google Drive Pfad nicht gefunden oder nicht konfiguriert."

    src_dir = os.path.join(PROJECTS_DIR, project_name)
    if not os.path.exists(src_dir):
        return False, "Projektordner existiert nicht."

    dest_dir = os.path.join(gdrive, project_name)
    os.makedirs(dest_dir, exist_ok=True)

    synced_files = []
    for item in os.listdir(src_dir):
        s = os.path.join(src_dir, item)
        d = os.path.join(dest_dir, item)
        if os.path.isfile(s):
            if not os.path.exists(d) or os.path.getsize(s) != os.path.getsize(d):
                shutil.copy2(s, d)
            synced_files.append(item)

    return True, synced_files

def is_project_backed_up(project_name: str) -> bool:
    cfg = get_config()
    gdrive = cfg.get("gdrive_path", "").strip().strip('"').strip("'")
    if not gdrive or not os.path.exists(gdrive):
        return False

    dest_dir = os.path.join(gdrive, project_name)
    if not os.path.exists(dest_dir):
        return False

    src_dir = os.path.join(PROJECTS_DIR, project_name)
    if not os.path.exists(src_dir):
        return True

    local_files = [f for f in os.listdir(src_dir) if os.path.isfile(os.path.join(src_dir, f))]
    if not local_files:
        return False

    for f in local_files:
        s = os.path.join(src_dir, f)
        d = os.path.join(dest_dir, f)
        if not os.path.exists(d):
            return False
        if os.path.getsize(s) != os.path.getsize(d):
            return False

    return True
