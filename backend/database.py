import sqlite3
import os
import time
from typing import Dict, Any, List, Optional
from backend.config import DB_FILE, PROJECTS_DIR, get_config

def get_db():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    with conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                bpm INTEGER DEFAULT 140,
                key TEXT DEFAULT 'C Minor',
                vibe TEXT DEFAULT '',
                duration_sec REAL DEFAULT 0.0,
                drop_sec REAL DEFAULT 12.0,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL,
                is_completed INTEGER DEFAULT 0,
                is_backed_up INTEGER DEFAULT 0,
                has_mp3 INTEGER DEFAULT 0,
                has_artwork INTEGER DEFAULT 0,
                has_video_loop INTEGER DEFAULT 0,
                has_final_video INTEGER DEFAULT 0,
                has_short_video INTEGER DEFAULT 0,
                has_thumbnail INTEGER DEFAULT 0,
                has_metadata INTEGER DEFAULT 0
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_projects_name ON projects(name)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_projects_completed ON projects(is_completed)")
    conn.close()

def scan_and_sync_projects(analyze_fn, is_backup_fn) -> List[Dict[str, Any]]:
    """Discovers folders in PROJECTS_DIR and updates/creates SQLite records."""
    if not os.path.exists(PROJECTS_DIR):
        return []
    
    cfg = get_config()
    completed_set = set(cfg.get("completed_projects", []))
    
    conn = get_db()
    cursor = conn.cursor()
    now = time.time()
    
    dir_names = set(os.listdir(PROJECTS_DIR))
    
    for name in dir_names:
        p_dir = os.path.join(PROJECTS_DIR, name)
        if not os.path.isdir(p_dir):
            continue
        
        has_mp3 = 1 if os.path.exists(os.path.join(p_dir, "beat.mp3")) else 0
        has_art = 1 if os.path.exists(os.path.join(p_dir, "artwork.jpg")) else 0
        has_loop = 1 if os.path.exists(os.path.join(p_dir, "video_loop.mp4")) else 0
        has_final = 1 if os.path.exists(os.path.join(p_dir, "final_youtube_video.mp4")) else 0
        has_short = 1 if os.path.exists(os.path.join(p_dir, "short_reel_video.mp4")) else 0
        has_thumb = 1 if os.path.exists(os.path.join(p_dir, "thumbnail.jpg")) else 0
        has_meta = 1 if os.path.exists(os.path.join(p_dir, "metadata.md")) else 0
        is_completed = 1 if name in completed_set else 0
        is_backed_up = 1 if is_backup_fn(name) else 0
        
        cursor.execute("SELECT * FROM projects WHERE name = ?", (name,))
        row = cursor.fetchone()
        
        analysis = analyze_fn(p_dir, name, force=False) if has_mp3 else {}
        bpm = analysis.get("bpm", 140)
        key_str = analysis.get("key", "C Minor")
        vibe = analysis.get("vibe", "")
        drop_sec = analysis.get("drop_sec", 12.0)
        duration_sec = analysis.get("duration_sec", 0.0) or analysis.get("duration", 0.0)
        
        if row:
            changed = (
                row["bpm"] != bpm or
                row["key"] != key_str or
                row["has_final_video"] != has_final or
                row["has_short_video"] != has_short or
                row["has_thumbnail"] != has_thumb or
                row["has_artwork"] != has_art or
                row["has_video_loop"] != has_loop or
                row["has_metadata"] != has_meta or
                row["is_completed"] != is_completed or
                row["is_backed_up"] != is_backed_up
            )
            up_time = now if changed else (row["updated_at"] or now)
            cursor.execute("""
                UPDATE projects SET
                    bpm = ?, key = ?, vibe = ?, duration_sec = ?, drop_sec = ?,
                    updated_at = ?, is_completed = ?, is_backed_up = ?,
                    has_mp3 = ?, has_artwork = ?, has_video_loop = ?,
                    has_final_video = ?, has_short_video = ?, has_thumbnail = ?, has_metadata = ?
                WHERE name = ?
            """, (
                bpm, key_str, vibe, duration_sec, drop_sec,
                up_time, is_completed, is_backed_up,
                has_mp3, has_art, has_loop,
                has_final, has_short, has_thumb, has_meta,
                name
            ))
        else:
            created_at = os.path.getctime(p_dir) if os.path.exists(p_dir) else now
            cursor.execute("""
                INSERT INTO projects (
                    name, bpm, key, vibe, duration_sec, drop_sec,
                    created_at, updated_at, is_completed, is_backed_up,
                    has_mp3, has_artwork, has_video_loop,
                    has_final_video, has_short_video, has_thumbnail, has_metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                name, bpm, key_str, vibe, duration_sec, drop_sec,
                created_at, now, is_completed, is_backed_up,
                has_mp3, has_art, has_loop,
                has_final, has_short, has_thumb, has_meta
            ))
            
    conn.commit()
    conn.close()

def get_all_projects(include_completed=False) -> List[Dict[str, Any]]:
    conn = get_db()
    cursor = conn.cursor()
    if include_completed:
        cursor.execute("SELECT * FROM projects ORDER BY updated_at DESC")
    else:
        cursor.execute("SELECT * FROM projects WHERE is_completed = 0 ORDER BY updated_at DESC")
    rows = cursor.fetchall()
    projects = [dict(r) for r in rows]
    conn.close()
    return projects

def mark_project_completed(name: str, completed: bool = True):
    conn = get_db()
    with conn:
        conn.execute("UPDATE projects SET is_completed = ?, updated_at = ? WHERE name = ?", (1 if completed else 0, time.time(), name))
    conn.close()

def update_project_audio_info(name: str, bpm: int, key_str: str, vibe: Optional[str] = None):
    conn = get_db()
    now = time.time()
    with conn:
        if vibe:
            conn.execute("UPDATE projects SET bpm = ?, key = ?, vibe = ?, updated_at = ? WHERE name = ?", (bpm, key_str, vibe, now, name))
        else:
            conn.execute("UPDATE projects SET bpm = ?, key = ?, updated_at = ? WHERE name = ?", (bpm, key_str, now, name))
    conn.close()

def delete_project_record(name: str):
    conn = get_db()
    with conn:
        conn.execute("DELETE FROM projects WHERE name = ?", (name,))
    conn.close()
