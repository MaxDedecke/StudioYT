import os
import re
import json
import time
import uuid
import base64
import random
import shutil
import subprocess
import threading
import urllib.parse
import urllib.request
from typing import Dict, Any, List, Optional
from backend.config import FFMPEG_PATH

THUMB_W, THUMB_H = 1280, 720
PANEL_W, PANEL_H = 576, 720
THUMB_SUBDIR = "thumbnails"
SELECTED_NAME = "thumbnail.jpg"

ARTIST_SCENES = {
    "future": [
        "extreme close-up of a fully iced-out VVS diamond Cartier Santos watch on a wrist against a pitch-black background, every diamond sparkling under a single hard spotlight",
        "a man in an all-black designer outfit and dark sunglasses seen from the side, heavy diamond chains, standing next to a private jet stairway at night, paparazzi flash",
        "a man in a black leather jacket with stacked iced-out chains walking out of an Atlanta strip club at 3 AM, red neon sign behind, face turned away from camera, paparazzi photo",
        "a hand with diamond rings holding a styrofoam cup in the back seat of a Maybach at night, warm interior lights, blurry city lights through the window",
    ],
    "drake": [
        "a man in an oversized beige hoodie seen from behind on a penthouse balcony overlooking the Toronto skyline and CN Tower at night, moody blue hour",
        "candid paparazzi photo of a well-dressed man in a black puffer jacket walking with a woman in a white fur coat on a snowy Toronto street at night, faces turned away, flash photography",
        "a man in a tailored black suit sitting alone in a dim luxury lounge with a glass of champagne, warm amber light, face hidden in shadow, cinematic",
        "a lone figure in a hooded winter coat standing in the rain outside a closed luxury boutique at night, reflections on wet pavement, melancholic",
    ],
    "juice wrld": [
        "a young man in a pink hoodie riding a bicycle on a dark city street at night, harsh flash photo, motion blur, hood up, face obscured",
        "a lonely teenager in a black hoodie sitting on a rooftop at night under purple and blue neon light, head down, emo melancholic mood",
        "close-up of rain drops on a window with blurry purple neon city lights behind, a broken heart drawn in the condensation",
        "a young man with a guitar sitting on the floor of a dark bedroom lit only by a blue LED strip, face hidden by hood, emotional",
    ],
    "travis scott": [
        "a figure in a brown utility jacket standing in a foggy desert at dusk with dramatic dark clouds, cactus silhouettes, cinematic and psychedelic",
        "a crowd silhouette at a rave in front of a stage full of red smoke and pyrotechnics, shot from behind, chaotic energy",
        "a man in vintage earth-tone streetwear sitting on the hood of a rusty old pickup truck in the Texas desert at night, warm headlights, film grain",
    ],
    "don toliver": [
        "a man in a vintage leather jacket leaning against a classic 1970s car under a glowing sunset sky, dreamy psychedelic orange haze, face turned away",
        "a blurry long-exposure photo of a figure dancing in a dark club under swirling pink and orange lights, psychedelic",
        "a vintage convertible driving along a palm-lined road at golden hour with warm lens flares, dreamy 35mm film look",
    ],
    "metro boomin": [
        "a masked figure in a black hooded coat standing in red smoke under a single red spotlight, dark cinematic villain aesthetic",
        "a dark cinematic shot of a black Rolls-Royce Cullinan in an empty parking garage under flickering red light, smoke on the ground",
        "silhouette of a man in a long black coat standing on top of a skyscraper at night with lightning in the sky, epic dark mood",
    ],
    "playboi carti": [
        "a figure in black leather, chains and spiked accessories under harsh red light, grainy blurry flash photo, vampire punk aesthetic, face obscured",
        "a blurry flash photo of a crowd moshing in a dark warehouse with red strobe lights, chaotic underground rave",
        "a gothic figure in a black fur coat standing in a dark cathedral lit by red candles, distorted grainy photo",
    ],
    "ken carson": [
        "a figure in black opium-style punk outfit with chains standing in a dark hallway under harsh red flash, grainy distorted photo, face hidden",
        "blurry flash photo of a guitar smashing on a dark stage with red light and smoke, rage energy",
    ],
    "destroy lonely": [
        "a figure in a black leather trench coat and dark sunglasses in a dimly lit parking garage, red tint, grainy flash photo, face partially obscured",
        "a black vintage sports car under a single red light in an empty lot at night, haze, gothic mood",
    ],
    "yeat": [
        "a figure in futuristic chrome sunglasses and a balaclava under bright cyan and white strobe lights, grainy rage aesthetic",
        "a futuristic black supercar under cold blue light in an empty tunnel, motion blur, high energy",
    ],
    "lil baby": [
        "a man in designer streetwear with an iced-out chain seen from behind, standing in front of a white Lamborghini Urus in front of a mansion at night",
        "stacks of cash and a diamond chain on the leather seat of a luxury car, moody low light",
    ],
    "gunna": [
        "a man in a colorful designer outfit and sunglasses walking out of a luxury boutique in Paris at night, paparazzi flash, face turned away",
        "a hand with diamond rings on the steering wheel of a vintage Porsche, warm sunset light, luxury lifestyle",
    ],
    "21 savage": [
        "a man in a black hoodie with a diamond cross pendant standing in a dark snowy alley at night, cold blue tones, face hidden in shadow",
        "a dark close-up of a diamond cross chain on black fabric, cold harsh light",
    ],
    "offset": [
        "a man in a designer fur coat with stacked iced-out chains stepping out of a Rolls-Royce at night, paparazzi flash, face turned away",
        "close-up of a hand with diamond rings and an iced Audemars Piguet on a Rolls-Royce steering wheel at night",
    ],
    "young thug": [
        "a figure in a flamboyant colorful designer outfit standing in a field of flowers at dusk, editorial fashion photo, face turned away",
        "a green-tinted photo of a figure in a fur coat in a dark mansion hallway, eccentric luxury",
    ],
    "central cee": [
        "a young man in a black puffer jacket and balaclava standing on a London council estate at night, sodium street lights, grainy",
        "a figure in a tracksuit walking through an empty London tube station at night, cold fluorescent light, face hidden",
    ],
    "nemzzz": [
        "a young man in a black puffer jacket seen from behind walking down a rainy Manchester street at night, moody streetlight reflections",
        "a car window view of rainy UK motorway lights at night, melancholic blurry bokeh",
    ],
    "pashanim": [
        "a young man in a tracksuit sitting on a Berlin Kreuzberg U-Bahn bench at night, warm yellow light, face turned away, candid",
        "a candid flash photo of friends in front of a Spätkauf kiosk in Berlin at night, faces turned away, summer vibe",
    ],
    "luciano": [
        "a black Maybach parked in front of a Berlin Plattenbau at night, street lights, cinematic",
        "a man in a designer tracksuit with an iced-out chain seen from behind in front of a luxury car at night",
    ],
    "reezy": [
        "a man in a designer jacket in the back seat of a luxury car at night, city lights passing, face in shadow, moody",
        "a lone figure on a rooftop in Frankfurt at night overlooking the skyline, cinematic blue tones",
    ]
}

GENERIC_SCENES = [
    "extreme close-up of an iced-out VVS diamond watch on a wrist against a pitch-black background, single hard spotlight",
    "a hooded figure riding a bicycle on a dark city street at night, harsh flash photo, face obscured",
    "candid paparazzi photo of a well-dressed couple walking out of a luxury hotel at night, faces turned away, flash photography",
    "a black luxury car parked under a single streetlight in the rain at night, cinematic reflections",
    "a man in designer streetwear with diamond chains seen from behind on a rooftop overlooking a city at night",
]

STYLE_SUFFIX = (
    "Vertical 4:5 portrait photograph. Candid paparazzi / editorial street photo, shot on 35mm, "
    "one clear central subject that reads instantly at small size, strong contrast, natural colors, "
    "slightly dark moody exposure. Any person is anonymous: face turned away, hidden, masked or in shadow. "
    "No celebrities, no text, no letters, no logos, no watermark, photorealistic."
)

ARTIST_ALIASES = {
    "juicewrld": "juice wrld",
    "juice": "juice wrld",
    "carti": "playboi carti",
    "travis scott": "travis scott",
    "weeknd": "the weeknd",
    "kendrick": "kendrick lamar",
    "pnd": "partynextdoor",
    "party next door": "partynextdoor",
    "dolph": "young dolph",
    "thug": "young thug",
    "cench": "central cee",
}

def normalize_artist(name: str) -> str:
    n = re.sub(r"\s+", " ", (name or "").strip().lower())
    return ARTIST_ALIASES.get(n, n)

def scenes_for_artist(name: str) -> List[str]:
    key = normalize_artist(name)
    if key in ARTIST_SCENES and ARTIST_SCENES[key]:
        return list(ARTIST_SCENES[key])
    for k, v in ARTIST_SCENES.items():
        if v and (k in key or key in k) and len(key) >= 3:
            return list(v)
    return []

def detect_artists(p_dir: str):
    meta = os.path.join(p_dir, "metadata.md")
    titles = []
    artists = []
    if os.path.isfile(meta):
        try:
            with open(meta, "r", encoding="utf-8", errors="replace") as f:
                text = f.read()
            for m in re.finditer(r"^\s*\d+\.\s*(.+?Type Beat.*)$", text, re.IGNORECASE | re.MULTILINE):
                title = m.group(1).strip()
                titles.append(title)
                head = re.split(r"\s+Type Beat", title, flags=re.IGNORECASE)[0]
                head = re.sub(r"\[.*?\]|\(.*?\)", "", head).strip()
                for a in re.split(r"\s+x\s+|\s*&\s*|,", head, flags=re.IGNORECASE):
                    a = a.strip()
                    if a and a.lower() not in [x.lower() for x in artists]:
                        artists.append(a)
        except Exception:
            pass
    return artists, titles

def build_prompts(artist_input: str, count: int = 4) -> List[str]:
    names = [a.strip() for a in re.split(r"\s+x\s+|,|&", artist_input or "", flags=re.IGNORECASE) if a.strip()]
    pools = [scenes_for_artist(n) for n in names]
    pools = [p for p in pools if p]
    if not pools:
        pools = [list(GENERIC_SCENES)]
    for p in pools:
        random.shuffle(p)

    scenes = []
    i = 0
    while len(scenes) < count and any(pools):
        pool = pools[i % len(pools)]
        if pool:
            s = pool.pop()
            if s not in scenes:
                scenes.append(s)
        i += 1
    extra = [s for s in GENERIC_SCENES if s not in scenes]
    random.shuffle(extra)
    while len(scenes) < count and extra:
        scenes.append(extra.pop())
    return [f"{s}. {STYLE_SUFFIX}" for s in scenes[:count]]

_GEMINI_QUOTA_ZERO = False

def _gen_gemini(api_key: str, prompt: str) -> Optional[bytes]:
    global _GEMINI_QUOTA_ZERO
    if not api_key or _GEMINI_QUOTA_ZERO:
        return None
    for model_name in ["gemini-3.1-flash-image", "gemini-2.5-flash-image"]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "responseModalities": ["TEXT", "IMAGE"],
                "imageConfig": {"aspectRatio": "4:5"},
            },
        }
        try:
            req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"),
                                         headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            for cand in data.get("candidates", []):
                for part in cand.get("content", {}).get("parts", []):
                    inline = part.get("inlineData") or part.get("inline_data")
                    if inline and "data" in inline:
                        return base64.b64decode(inline["data"])
        except urllib.error.HTTPError as e:
            body = ""
            try: body = e.read().decode("utf-8", errors="replace")
            except Exception: pass
            if e.code == 429 and "limit: 0" in body:
                _GEMINI_QUOTA_ZERO = True
                return None
        except Exception:
            pass
    return None

def _gen_hf_router(hf_key: str, prompt: str) -> Optional[bytes]:
    if not hf_key:
        return None
    payload = {"inputs": prompt, "parameters": {"width": 832, "height": 1040, "num_inference_steps": 4}}
    for url in [
        "https://router.huggingface.co/hf-inference/models/black-forest-labs/FLUX.1-schnell",
        "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell",
    ]:
        try:
            req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={
                "Authorization": f"Bearer {hf_key}", "Content-Type": "application/json", "Accept": "image/jpeg"
            }, method="POST")
            with urllib.request.urlopen(req, timeout=40) as resp:
                b = resp.read()
                if b and len(b) > 5000:
                    return b
        except Exception:
            pass
    return None

def _gen_flux_space(hf_key: str, prompt: str) -> Optional[bytes]:
    headers = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
    if hf_key:
        headers["Authorization"] = f"Bearer {hf_key}"
    spaces = [
        ("https://multimodalart-flux-1-merged.hf.space", [prompt, 0, True, 832, 1040, 3.5, 4]),
        ("https://black-forest-labs-flux-1-schnell.hf.space", [prompt, 0, True, 832, 1040, 4]),
    ]
    for base, data in spaces:
        call_url = f"{base}/gradio_api/call/infer"
        t0 = time.time()
        try:
            req = urllib.request.Request(call_url, data=json.dumps({"data": data}).encode("utf-8"),
                                         headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=8) as resp:
                event_id = json.loads(resp.read().decode("utf-8")).get("event_id")
            if not event_id:
                continue
            with urllib.request.urlopen(urllib.request.Request(f"{call_url}/{event_id}", headers=headers), timeout=25) as sse:
                current = None
                while time.time() - t0 < 30:
                    raw = sse.readline()
                    if not raw: break
                    line = raw.decode("utf-8", errors="replace").strip()
                    if line.startswith("event: "):
                        current = line[7:].strip()
                        if current == "error": break
                    elif line.startswith("data: ") and current == "complete":
                        arr = json.loads(line[6:])
                        if isinstance(arr, list) and arr and isinstance(arr[0], dict) and arr[0].get("url"):
                            ir = urllib.request.Request(arr[0]["url"], headers={"User-Agent": "Mozilla/5.0"})
                            with urllib.request.urlopen(ir, timeout=15) as r:
                                return r.read()
        except Exception:
            pass
    return None

def _gen_keyless(prompt: str) -> Optional[bytes]:
    try:
        data = urllib.parse.urlencode({
            "prompt": prompt,
            "output_format": "bytes",
            "user_profile_id": "null",
            "anonymous_user_id": str(uuid.uuid4()),
            "request_timestamp": f"{time.time():.3f}",
            "user_is_subscribed": "false",
            "client_id": "pSgX7WgjukXCBoYwDM8G8GLnRRkvAoJlqa5eAVvj95o",
        }).encode("utf-8")
        req = urllib.request.Request("https://ai-api.magicstudio.com/api/ai-art-generator", data=data, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Origin": "https://magicstudio.com",
            "Referer": "https://magicstudio.com/ai-art-generator/",
        }, method="POST")
        with urllib.request.urlopen(req, timeout=25) as r:
            b = r.read()
            if b and len(b) > 10000:
                return b
    except Exception:
        pass
    return None

def generate_image_bytes(prompt: str, gemini_key: str = "", hf_key: str = "") -> Optional[bytes]:
    for fn in (lambda: _gen_gemini(gemini_key, prompt),
               lambda: _gen_hf_router(hf_key, prompt),
               lambda: _gen_flux_space(hf_key, prompt),
               lambda: _gen_keyless(prompt)):
        b = fn()
        if b:
            return b
    return None

def compose_thumbnail(src_path: str, dst_path: str) -> bool:
    vf = (
        f"scale={PANEL_W}:{PANEL_H}:force_original_aspect_ratio=increase:flags=lanczos,"
        f"crop={PANEL_W}:{PANEL_H},"
        f"eq=contrast=1.08:saturation=1.10:brightness=-0.01,"
        f"unsharp=5:5:0.6:5:5:0.0,"
        f"noise=alls=5:allf=t,"
        f"pad={THUMB_W}:{THUMB_H}:(ow-iw)/2:(oh-ih)/2:black,"
        f"format=yuvj420p"
    )
    try:
        subprocess.run(
            [FFMPEG_PATH, "-y", "-i", src_path, "-vf", vf, "-q:v", "2", "-frames:v", "1", "-update", "1", dst_path],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30,
        )
        return os.path.isfile(dst_path) and os.path.getsize(dst_path) > 5000
    except Exception:
        return False

THUMB_JOBS: Dict[str, Dict[str, Any]] = {}
_JOBS_LOCK = threading.Lock()

def list_variants(p_dir: str) -> List[str]:
    d = os.path.join(p_dir, THUMB_SUBDIR)
    if not os.path.isdir(d):
        return []
    files = sorted([f for f in os.listdir(d) if f.lower().endswith(".jpg") and not f.startswith("_")], reverse=True)
    return [f"{THUMB_SUBDIR}/{f}" for f in files]

def thumbnail_state(p_dir: str, project_name: str) -> Dict[str, Any]:
    artists, titles = detect_artists(p_dir)
    sel = os.path.join(p_dir, SELECTED_NAME)
    selected_src = ""
    marker = os.path.join(p_dir, THUMB_SUBDIR, "_selected.txt")
    if os.path.isfile(marker):
        try:
            with open(marker, "r", encoding="utf-8") as f:
                selected_src = f.read().strip()
        except Exception:
            pass
    default_artist = ""
    if titles:
        head = re.split(r"\s+Type Beat", titles[0], flags=re.IGNORECASE)[0]
        default_artist = re.sub(r"\[.*?\]|\(.*?\)", "", head).strip()
    return {
        "artists": artists,
        "titles": titles,
        "default_artist": default_artist,
        "variants": list_variants(p_dir),
        "has_selected": os.path.isfile(sel),
        "selected_src": selected_src,
        "job": THUMB_JOBS.get(project_name),
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

def _worker(project_name: str, p_dir: str, artist: str, count: int, gemini_key: str, hf_key: str):
    job = THUMB_JOBS[project_name]
    out_dir = os.path.join(p_dir, THUMB_SUBDIR)
    os.makedirs(out_dir, exist_ok=True)
    prompts = build_prompts(artist, count)
    job["total"] = len(prompts)
    try:
        for i, prompt in enumerate(prompts):
            job["label"] = f"Generiere Thumbnail {i + 1} von {len(prompts)} ..."
            img = generate_image_bytes(prompt, gemini_key, hf_key)
            if not img:
                job["failed"] += 1
                continue
            uid = f"{int(time.time() * 1000)}_{i}"
            raw = os.path.join(out_dir, f"_raw_{uid}.img")
            dst = os.path.join(out_dir, f"thumb_{uid}.jpg")
            with open(raw, "wb") as f:
                f.write(img)
            ok = compose_thumbnail(raw, dst)
            try: os.remove(raw)
            except Exception: pass
            if ok:
                job["done"] += 1
                job["new_files"].append(f"{THUMB_SUBDIR}/{os.path.basename(dst)}")
                if not os.path.isfile(os.path.join(p_dir, SELECTED_NAME)):
                    select_variant(p_dir, dst)
            else:
                job["failed"] += 1
        job["label"] = (f"{job['done']} Thumbnails fertig" if job["done"]
                        else "Kein Bild-Generator erreichbar – HF Token oder Gemini Key prüfen")
    except Exception as e:
        job["label"] = f"Fehler: {e}"
    finally:
        job["active"] = False
        job["finished_at"] = time.time()

def start_job(project_name: str, p_dir: str, artist: str, count: int, gemini_key: str = "", hf_key: str = "") -> Dict[str, Any]:
    with _JOBS_LOCK:
        cur = THUMB_JOBS.get(project_name)
        if cur and cur.get("active"):
            return cur
        THUMB_JOBS[project_name] = {
            "active": True, "artist": artist, "total": count, "done": 0, "failed": 0,
            "label": "Starte ...", "new_files": [], "started_at": time.time(),
        }
    threading.Thread(target=_worker, args=(project_name, p_dir, artist, count, gemini_key, hf_key),
                     daemon=True).start()
    return THUMB_JOBS[project_name]
