import os
import re
import json
import time
import base64
import random
import hashlib
import shutil
import tempfile
import subprocess
import threading
import urllib.parse
import urllib.request
import httpx
from typing import Tuple, Optional, Set
from backend.config import BASE_DIR, PROJECTS_DIR, ARTWORK_POOL_DIR, TRASH_DIR, FFMPEG_PATH, get_config, save_config

def file_md5(path: str) -> str:
    try:
        with open(path, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()
    except Exception:
        return ""

def safe_copy_file(src: str, dst: str, retries: int = 6, delay: float = 0.15) -> bool:
    for i in range(retries):
        try:
            tmp_dst = f"{dst}.tmp_{random.randint(1000, 9999)}"
            shutil.copyfile(src, tmp_dst)
            os.replace(tmp_dst, dst)
            return True
        except Exception:
            try:
                if os.path.exists(tmp_dst):
                    os.remove(tmp_dst)
            except Exception:
                pass
            try:
                shutil.copyfile(src, dst)
                return True
            except Exception:
                if i < retries - 1:
                    time.sleep(delay)
    return False

DEFAULT_LITHEN_ANIM_PROMPT = (
    "Animate this underground rap album cover into a seamless 3-5 second video loop:\n"
    "- Keep the static image and centered 1:1 cover framing 100% in focus with NO wild subject warping or morphing.\n"
    "- Add only a subtle, rhythmic analog camcorder / shutter stutter effect (candid micro-shake, subtle living 35mm grain jitter, and soft optical flash pulse).\n"
    "- High-contrast monochrome green/cyan tone, pitch-black outer pillarbox borders remain clean and still. Seamless music video loop."
)

_LITHEN_MODE_DECK = []
_LITHEN_GRADE_DECK = []
_ARTWORK_LOCK = threading.Lock()
GEMINI_IMAGE_QUOTA_ZERO = False

def build_lithen_prompts() -> Tuple[str, str]:
    global _LITHEN_MODE_DECK
    all_modes = [
        "only_woman",
        "only_car",
        "only_jewelry",
        "woman_car",
        "woman_jewelry",
        "car_jewelry",
        "woman_car_jewelry",
    ]
    if not _LITHEN_MODE_DECK:
        _LITHEN_MODE_DECK = list(all_modes)
        random.shuffle(_LITHEN_MODE_DECK)
    mode = _LITHEN_MODE_DECK.pop()

    cars = [
        "a matte black Porsche 911 GT3 RS with carbon swan-neck rear wing",
        "a tuned silver Nissan Skyline GT-R R34 V-Spec lowered on bronze TE37 forged wheels",
        "a white tuned widebody Nissan GT-R R35 Nismo with carbon fiber splitter",
        "a grey Lamborghini Huracán Tecnica parked in an underground lot",
        "a lowered white Mazda RX-7 FD3S with aggressive aero and titanium exhaust",
        "a black Lamborghini Aventador SVJ with aggressive carbon aerodynamics",
        "a tuned dark purple Nissan Silvia S15 Spec-R with widebody stance",
        "a chalk grey Porsche 911 GT3 with center-lock wheels",
        "a lowered BMW M4 G82 Competition with carbon aero kit",
        "a silver widebody Toyota Supra MK4 Turbo with custom deep-dish wheels",
        "a gloss black Ferrari F8 Tributo parked under dim garage lights",
    ]

    women = [
        "a young woman wearing a fitted black ribbed knit ski mask balaclava covering her face with only her intense eyes and sharp winged eyeliner visible",
        "a stylish woman wearing a designer silk patterned scarf tied securely across her lower face and nose, concealing her mouth and cheeks, with piercing smoky eyes",
        "a woman wearing a sleek tactical black balaclava covering her head, neck, chin, and mouth, revealing only her intense dark eyes looking directly into the lens",
        "a woman wearing a dark charcoal cashmere ski mask with clean cutouts revealing only her sharp, confident eyes",
        "a woman wearing a black knit balaclava face-covering pulled snug, with only her feline eyeliner and dark eyes exposed to the camera",
        "a girl wearing an oversized black streetwear hoodie and a tight black ski mask covering her lower face, nose, and mouth, revealing only intense eyes",
    ]

    cuban_chains = [
        "a heavy 18mm solid white-gold Miami Cuban link chain encrusted with brilliant pave VVS diamonds",
        "stacked diamond chains: a thick VVS Miami Cuban link choker and a sparkling baguette diamond tennis necklace",
        "a massive iced-out VVS diamond Miami Cuban link chain with a micro-pave box clasp and matching diamond Cuban bracelet",
        "two layered heavy silver and white-gold Cuban link chains with iced-out links and a diamond cross pendant",
        "a thick interlocking diamond Miami Cuban link chain around the neck and an iced-out Audemars Piguet Royal Oak watch on the wrist",
    ]

    iphone_settings = [
        "inside a dark concrete underground parking garage at night, harsh direct iPhone flash casting deep shadows",
        "in an empty dimly lit multi-story car park at 2 AM with direct smartphone camera flash",
        "against a pitch-black wall at a late-night private underground gathering, lit only by harsh direct phone flash",
        "in the passenger seat of a sports car at night with direct on-camera iPhone flash illumination",
        "at an empty late-night Japanese highway rest stop parking bay lit by direct mobile phone flash",
    ]

    car = random.choice(cars)
    woman = random.choice(women)
    chain = random.choice(cuban_chains)
    setting = random.choice(iphone_settings)

    if mode == "only_woman":
        scene_variants = [
            f"candid iPhone camera roll photo, sharp direct phone flash snapshot of {woman}, wearing {chain}, {setting}, looking straight into the phone camera lens",
            f"candid mirror selfie shot on iPhone with direct LED flash, close-up of {woman} wearing {chain}, harsh direct illumination against a dark background",
            f"authentic iPhone night photo of {woman} wearing {chain}, glancing directly into the smartphone lens, direct frontal flash lighting, dark shadows behind",
            f"raw camera roll snapshot taken on iPhone 15 Pro of {woman} wearing {chain}, harsh direct flash blowing out close highlights, unposed candid vibe",
        ]
    elif mode == "only_car":
        scene_variants = [
            f"candid iPhone camera roll night photo of {car} parked {setting}, direct phone flash reflecting off the clean glossy paint and carbon fiber bodywork, no people",
            f"candid smartphone flash photo, low-angle eye-level shot of {car} {setting}, direct on-camera flash highlighting the wheels and front bumper, pitch-black background, no people",
            f"raw unedited iPhone photo taken at night of {car} parked in a dark underground bay, harsh direct flash reflecting off headlights and chrome rims, authentic camera roll photo",
            f"candid handheld iPhone photo of {car} parked at night in an underground lot, direct camera flash overexposing the license plate and body crease, real smartphone snapshot",
        ]
    elif mode == "only_jewelry":
        scene_variants = [
            f"extreme close-up candid iPhone flash photo of {chain} resting on dark perforated leather car upholstery at night, direct phone flash catching every cut of the VVS diamonds",
            f"candid iPhone camera roll photo of a hand wearing diamond rings and holding {chain} up to the phone camera with direct LED flash against a pitch-black background",
            f"macro smartphone flash snapshot of {chain} and an iced-out luxury skeleton watch resting together on a dark surface, harsh direct flash highlighting solid interlocking metal links",
            f"candid handheld iPhone photo of {chain} draped over a dark steering wheel at night, direct camera flash sparkling off the pave diamonds",
        ]
    elif mode == "woman_car":
        scene_variants = [
            f"candid iPhone night photo with direct phone flash of {woman} wearing {chain} leaning against {car} {setting}, looking directly at the phone camera",
            f"candid camera roll snapshot taken on iPhone of {woman} wearing {chain} standing right next to the driver door of {car} {setting}, harsh direct flash lighting",
            f"candid iPhone photo from inside {car} with direct flash looking at {woman} wearing {chain} sitting in the passenger bucket seat at night",
            f"raw candid smartphone flash photo of {woman} wearing {chain} posing casually in front of {car} in a dark parking garage, direct LED flash",
        ]
    elif mode == "woman_jewelry":
        scene_variants = [
            f"candid close-up iPhone flash selfie of {woman} wearing {chain}, holding her hand with diamond rings up near the collar of her balaclava, harsh direct smartphone flash",
            f"candid iPhone camera roll photo of {woman} {setting}, with direct phone flash accentuating {chain} around her neck and her intense dark eyes above the mask",
            f"intimate handheld iPhone direct-flash portrait of {woman} wearing {chain} and an iced-out watch, looking straight into the camera lens in a pitch-black room",
            f"candid smartphone flash snapshot of {woman} adjusting {chain} over her black ski mask, direct LED flash highlights, dark shadows",
        ]
    elif mode == "car_jewelry":
        scene_variants = [
            f"candid iPhone POV photo inside the cockpit of {car} at night, a hand wearing an iced-out watch and heavy Cuban bracelet gripping the carbon steering wheel, direct phone flash",
            f"candid handheld iPhone flash photo of {chain} draped neatly across the center horn badge of the steering wheel inside {car} at night",
            f"candid smartphone flash photo showing a hand flexing {chain} in the foreground with {car} parked in the dark background {setting}",
            f"candid iPhone camera roll photo of {chain} and an iced watch resting on the carbon fiber center console inside {car}, direct LED flash",
        ]
    else:  # woman_car_jewelry
        scene_variants = [
            f"candid iPhone camera roll photo with direct flash of {woman} wearing {chain} standing closely beside {car} {setting}, looking directly into the smartphone lens",
            f"raw candid smartphone photo taken on iPhone of {woman} wearing {chain} leaning on the front fender of {car} {setting}, harsh direct frontal flash",
            f"candid iPhone flash snapshot inside {car} at night showing {woman} in the passenger seat wearing {chain}, direct camera flash illuminating the interior",
            f"candid handheld iPhone photo of {woman} wearing {chain} posing casually next to {car} in a dark underground garage, harsh direct flash, deep black shadows",
        ]

    scene = random.choice(scene_variants)
    img_prompt = (
        f"{scene}, candid iPhone camera roll photo, shot on iPhone 15 Pro, harsh direct on-camera flash, "
        f"realistic digital sensor texture, deep dark shadows, authentic unposed smartphone snapshot, no text, no watermarks, photorealistic."
    )
    anim_prompt = (
        f"Animate this underground rap album cover ({scene}) into a seamless 3-5 second video loop:\n"
        f"- The static image and centered 1:1 square frame remain in the foreground as the primary visual focus, with zero warping or facial/body distortion.\n"
        f"- Add a subtle, rhythmic analog shutter-stutter effect (candid handheld micro-jitters, living digital grain flutter, and soft optical light pulse on highlights/chrome).\n"
        f"- High-contrast monochrome green/cyan tone, pitch-black outer borders stay completely still. Clean, seamless loop."
    )
    return img_prompt, anim_prompt

def apply_lithen_finishing_grade(src_path: str, dst_path: str, subtle: bool = False) -> bool:
    global _LITHEN_GRADE_DECK
    if not _LITHEN_GRADE_DECK:
        _LITHEN_GRADE_DECK = ["cyan_flash", "olive_film", "mint_flash"]
        random.shuffle(_LITHEN_GRADE_DECK)
    grade_style = _LITHEN_GRADE_DECK.pop()

    if grade_style == "cyan_flash":
        tilt_deg = random.choice([-6.5, -4.5, 4.5, 6.5])
        noise_lvl = random.randint(25, 30)
        vf = (
            f"scale=1080:1080:force_original_aspect_ratio=increase,crop=1080:1080,"
            f"rotate={tilt_deg}*PI/180:ow=1080:oh=1080,"
            f"crop=920:920:80:80,scale=640:640:flags=bilinear,"
            f"hue=s=0,"
            f"eq=contrast=1.45:brightness=-0.06:gamma=0.94,"
            f"colorchannelmixer=rr=0.02:rg=0.04:rb=0.0:gr=0.0:gg=0.86:gb=0.0:br=0.0:bg=0.68:bb=0.0,"
            f"scale=1080:1080:flags=bilinear,"
            f"noise=alls={noise_lvl}:allf=t+u,"
            f"pad=1920:1080:(ow-iw)/2:(oh-ih)/2:black"
        )
    elif grade_style == "olive_film":
        noise_lvl = random.randint(20, 25)
        vf = (
            f"scale=1080:1080:force_original_aspect_ratio=increase,crop=1080:1080,"
            f"scale=620:620:flags=bilinear,"
            f"hue=s=0,"
            f"eq=contrast=1.35:brightness=-0.10:gamma=0.90,"
            f"colorchannelmixer=rr=0.0:rg=0.36:rb=0.0:gr=0.0:gg=0.58:gb=0.0:br=0.0:bg=0.38:bb=0.0,"
            f"curves=r='0/0.03 0.5/0.22 1/0.68':g='0/0.06 0.5/0.38 1/0.92':b='0/0.04 0.5/0.24 1/0.72',"
            f"scale=1080:1080:flags=bilinear,"
            f"noise=alls={noise_lvl}:allf=t+u,"
            f"pad=1920:1080:(ow-iw)/2:(oh-ih)/2:black"
        )
    else:
        noise_lvl = random.randint(23, 28)
        vf = (
            f"scale=1080:1080:force_original_aspect_ratio=increase,crop=1080:1080,"
            f"scale=640:640:flags=bilinear,"
            f"hue=s=0,"
            f"eq=contrast=1.42:brightness=0.05:gamma=1.14,"
            f"colorchannelmixer=rr=0.0:rg=0.64:rb=0.0:gr=0.0:gg=0.96:gb=0.0:br=0.0:bg=0.76:bb=0.0,"
            f"scale=1080:1080:flags=bilinear,"
            f"noise=alls={noise_lvl}:allf=t+u,"
            f"pad=1920:1080:(ow-iw)/2:(oh-ih)/2:black"
        )
    try:
        subprocess.run(
            [FFMPEG_PATH, "-y", "-i", src_path, "-vf", vf, "-q:v", "2", "-frames:v", "1", "-update", "1", dst_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=15
        )
        return os.path.isfile(dst_path) and os.path.getsize(dst_path) > 10000
    except Exception:
        return False

def generate_live_hf_artwork(hf_key: str, project_name: str) -> Tuple[Optional[str], Optional[str]]:
    img_prompt, anim_prompt = build_lithen_prompts()
    uid = f"{int(time.time() * 1000)}_{random.randint(100, 999)}"

    if hf_key:
        endpoints = [
            "https://router.huggingface.co/hf-inference/models/black-forest-labs/FLUX.1-schnell",
            "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell",
        ]
        payload = {
            "inputs": img_prompt,
            "parameters": {"width": 1280, "height": 720, "num_inference_steps": 4}
        }
        for url in endpoints:
            try:
                req = urllib.request.Request(
                    url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={
                        "Authorization": f"Bearer {hf_key}",
                        "Content-Type": "application/json",
                        "Accept": "image/jpeg"
                    },
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=15) as resp:
                    img_bytes = resp.read()
                    if img_bytes and len(img_bytes) > 5000:
                        raw_path = os.path.join(ARTWORK_POOL_DIR, f"_hf_raw_{project_name}_{uid}.jpg")
                        pool_name = f"lithen_hf_{project_name}_{uid}.jpg"
                        pool_path = os.path.join(ARTWORK_POOL_DIR, pool_name)
                        with open(raw_path, "wb") as f:
                            f.write(img_bytes)
                        if apply_lithen_finishing_grade(raw_path, pool_path, subtle=True):
                            try:
                                os.remove(raw_path)
                            except Exception:
                                pass
                            return pool_path, anim_prompt
                        else:
                            shutil.move(raw_path, pool_path)
                            return pool_path, anim_prompt
            except Exception:
                break

    # FLUX.1 Spaces
    flux_spaces = [
        ("https://multimodalart-flux-1-merged.hf.space", [img_prompt, 0, True, 1024, 576, 3.5, 4]),
        ("https://black-forest-labs-flux-1-schnell.hf.space", [img_prompt, 0, True, 1024, 576, 4]),
    ]
    headers = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
    if hf_key:
        headers["Authorization"] = f"Bearer {hf_key}"

    for space_base, space_data in flux_spaces:
        call_url = f"{space_base}/gradio_api/call/infer"
        t0 = time.time()
        try:
            req = urllib.request.Request(call_url, data=json.dumps({"data": space_data}).encode("utf-8"), headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=6) as resp:
                event_id = json.loads(resp.read().decode("utf-8")).get("event_id")

            if event_id:
                sse_req = urllib.request.Request(f"{call_url}/{event_id}", headers=headers)
                with urllib.request.urlopen(sse_req, timeout=10) as sse:
                    current_event = None
                    while time.time() - t0 < 12.0:
                        raw_line = sse.readline()
                        if not raw_line: break
                        line = raw_line.decode("utf-8", errors="replace").strip()
                        if line.startswith("event: "):
                            current_event = line[7:].strip()
                            if current_event in ("error", "heartbeat"): break
                        elif line.startswith("data: ") and current_event == "complete":
                            arr = json.loads(line[6:])
                            if isinstance(arr, list) and len(arr) > 0 and isinstance(arr[0], dict):
                                img_url = arr[0].get("url")
                                if img_url:
                                    raw_webp = os.path.join(ARTWORK_POOL_DIR, f"_flux_raw_{project_name}_{uid}.webp")
                                    pool_name = f"lithen_flux_{project_name}_{uid}.jpg"
                                    pool_path = os.path.join(ARTWORK_POOL_DIR, pool_name)
                                    img_req = urllib.request.Request(img_url, headers={"User-Agent": "Mozilla/5.0"})
                                    with urllib.request.urlopen(img_req, timeout=12) as ir:
                                        with open(raw_webp, "wb") as f:
                                            f.write(ir.read())
                                    if apply_lithen_finishing_grade(raw_webp, pool_path, subtle=True):
                                        try: os.remove(raw_webp)
                                        except Exception: pass
                                        return pool_path, anim_prompt
        except Exception:
            pass

    # Direct 2.5s Generator
    try:
        import uuid
        ms_data = urllib.parse.urlencode({
            "prompt": img_prompt,
            "output_format": "bytes",
            "user_profile_id": "null",
            "anonymous_user_id": str(uuid.uuid4()),
            "request_timestamp": f"{time.time():.3f}",
            "user_is_subscribed": "false",
            "client_id": "pSgX7WgjukXCBoYwDM8G8GLnRRkvAoJlqa5eAVvj95o"
        }).encode("utf-8")
        ms_req = urllib.request.Request(
            "https://ai-api.magicstudio.com/api/ai-art-generator",
            data=ms_data,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Origin": "https://magicstudio.com",
                "Referer": "https://magicstudio.com/ai-art-generator/"
            },
            method="POST"
        )
        with urllib.request.urlopen(ms_req, timeout=15) as r:
            img_bytes = r.read()
            if img_bytes and len(img_bytes) > 10000:
                raw_jpg = os.path.join(ARTWORK_POOL_DIR, f"_ms_raw_{project_name}_{uid}.jpg")
                pool_name = f"lithen_live_{project_name}_{uid}.jpg"
                pool_path = os.path.join(ARTWORK_POOL_DIR, pool_name)
                with open(raw_jpg, "wb") as f:
                    f.write(img_bytes)
                if apply_lithen_finishing_grade(raw_jpg, pool_path, subtle=True):
                    try: os.remove(raw_jpg)
                    except Exception: pass
                    return pool_path, anim_prompt
    except Exception:
        pass

    return None, None

def generate_live_gemini_artwork(api_key: str, project_name: str) -> Tuple[Optional[str], Optional[str]]:
    global GEMINI_IMAGE_QUOTA_ZERO
    if GEMINI_IMAGE_QUOTA_ZERO or not api_key:
        return None, None

    img_prompt, anim_prompt = build_lithen_prompts()

    for model_name in ["gemini-3.1-flash-image", "gemini-2.5-flash-image"]:
        gen_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        gen_payload = {
            "contents": [{"parts": [{"text": img_prompt}]}],
            "generationConfig": {"responseModalities": ["TEXT", "IMAGE"]}
        }
        try:
            req = urllib.request.Request(
                gen_url,
                data=json.dumps(gen_payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=25) as resp:
                res_data = json.loads(resp.read().decode("utf-8"))
                candidates = res_data.get("candidates", [])
                for cand in candidates:
                    parts = cand.get("content", {}).get("parts", [])
                    for part in parts:
                        inline = part.get("inlineData") or part.get("inline_data")
                        if inline and "data" in inline:
                            img_bytes = base64.b64decode(inline["data"])
                            pool_name = f"lithen_live_{project_name}_{int(time.time())}.jpg"
                            pool_path = os.path.join(ARTWORK_POOL_DIR, pool_name)
                            with open(pool_path, "wb") as f:
                                f.write(img_bytes)
                            return pool_path, anim_prompt
        except urllib.error.HTTPError as e:
            err_body = ""
            try: err_body = e.read().decode("utf-8", errors="replace")
            except Exception: pass
            if e.code == 429 and "limit: 0" in err_body:
                GEMINI_IMAGE_QUOTA_ZERO = True
                return None, None
        except Exception:
            pass

    return None, None

def get_active_project_artwork_hashes(exclude_project: Optional[str] = None) -> Set[str]:
    active = set()
    if os.path.exists(PROJECTS_DIR):
        for d in os.listdir(PROJECTS_DIR):
            if exclude_project and d == exclude_project: continue
            art_file = os.path.join(PROJECTS_DIR, d, "artwork.jpg")
            if os.path.isfile(art_file):
                h = file_md5(art_file)
                if h: active.add(h)
    return active

def get_all_used_artwork_hashes(exclude_project: Optional[str] = None) -> Set[str]:
    cfg = get_config()
    used = set(cfg.get("used_artwork_hashes", []))
    gdrive = cfg.get("gdrive_path", "").strip().strip('"').strip("'")
    search_roots = [PROJECTS_DIR, TRASH_DIR]
    if gdrive and os.path.exists(gdrive):
        search_roots.append(gdrive)
    for root_dir in search_roots:
        if not os.path.exists(root_dir): continue
        for d in os.listdir(root_dir):
            if exclude_project and d == exclude_project: continue
            art_file = os.path.join(root_dir, d, "artwork.jpg")
            if os.path.isfile(art_file):
                h = file_md5(art_file)
                if h: used.add(h)
    return used

def natural_sort_key(s: str):
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', os.path.basename(s))]

def analyze_artwork_and_build_loop_prompt(image_path: str, api_key: str = "") -> str:
    """Uses Gemini Multimodal Vision to inspect the actual generated image and craft a tailored video loop prompt
    where ONLY specific micro-motion details animate, with zero distortion or morphing of the main subject.
    """
    if not os.path.isfile(image_path):
        return DEFAULT_LITHEN_ANIM_PROMPT

    if not api_key:
        cfg = get_config()
        api_key = cfg.get("gemini_api_key", "").strip() or os.environ.get("GEMINI_API_KEY", "").strip()

    if api_key:
        temp_thumb = None
        try:
            # Create a lightweight 640px thumbnail to drastically speed up upload and vision inference
            temp_thumb = os.path.join(tempfile.gettempdir(), f"gemini_vision_{random.randint(10000, 99999)}.jpg")
            try:
                subprocess.run(
                    [FFMPEG_PATH, "-y", "-i", image_path, "-vf", "scale=640:-1", "-q:v", "4", temp_thumb],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=8
                )
                input_file = temp_thumb if os.path.isfile(temp_thumb) and os.path.getsize(temp_thumb) > 1000 else image_path
            except Exception:
                input_file = image_path

            with open(input_file, "rb") as f:
                img_b64 = base64.b64encode(f.read()).decode("utf-8")

            prompt = (
                "Du bist ein erfahrener Director und Video-Animator für Hip-Hop & Trap Musikvideos.\n"
                "Analysiere dieses Album-Cover-Bild genau und erstelle daraus einen maßgeschneiderten, hochpräzisen Prompt für die Gemini Video-Animation (3-5 Sekunden nahtloser Video-Loop).\n\n"
                "STRIKTE VORGABEN:\n"
                "1. Analysiere präzise, welche Motive auf DIESEM BILD zu sehen sind (z. B. maskierte Frau, Sportwagen, diamantbesetzte Uhr, Cuban Chains, Lenkrad, etc.).\n"
                "2. Im Video-Loop dürfen sich IMMER NUR FEINE DETAILS bewegen! Das Hauptmotiv und die Anatomie dürfen sich NIEMALS verformen, morphen oder schmelzen.\n"
                "3. Die zentrierte 1:1 Abdeckung und die schwarzen Balken links und rechts bleiben 100% starr und eingefroren.\n"
                "4. Definiere 2 bis 3 ganz konkrete Mikrobewegungen, die exakt zu den Elementen auf diesem Bild passen (z. B. subtiles Funkeln auf Diamant-Facetten, sanftes Atmen, Scheinwerfer-Glimmer, Shutter-Jitter, analoges Film-Korn).\n\n"
                "Antworte genau in diesem Format:\n"
                "### 🔍 Bild-Analyse:\n"
                "[1-2 Sätze auf Deutsch: Was wurde im Bild erkannt?]\n\n"
                "### 🎬 Gemini Video-Loop Prompt:\n"
                "```text\n"
                "[Englischer, optimierter Prompt für Gemini / Veo / Video-Generatoren, der exakt beschreibt was statisch bleibt und welche spezifischen Details sich im 3-5s Loop bewegen]\n"
                "```"
            )

            payload = {
                "contents": [{
                    "parts": [
                        {"text": prompt},
                        {"inline_data": {"mime_type": "image/jpeg", "data": img_b64}}
                    ]
                }],
                "generationConfig": {"temperature": 0.6}
            }

            models = ["gemini-3.5-flash", "gemini-3.8-flash", "gemini-3.1-flash-lite", "gemini-flash-latest", "gemini-pro-latest"]
            for model_name in models:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
                try:
                    r = httpx.post(url, json=payload, timeout=20.0)
                    if r.status_code == 200:
                        cand = r.json().get("candidates", [])
                        if cand:
                            parts = cand[0].get("content", {}).get("parts", [])
                            text = "".join([p.get("text", "") for p in parts]).strip()
                            if len(text) > 40:
                                return text
                except Exception as e:
                    print(f"[Gemini Vision ({model_name})] Fallback:", e)
        except Exception as e:
            print("[Gemini Vision Analysis] Error:", e)
        finally:
            if temp_thumb and os.path.exists(temp_thumb):
                try:
                    os.remove(temp_thumb)
                except Exception:
                    pass

    # High-quality fallback if Gemini Vision is temporarily overloaded / unavailable
    return (
        "### 🔍 Bild-Analyse:\n"
        "Lithen Dark-Trap Artwork mit zentriertem 1:1 Cover, starkem Blitzlicht-Fokus und monochromatischem Farbgrading.\n\n"
        "### 🎬 Gemini Video-Loop Prompt:\n"
        "```text\n"
        "Seamless 4-second video loop, locked static camera. The left and right vertical black pillarbox bars remain 100% frozen, pitch black, and completely static throughout.\n\n"
        "Strict micro-movements only, preserving absolute subject geometry, bodywork, and facial features without morphing or warping:\n"
        "1. Specular glints: Tiny, sharp light gleams travel smoothly across metallic edges, Cuban chains, and watch bezels.\n"
        "2. Texture & grain: Living 35mm handheld shutter grain pulses delicately across the deep shadow tones.\n"
        "3. Ambient light pulse: Subtle, rhythmic optical luminance flutter reflecting off reflective surfaces.\n\n"
        "Absolute structural stability, no morphing, no distortion. Ultra-clean underground hip-hop aesthetic.\n"
        "```"
    )

def assign_unique_artwork(p_dir: str, project_name: str, force_new: bool = False) -> str:
    with _ARTWORK_LOCK:
        cfg = get_config()
        hf_key = cfg.get("hf_api_key", "").strip() or os.environ.get("HF_TOKEN", "").strip()
        api_key = cfg.get("gemini_api_key", "").strip() or os.environ.get("GEMINI_API_KEY", "").strip()
        current_art = os.path.join(p_dir, "artwork.jpg")

        # 1. Try Live Generator
        live_path, _ = generate_live_hf_artwork(hf_key, project_name)
        if live_path and os.path.exists(live_path):
            safe_copy_file(live_path, current_art)
            h = file_md5(live_path)
            used_list = cfg.get("used_artwork_hashes", [])
            if h and h not in used_list:
                used_list.append(h)
                cfg["used_artwork_hashes"] = used_list
                save_config(cfg)
            return analyze_artwork_and_build_loop_prompt(current_art, api_key)

        # 2. Try Gemini
        if api_key:
            live_path, _ = generate_live_gemini_artwork(api_key, project_name)
            if live_path and os.path.exists(live_path):
                safe_copy_file(live_path, current_art)
                h = file_md5(live_path)
                used_list = cfg.get("used_artwork_hashes", [])
                if h and h not in used_list:
                    used_list.append(h)
                    cfg["used_artwork_hashes"] = used_list
                    save_config(cfg)
                return analyze_artwork_and_build_loop_prompt(current_art, api_key)

        # 3. Fallback from Artwork Pool
        active_hashes = get_active_project_artwork_hashes(exclude_project=project_name)
        used_hashes = get_all_used_artwork_hashes(exclude_project=None if force_new else project_name)

        pool_images = sorted(
            [
                os.path.join(ARTWORK_POOL_DIR, f)
                for f in os.listdir(ARTWORK_POOL_DIR)
                if f.lower().endswith((".jpg", ".png")) and not f.startswith("_") and os.path.isfile(os.path.join(ARTWORK_POOL_DIR, f))
            ],
            key=natural_sort_key
        )

        chosen_art = None
        for img_path in pool_images:
            h = file_md5(img_path)
            if h not in used_hashes and h not in active_hashes:
                chosen_art = img_path
                break

        if not chosen_art:
            non_active_candidates = [img_path for img_path in pool_images if file_md5(img_path) not in active_hashes]
            if non_active_candidates:
                chosen_art = random.choice(non_active_candidates)

        if chosen_art:
            safe_copy_file(chosen_art, current_art)
            h = file_md5(current_art)
            used_list = list(get_all_used_artwork_hashes())
            if h and h not in used_list:
                used_list.append(h)
            cfg["used_artwork_hashes"] = used_list
            save_config(cfg)
            return analyze_artwork_and_build_loop_prompt(current_art, api_key)
        elif pool_images:
            base_art = random.choice(pool_images)
            safe_copy_file(base_art, current_art)
            return analyze_artwork_and_build_loop_prompt(current_art, api_key)

        return analyze_artwork_and_build_loop_prompt(current_art, api_key)
