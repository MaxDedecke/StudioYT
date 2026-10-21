import os
import json
from typing import List, Dict, Any

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECTS_DIR = os.path.join(BASE_DIR, "projects")
ARTWORK_POOL_DIR = os.path.join(BASE_DIR, "artwork_pool")
TRASH_DIR = os.path.join(BASE_DIR, "trash")
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")
DB_FILE = os.path.join(BASE_DIR, "flyt.db")

os.makedirs(PROJECTS_DIR, exist_ok=True)
os.makedirs(ARTWORK_POOL_DIR, exist_ok=True)
os.makedirs(TRASH_DIR, exist_ok=True)

FFMPEG_PATH = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Packages\Gyan.FFmpeg.Essentials_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.1-essentials_build\bin\ffmpeg.exe")
if not os.path.exists(FFMPEG_PATH):
    FFMPEG_PATH = "ffmpeg"

def get_config() -> Dict[str, Any]:
    default_cfg = {
        "gdrive_path": "",
        "gemini_api_key": "",
        "hf_api_key": "",
        "used_artwork_hashes": [],
        "completed_projects": []
    }
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                default_cfg.update(data)
                return default_cfg
        except Exception:
            pass
    return default_cfg

def auto_detect_gdrive() -> str:
    cfg = get_config()
    current = cfg.get("gdrive_path", "").strip()
    if current and os.path.exists(current):
        return current
    
    candidates = [
        r"G:\Meine Ablage\Beats",
        r"G:\Meine Ablage\beats",
        r"G:\My Drive\Beats",
        r"G:\My Drive\beats",
        r"G:\Beats",
        r"G:\beats",
        os.path.expanduser(r"~\Google Drive\Beats"),
        os.path.expanduser(r"~\Google Drive\beats"),
        r"H:\Meine Ablage\Beats",
        r"H:\My Drive\Beats"
    ]
    for c in candidates:
        if os.path.exists(c):
            cfg["gdrive_path"] = c
            save_config(cfg)
            return c
    return current

def save_config(cfg: Dict[str, Any]):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
    except Exception as e:
        print("[Config] Error saving config:", e)
