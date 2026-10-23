import os
import shutil
import subprocess
import threading
from typing import Dict, Any, List, Optional
from backend.config import FFMPEG_PATH

THUMB_W, THUMB_H = 1280, 720
THUMB_SUBDIR = "thumbnails"
SELECTED_NAME = "thumbnail.jpg"

STYLE_LABELS = {
    "style_1_badge.jpg": "Studio Pill Badge",
    "style_2_lower_bar.jpg": "Cinematic Letterspaced Bar",
    "style_3_corner_rec.jpg": "Session ● REC Tag",
    "style_4_advisory_box.jpg": "Producer Advisory Stamp",
    "style_5_clean_watermark.jpg": "Minimalist Signature"
}

def generate_brand_thumbnails(p_dir: str, brand_tag: str = "prodbyjmd") -> List[str]:
    """Overlays the producer brand onto the beat's artwork in 5 stylish aesthetic variants.
    Runs locally in ~0.5s via FFmpeg with zero external dependencies.
    """
    src_art = os.path.join(p_dir, "artwork.jpg")
    if not os.path.isfile(src_art):
        return []

    out_dir = os.path.join(p_dir, THUMB_SUBDIR)
    os.makedirs(out_dir, exist_ok=True)

    tag = (brand_tag or "prodbyjmd").strip()
    tag_upper = tag.upper()
    tag_spaced = " ".join(list(tag_upper))
    tag_lower = tag.lower()

    font_bold = "C\\:/Windows/Fonts/segoeuib.ttf" if os.path.exists("C:/Windows/Fonts/segoeuib.ttf") else "C\\:/Windows/Fonts/arialbd.ttf"
    font_mono = "C\\:/Windows/Fonts/consolab.ttf" if os.path.exists("C:/Windows/Fonts/consolab.ttf") else font_bold
    font_reg = "C\\:/Windows/Fonts/segoeui.ttf" if os.path.exists("C:/Windows/Fonts/segoeui.ttf") else font_bold

    # 16:9 YouTube Feed Enhancement filter
    base_eq = "scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,eq=contrast=1.06:brightness=-0.01:saturation=1.05"

    styles = [
        (
            "style_1_badge.jpg",
            f"{base_eq},"
            f"drawbox=x=w-270:y=30:w=235:h=46:color=black@0.8:t=fill,"
            f"drawbox=x=w-270:y=30:w=235:h=46:color=white@0.3:t=1,"
            f"drawtext=fontfile='{font_bold}':text='{tag_upper}':fontcolor=white:fontsize=22:x=w-255:y=42,"
            f"drawtext=fontfile='{font_mono}':text='2026':fontcolor=0x38bdf8:fontsize=15:x=w-80:y=45"
        ),
        (
            "style_2_lower_bar.jpg",
            f"{base_eq},"
            f"drawbox=x=(w-380)/2:y=h-90:w=380:h=50:color=black@0.85:t=fill,"
            f"drawbox=x=(w-380)/2:y=h-90:w=380:h=2:color=0xa855f7:t=fill,"
            f"drawtext=fontfile='{font_bold}':text='{tag_spaced}':fontcolor=white:fontsize=22:x=(w-text_w)/2:y=h-76:shadowcolor=black@0.9:shadowx=0:shadowy=2"
        ),
        (
            "style_3_corner_rec.jpg",
            f"{base_eq},"
            f"drawbox=x=w-270:y=h-75:w=235:h=44:color=black@0.85:t=fill,"
            f"drawbox=x=w-270:y=h-75:w=235:h=44:color=0x22c55e@0.5:t=1,"
            f"drawtext=fontfile='{font_mono}':text='● REC':fontcolor=0xef4444:fontsize=15:x=w-255:y=h-61,"
            f"drawtext=fontfile='{font_bold}':text='{tag_lower}':fontcolor=white:fontsize=21:x=w-185:y=h-62"
        ),
        (
            "style_4_advisory_box.jpg",
            f"{base_eq},"
            f"drawbox=x=45:y=h-115:w=220:h=70:color=black@0.9:t=fill,"
            f"drawbox=x=45:y=h-115:w=220:h=70:color=white:t=2,"
            f"drawtext=fontfile='{font_bold}':text='PRODUCED BY':fontcolor=white:fontsize=13:x=60:y=h-105,"
            f"drawtext=fontfile='{font_bold}':text='{tag_upper}':fontcolor=white:fontsize=26:x=60:y=h-86,"
            f"drawtext=fontfile='{font_mono}':text='AUTHENTIC BEAT':fontcolor=0xa1a1aa:fontsize=10:x=60:y=h-58"
        ),
        (
            "style_5_clean_watermark.jpg",
            f"{base_eq},"
            f"drawtext=fontfile='{font_bold}':text='{tag_lower}':fontcolor=white:fontsize=36:x=50:y=40:shadowcolor=black@0.95:shadowx=2:shadowy=2,"
            f"drawtext=fontfile='{font_mono}':text='ORIGINAL INSTRUMENTAL':fontcolor=white@0.75:fontsize=12:x=52:y=82:shadowcolor=black@0.9:shadowx=1:shadowy=1"
        )
    ]

    created = []
    for fname, vf in styles:
        dst = os.path.join(out_dir, fname)
        cmd = [FFMPEG_PATH, "-nostdin", "-y", "-i", src_art, "-vf", vf, "-q:v", "2", "-frames:v", "1", dst]
        try:
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)
            if os.path.isfile(dst):
                created.append(f"{THUMB_SUBDIR}/{fname}")
        except Exception:
            pass

    # Save artwork mtime and brand tag marker
    try:
        with open(os.path.join(out_dir, "_artwork_mtime.txt"), "w", encoding="utf-8") as f:
            f.write(str(os.path.getmtime(src_art)))
        with open(os.path.join(out_dir, "_brand_tag.txt"), "w", encoding="utf-8") as f:
            f.write(tag)
    except Exception:
        pass

    # Ensure thumbnail.jpg is updated to the current artwork (using previous selection or style 1)
    sel_path = os.path.join(p_dir, SELECTED_NAME)
    chosen_file = None
    marker = os.path.join(out_dir, "_selected.txt")
    if os.path.isfile(marker):
        try:
            with open(marker, "r", encoding="utf-8") as f:
                prev_name = os.path.basename(f.read().strip())
                cand = os.path.join(out_dir, prev_name)
                if os.path.isfile(cand):
                    chosen_file = cand
        except Exception:
            pass

    if not chosen_file and created:
        first_variant = os.path.join(out_dir, "style_1_badge.jpg")
        if os.path.isfile(first_variant):
            chosen_file = first_variant

    if chosen_file and os.path.isfile(chosen_file):
        shutil.copyfile(chosen_file, sel_path)
        try:
            with open(os.path.join(out_dir, "_selected.txt"), "w", encoding="utf-8") as f:
                f.write(f"{THUMB_SUBDIR}/{os.path.basename(chosen_file)}")
        except Exception:
            pass

    return created

def list_variants(p_dir: str) -> List[str]:
    d = os.path.join(p_dir, THUMB_SUBDIR)
    if not os.path.isdir(d):
        return []
    files = sorted([f for f in os.listdir(d) if f.lower().endswith(".jpg") and not f.startswith("_")])
    return [f"{THUMB_SUBDIR}/{f}" for f in files]

def thumbnail_state(p_dir: str, project_name: str) -> Dict[str, Any]:
    src_art = os.path.join(p_dir, "artwork.jpg")
    out_dir = os.path.join(p_dir, THUMB_SUBDIR)
    mtime_file = os.path.join(out_dir, "_artwork_mtime.txt")

    # Auto-refresh thumbnail styles if artwork.jpg is newer than thumbnails
    needs_refresh = False
    if os.path.isfile(src_art):
        if not os.path.isdir(out_dir) or not list_variants(p_dir):
            needs_refresh = True
        elif os.path.isfile(mtime_file):
            try:
                with open(mtime_file, "r", encoding="utf-8") as f:
                    saved_mtime = float(f.read().strip())
                if abs(os.path.getmtime(src_art) - saved_mtime) > 0.5:
                    needs_refresh = True
            except Exception:
                needs_refresh = True
        else:
            needs_refresh = True

    if needs_refresh:
        brand_marker = os.path.join(out_dir, "_brand_tag.txt")
        brand_tag = "prodbyjmd"
        if os.path.isfile(brand_marker):
            try:
                with open(brand_marker, "r", encoding="utf-8") as f:
                    brand_tag = f.read().strip() or "prodbyjmd"
            except Exception:
                pass
        generate_brand_thumbnails(p_dir, brand_tag=brand_tag)

    sel = os.path.join(p_dir, SELECTED_NAME)
    selected_src = ""
    marker = os.path.join(p_dir, THUMB_SUBDIR, "_selected.txt")
    if os.path.isfile(marker):
        try:
            with open(marker, "r", encoding="utf-8") as f:
                selected_src = f.read().strip()
        except Exception:
            pass

    brand_marker = os.path.join(p_dir, THUMB_SUBDIR, "_brand_tag.txt")
    brand_tag = "prodbyjmd"
    if os.path.isfile(brand_marker):
        try:
            with open(brand_marker, "r", encoding="utf-8") as f:
                brand_tag = f.read().strip() or "prodbyjmd"
        except Exception:
            pass

    return {
        "brand_tag": brand_tag,
        "default_artist": brand_tag,
        "variants": list_variants(p_dir),
        "has_selected": os.path.isfile(sel),
        "selected_src": selected_src,
        "style_labels": STYLE_LABELS,
        "job": None,
    }

def select_variant(p_dir: str, rel_file: str) -> bool:
    rel_file = rel_file.replace("\\", "/")
    name = os.path.basename(rel_file)
    src = os.path.join(p_dir, THUMB_SUBDIR, name)
    if not os.path.isfile(src):
        return False
    shutil.copyfile(src, os.path.join(p_dir, SELECTED_NAME))
    try:
        with open(os.path.join(p_dir, THUMB_SUBDIR, "_selected.txt"), "w", encoding="utf-8") as f:
            f.write(f"{THUMB_SUBDIR}/{name}")
    except Exception:
        pass
    return True
