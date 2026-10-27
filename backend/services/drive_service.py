import os
import shutil
import subprocess
from typing import Tuple, List, Union
from backend.config import PROJECTS_DIR, FFMPEG_PATH, get_config

def get_cloud_project_dirs(project_name: str) -> List[str]:
    cfg = get_config()
    candidates = []
    gdrive = cfg.get("gdrive_path", "").strip().strip('"').strip("'")
    if gdrive and os.path.exists(gdrive):
        candidates.append(os.path.join(gdrive, project_name))

    onedrive_beats = os.path.expanduser(r"~\OneDrive\Beats")
    if os.path.exists(onedrive_beats):
        candidates.append(os.path.join(onedrive_beats, project_name))

    onedrive_root = os.path.expanduser(r"~\OneDrive")
    cand_proj = os.path.join(onedrive_root, project_name)
    if os.path.exists(cand_proj):
        candidates.append(cand_proj)

    res = []
    for d in candidates:
        if os.path.isdir(d) and d not in res:
            res.append(d)
    return res

def sync_artwork_from_drive(project_name: str) -> bool:
    """Checks if the cloud drive (Google Drive / OneDrive) has a newer or updated artwork,
    and syncs it down to local projects/<project>/artwork.jpg if so.
    """
    cloud_dirs = get_cloud_project_dirs(project_name)
    if not cloud_dirs:
        return False

    src_dir = os.path.join(PROJECTS_DIR, project_name)
    if not os.path.isdir(src_dir):
        return False

    art_names = [
        "artwork.jpg", "artwork.png", "artwork.jpeg", "artwork.webp",
        "cover.jpg", "cover.png", "cover.jpeg",
        f"{project_name}.jpg", f"{project_name}.png", f"{project_name}.jpeg"
    ]

    for c_dir in cloud_dirs:
        cloud_art = None
        for name in art_names:
            cand = os.path.join(c_dir, name)
            if os.path.isfile(cand):
                cloud_art = cand
                break

        if not cloud_art:
            continue

        local_art = os.path.join(src_dir, "artwork.jpg")
        needs_pull = False
        if not os.path.isfile(local_art):
            needs_pull = True
        else:
            c_mtime = os.path.getmtime(cloud_art)
            l_mtime = os.path.getmtime(local_art)
            c_size = os.path.getsize(cloud_art)
            l_size = os.path.getsize(local_art)
            if (c_mtime - l_mtime) > 1.0 or (c_size != l_size and abs(c_mtime - l_mtime) > 1.0):
                needs_pull = True

        if needs_pull:
            try:
                if cloud_art.lower().endswith(".jpg") or cloud_art.lower().endswith(".jpeg"):
                    shutil.copy2(cloud_art, local_art)
                else:
                    subprocess.run(
                        [FFMPEG_PATH, "-y", "-i", cloud_art, "-q:v", "2", local_art],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        timeout=15
                    )
                return True
            except Exception as e:
                print(f"Error pulling artwork from cloud for {project_name}: {e}")

    return False

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
