import os
import re
import time
import subprocess
import threading
from typing import Dict, Any, Tuple
from backend.config import BASE_DIR, PROJECTS_DIR, FFMPEG_PATH
from backend.services.audio_service import format_mmss, get_audio_duration, analyze_beat_audio
from backend.services.drive_service import sync_project_to_drive

RENDER_JOBS: Dict[str, Dict[str, Any]] = {}
RENDER_LOCK = threading.Lock()

def run_ffmpeg_tracked(cmd: list, target_duration: float, job: Dict[str, Any], stage_prefix: str, weight_start: float, weight_end: float) -> Tuple[bool, str]:
    full_cmd = [cmd[0], "-nostdin", "-y", "-progress", "pipe:1", "-nostats"] + [c for c in cmd[1:] if c not in ("-y", "-nostdin")]
    proc = subprocess.Popen(
        full_cmd,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1
    )
    cur_sec = 0.0
    tail_lines = []
    try:
        for line in proc.stdout:
            sline = line.strip()
            if sline:
                tail_lines.append(sline)
                if len(tail_lines) > 25:
                    tail_lines.pop(0)

            if sline.startswith("out_time_us=") or sline.startswith("out_time_ms="):
                val_str = sline.split("=", 1)[1].strip()
                if val_str.lstrip("-").isdigit():
                    us = int(val_str)
                    if us > 0:
                        cur_sec = us / 1_000_000.0
                        stage_pct = min(99, max(0, int((cur_sec / max(1.0, target_duration)) * 100)))
                        overall_pct = int(weight_start + (stage_pct / 100.0) * (weight_end - weight_start))
                        job[f"{stage_prefix}_percent"] = stage_pct
                        job["percent"] = min(99, max(job.get("percent", 0), overall_pct))
                        job["current_time_str"] = f"{format_mmss(cur_sec)} / {format_mmss(target_duration)}"

            elif sline.startswith("speed="):
                spd_str = sline.split("=", 1)[1].strip()
                job["speed"] = spd_str
                spd_num = spd_str.replace("x", "").strip()
                try:
                    spd_f = float(spd_num)
                    if spd_f > 0.05 and cur_sec > 0:
                        rem_sec = max(0, int((target_duration - cur_sec) / spd_f))
                        job["eta_str"] = f"~{rem_sec}s"
                except Exception:
                    pass

            elif sline == "progress=end":
                job[f"{stage_prefix}_percent"] = 100
                job["percent"] = int(weight_end)
                job["current_time_str"] = f"{format_mmss(target_duration)} / {format_mmss(target_duration)}"
                break
    except Exception as e:
        print("[run_ffmpeg_tracked] error:", e)

    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        try:
            proc.kill()
            proc.wait(timeout=2)
        except Exception:
            pass

    return proc.returncode == 0 or proc.returncode is None, "\n".join(tail_lines)

def build_main_video_cmd(p_dir: str) -> list:
    mp3_path = os.path.join(p_dir, "beat.mp3")
    output_video = os.path.join(p_dir, "final_youtube_video.mp4")
    video_loop = os.path.join(p_dir, "video_loop.mp4")
    artwork_path = os.path.join(p_dir, "artwork.jpg")
    thumb_path = os.path.join(p_dir, "thumbnail.jpg")
    img_source = thumb_path if os.path.exists(thumb_path) else artwork_path

    if os.path.exists(video_loop):
        return [
            FFMPEG_PATH, "-y",
            "-stream_loop", "-1", "-i", video_loop,
            "-i", mp3_path,
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-c:v", "libx264", "-preset", "veryfast",
            "-vf", "scale=2560:1440:force_original_aspect_ratio=decrease,pad=2560:1440:(ow-iw)/2:(oh-ih)/2:black,setsar=1",
            "-c:a", "aac", "-b:a", "320k",
            "-pix_fmt", "yuv420p",
            "-shortest",
            "-movflags", "+faststart",
            output_video
        ]
    else:
        # Reines Bild (Brand-Thumbnail oder Artwork) + Beat ohne künstliche Effekte
        return [
            FFMPEG_PATH, "-y",
            "-loop", "1", "-r", "30", "-i", img_source,
            "-i", mp3_path,
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-c:v", "libx264", "-preset", "veryfast", "-tune", "stillimage",
            "-vf", "scale=2560:1440:force_original_aspect_ratio=decrease,pad=2560:1440:(ow-iw)/2:(oh-ih)/2:black,setsar=1",
            "-c:a", "aac", "-b:a", "320k",
            "-pix_fmt", "yuv420p",
            "-shortest",
            "-movflags", "+faststart",
            output_video
        ]

def build_short_video_cmd(p_dir: str, beat_duration: float, short_start: float = 12.0, short_duration: float = 30.0) -> Tuple[list, float]:
    mp3_path = os.path.join(p_dir, "beat.mp3")
    output_short = os.path.join(p_dir, "short_reel_video.mp4")
    video_loop = os.path.join(p_dir, "video_loop.mp4")
    artwork_path = os.path.join(p_dir, "artwork.jpg")
    thumb_path = os.path.join(p_dir, "thumbnail.jpg")
    img_source = thumb_path if os.path.exists(thumb_path) else artwork_path

    project_name = os.path.basename(p_dir)
    analysis = analyze_beat_audio(p_dir, project_name, force=False)
    bpm = analysis.get("bpm", 140)
    key_str = analysis.get("key", "C Minor")

    actual_start = float(short_start) if beat_duration > (float(short_start) + 15.0) else 0.0
    clip_dur = min(float(short_duration), max(10.0, beat_duration - actual_start))
    fade_out_st = max(0.0, clip_dur - 2.0)
    af_filter = f"afade=t=in:st=0:d=1.0,afade=t=out:st={fade_out_st:.2f}:d=2.0"

    safe_key = str(key_str).replace(":", "\\:").replace("'", "\\'").strip()
    safe_bpm = str(bpm).replace(":", "\\:").replace("'", "\\'").strip()
    info_text = f"{safe_key.upper()}  ·  {safe_bpm} BPM"
    cta_text = "listen full version now"
    font_bold = "C\\:/Windows/Fonts/segoeuib.ttf" if os.path.exists("C:/Windows/Fonts/segoeuib.ttf") else "C\\:/Windows/Fonts/arialbd.ttf"
    font_reg = "C\\:/Windows/Fonts/segoeui.ttf" if os.path.exists("C:/Windows/Fonts/segoeui.ttf") else "C\\:/Windows/Fonts/arial.ttf"

    draw_info = (
        f"drawtext=fontfile='{font_bold}':text='{info_text}':"
        f"fontcolor=white:fontsize=56:x=(w-text_w)/2:y=h-430:"
        f"shadowcolor=black@0.75:shadowx=0:shadowy=3:"
        f"enable='gte(t,5)':alpha='if(lt(t,5.5),(t-5)/0.5*0.94,0.94)'"
    )
    draw_cta = (
        f"drawtext=fontfile='{font_reg}':text='{cta_text}':"
        f"fontcolor=white:fontsize=46:x=(w-text_w)/2:y=h-350:"
        f"shadowcolor=black@0.75:shadowx=0:shadowy=3:"
        f"enable='gte(t,10)':alpha='if(lt(t,10.5),(t-10)/0.5*0.86,0.86)'"
    )
    vf_9_16 = f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,{draw_info},{draw_cta}"

    if os.path.exists(video_loop):
        cmd = [
            FFMPEG_PATH, "-y",
            "-stream_loop", "-1", "-i", video_loop,
            "-ss", f"{actual_start:.2f}", "-t", f"{clip_dur:.2f}", "-i", mp3_path,
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-t", f"{clip_dur:.2f}",
            "-c:v", "libx264", "-preset", "veryfast",
            "-vf", vf_9_16,
            "-af", af_filter,
            "-c:a", "aac", "-b:a", "320k",
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            output_short
        ]
    else:
        cmd = [
            FFMPEG_PATH, "-y",
            "-loop", "1", "-r", "30", "-i", img_source,
            "-ss", f"{actual_start:.2f}", "-t", f"{clip_dur:.2f}", "-i", mp3_path,
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-t", f"{clip_dur:.2f}",
            "-c:v", "libx264", "-preset", "veryfast", "-tune", "stillimage",
            "-vf", vf_9_16,
            "-af", af_filter,
            "-c:a", "aac", "-b:a", "320k",
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            output_short
        ]
    return cmd, clip_dur

def render_pipeline_worker(project_name: str, mode: str = "both", short_start: float = 12.0, short_duration: float = 30.0):
    p_dir = os.path.join(PROJECTS_DIR, project_name)
    mp3_path = os.path.join(p_dir, "beat.mp3")
    beat_duration = get_audio_duration(mp3_path)

    job = RENDER_JOBS[project_name]
    try:
        # Stage 1: Main 1440p
        if mode in ("both", "main_only"):
            job["stage"] = "main_video"
            job["stage_label"] = "1/3 · Rendere 1440p YouTube Hauptvideo (16:9)..." if mode == "both" else "1/2 · Rendere 1440p YouTube Hauptvideo (16:9)..."
            w_end = 65 if mode == "both" else 92
            cmd_main = build_main_video_cmd(p_dir)
            ok, err_log = run_ffmpeg_tracked(cmd_main, beat_duration, job, "main", 2, w_end)
            if not ok:
                raise RuntimeError(f"Fehler beim Rendern des Hauptvideos: {err_log[-300:]}")
            job["main_percent"] = 100

        # Stage 2: 9:16 Short / Reel
        if mode in ("both", "short_only"):
            job["stage"] = "short_video"
            job["stage_label"] = "2/3 · Rendere 9:16 Short & Instagram Reel (1080x1920)..." if mode == "both" else "1/2 · Rendere 9:16 Short & Instagram Reel (1080x1920)..."
            w_start = 65 if mode == "both" else 4
            w_end = 94
            cmd_short, clip_dur = build_short_video_cmd(p_dir, beat_duration, short_start, short_duration)
            ok, err_log = run_ffmpeg_tracked(cmd_short, clip_dur, job, "short", w_start, w_end)
            if not ok:
                raise RuntimeError(f"Fehler beim Rendern des Short/Reel Videos: {err_log[-300:]}")
            job["short_percent"] = 100

        # Stage 3: Google Drive Sync
        job["stage"] = "sync_drive"
        job["stage_label"] = "Sichere fertige Videos in Google Drive..."
        job["percent"] = 96
        job["eta_str"] = "~1s"
        try:
            sync_project_to_drive(project_name)
        except Exception:
            pass

        job["stage"] = "done"
        if mode == "main_only":
            job["stage_label"] = "1440p YouTube-Video erfolgreich gerendert!"
        elif mode == "short_only":
            job["stage_label"] = "9:16 Short & Reel erfolgreich geschnitten!"
        else:
            job["stage_label"] = "Pipeline abgeschlossen: 1440p Hauptvideo & 9:16 Short/Reel fertig!"
        job["percent"] = 100
        job["eta_str"] = "0s"
        job["active"] = False
        job["finished_at"] = time.time()
    except Exception as e:
        job["stage"] = "error"
        job["stage_label"] = f"Fehler: {str(e)}"
        job["error"] = str(e)
        job["active"] = False
        job["finished_at"] = time.time()

def start_render_pipeline(project_name: str, mode: str = "both", short_start: float = 12.0, short_duration: float = 30.0) -> Dict[str, Any]:
    with RENDER_LOCK:
        existing = RENDER_JOBS.get(project_name)
        if existing and existing.get("active"):
            return existing
        job = {
            "project": project_name,
            "active": True,
            "mode": mode,
            "stage": "starting",
            "stage_label": "Initialisiere FFmpeg Render-Pipeline...",
            "percent": 2,
            "main_percent": 100 if mode == "short_only" else 0,
            "short_percent": 100 if mode == "main_only" else 0,
            "current_time_str": "00:00 / --:--",
            "speed": "-",
            "eta_str": "Berechne...",
            "started_at": time.time(),
            "finished_at": None,
            "error": None
        }
        RENDER_JOBS[project_name] = job
        t = threading.Thread(
            target=render_pipeline_worker,
            args=(project_name, mode, short_start, short_duration),
            daemon=True
        )
        t.start()
        return job
