import os
import re
import json
import time
import base64
import random
import hashlib
import subprocess
import threading
import urllib.parse
import urllib.request
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import shutil
import numpy as np
import thumbnail_gen

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECTS_DIR = os.path.join(BASE_DIR, "projects")
ARTWORK_POOL_DIR = os.path.join(BASE_DIR, "artwork_pool")
TRASH_DIR = os.path.join(BASE_DIR, "trash")
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")

os.makedirs(PROJECTS_DIR, exist_ok=True)
os.makedirs(ARTWORK_POOL_DIR, exist_ok=True)
os.makedirs(TRASH_DIR, exist_ok=True)

FFMPEG_PATH = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Packages\Gyan.FFmpeg.Essentials_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.1-essentials_build\bin\ffmpeg.exe")
if not os.path.exists(FFMPEG_PATH):
    FFMPEG_PATH = "ffmpeg"

def get_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"gdrive_path": "", "gemini_api_key": "", "hf_api_key": "", "used_artwork_hashes": []}

def auto_detect_gdrive():
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

def save_config(cfg):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
    except Exception as e:
        print("Error saving config:", e)

def file_md5(path):
    try:
        with open(path, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()
    except Exception:
        return ""

DEFAULT_LITHEN_ANIM_PROMPT = (
    "Animate this underground rap album cover into a seamless 3-5 second video loop:\n"
    "- Keep the static image and centered 1:1 cover framing 100% in focus with NO wild subject warping or morphing.\n"
    "- Add only a subtle, rhythmic analog camcorder / shutter stutter effect (candid micro-shake, subtle living 35mm grain jitter, and soft optical flash pulse).\n"
    "- High-contrast monochrome green/cyan tone, pitch-black outer pillarbox borders remain clean and still. Seamless music video loop."
)

POOL_PROMPTS = {
    "lithen_cover_cyan_grillz.jpg": (
        "Animate this 35mm flash portrait into a seamless video loop:\n"
        "- The close-up photo stays sharp and centered with zero facial distortion.\n"
        "- Add a subtle, rhythmic shutter-stutter effect (candid analog camera micro-jitters, living CCD film grain flicker, and delicate light glints on the teeth and silver rings).\n"
        "- Perfect seamless loop, dark cyan-green monochrome tone."
    ),
    "lithen_cover_olive_lambos.jpg": (
        "Animate this underground car meet photograph into a seamless video loop:\n"
        "- The cars and environment stay fixed in place with clean geometric perspective.\n"
        "- Apply a subtle analog shutter stutter / film gate pulse and gentle living grain flutter across the olive-green tones.\n"
        "- 4-point cross star-filter glints on the car paint softly pulse. Seamless loop."
    ),
    "lithen_cover_mint_jdm.jpg": (
        "Animate this disposable camera flash garage photo into a seamless video loop:\n"
        "- The parked white JDM cars remain razor sharp without warping.\n"
        "- Subtle rhythmic shutter micro-stutter effect, analog frame jitter, and living film grain.\n"
        "- Clean seamless loop, mint-green direct flash monochrome palette."
    ),
}

_LITHEN_MODE_DECK = []
_LITHEN_GRADE_DECK = []

def build_lithen_prompts():
    """Creates a unique, randomized candid iPhone night-flash photo prompt that rotates across:
    - only_woman (Verhüllte Frau mit Skimaske/Tuch + Cuban Chain)
    - only_car (Modernes Supercar oder getunter JDM)
    - only_jewelry (Schwere VVS Cuban Chains, iced-out Watches & Rings)
    - woman_car (Verhüllte Frau an Supercar/JDM)
    - woman_jewelry (Verhüllte Frau zeigt Cuban Chains & Iced Watches)
    - car_jewelry (Cockpit mit Cuban Chain am Lenkrad / Iced Watch)
    - woman_car_jewelry (Verhüllte Frau mit Cuban Chain & Supercar)
    
    Adheres strictly to user requirements:
    1. Cars: ONLY modern supercars (Porsche GT3 RS, Lambo, Ferrari, BMW M4) or tuned JDM (GT-R R34/R35, RX-7 FD, S15, Supra).
    2. Women: ALWAYS veiled (fitted knit ski mask / balaclava or designer silk scarf covering lower face/nose, showing only intense eyes).
    3. Jewelry: Heavy realistic solid white-gold / platinum VVS Miami Cuban link chains, iced-out watches, diamond tennis chains.
    4. Vibe: Authentic candid iPhone 15 Pro direct-flash camera roll snapshot at night, sharp flash highlights against pitch-black shadows.
    5. No repetitive prompt clichés.
    """
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

    # Modern Supercars & Tuned JDM only
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

    # Masked / Veiled Women only (Ski mask / Balaclava / Silk Scarf covering face, only eyes visible)
    women = [
        "a young woman wearing a fitted black ribbed knit ski mask balaclava covering her face with only her intense eyes and sharp winged eyeliner visible",
        "a stylish woman wearing a designer silk patterned scarf tied securely across her lower face and nose, concealing her mouth and cheeks, with piercing smoky eyes",
        "a woman wearing a sleek tactical black balaclava covering her head, neck, chin, and mouth, revealing only her intense dark eyes looking directly into the lens",
        "a woman wearing a dark charcoal cashmere ski mask with clean cutouts revealing only her sharp, confident eyes",
        "a woman wearing a black knit balaclava face-covering pulled snug, with only her feline eyeliner and dark eyes exposed to the camera",
        "a girl wearing an oversized black streetwear hoodie and a tight black ski mask covering her lower face, nose, and mouth, revealing only intense eyes",
    ]

    # Realistic Heavy Jewelry (Heavy Cuban link chains, diamond tennis chains, iced AP/Rolex)
    cuban_chains = [
        "a heavy 18mm solid white-gold Miami Cuban link chain encrusted with brilliant pave VVS diamonds",
        "stacked diamond chains: a thick VVS Miami Cuban link choker and a sparkling baguette diamond tennis necklace",
        "a massive iced-out VVS diamond Miami Cuban link chain with a micro-pave box clasp and matching diamond Cuban bracelet",
        "two layered heavy silver and white-gold Cuban link chains with iced-out links and a diamond cross pendant",
        "a thick interlocking diamond Miami Cuban link chain around the neck and an iced-out Audemars Piguet Royal Oak watch on the wrist",
    ]

    # Realistic iPhone night-flash settings
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
        anim_focus = "the masked woman's steady gaze, subtle micro-stutter shutter flutter, and diamond flash glints"
    elif mode == "only_car":
        scene_variants = [
            f"candid iPhone camera roll night photo of {car} parked {setting}, direct phone flash reflecting off the clean glossy paint and carbon fiber bodywork, no people",
            f"candid smartphone flash photo, low-angle eye-level shot of {car} {setting}, direct on-camera flash highlighting the wheels and front bumper, pitch-black background, no people",
            f"raw unedited iPhone photo taken at night of {car} parked in a dark underground bay, harsh direct flash reflecting off headlights and chrome rims, authentic camera roll photo",
            f"candid handheld iPhone photo of {car} parked at night in an underground lot, direct camera flash overexposing the license plate and body crease, real smartphone snapshot",
        ]
        anim_focus = "the parked supercar's clean body lines, subtle analog shutter micro-jitter, and delicate reflections"
    elif mode == "only_jewelry":
        scene_variants = [
            f"extreme close-up candid iPhone flash photo of {chain} resting on dark perforated leather car upholstery at night, direct phone flash catching every cut of the VVS diamonds",
            f"candid iPhone camera roll photo of a hand wearing diamond rings and holding {chain} up to the phone camera with direct LED flash against a pitch-black background",
            f"macro smartphone flash snapshot of {chain} and an iced-out luxury skeleton watch resting together on a dark surface, harsh direct flash highlighting solid interlocking metal links",
            f"candid handheld iPhone photo of {chain} draped over a dark steering wheel at night, direct camera flash sparkling off the pave diamonds",
        ]
        anim_focus = "the sparkling diamond facets, rhythmic subtle shutter micro-stutter, and crisp metallic reflections"
    elif mode == "woman_car":
        scene_variants = [
            f"candid iPhone night photo with direct phone flash of {woman} wearing {chain} leaning against {car} {setting}, looking directly at the phone camera",
            f"candid camera roll snapshot taken on iPhone of {woman} wearing {chain} standing right next to the driver door of {car} {setting}, harsh direct flash lighting",
            f"candid iPhone photo from inside {car} with direct flash looking at {woman} wearing {chain} sitting in the passenger bucket seat at night",
            f"raw candid smartphone flash photo of {woman} wearing {chain} posing casually in front of {car} in a dark parking garage, direct LED flash",
        ]
        anim_focus = "the masked woman and the tuned car, subtle rhythmic stutter pulse, and living micro-jitter"
    elif mode == "woman_jewelry":
        scene_variants = [
            f"candid close-up iPhone flash selfie of {woman} wearing {chain}, holding her hand with diamond rings up near the collar of her balaclava, harsh direct smartphone flash",
            f"candid iPhone camera roll photo of {woman} {setting}, with direct phone flash accentuating {chain} around her neck and her intense dark eyes above the mask",
            f"intimate handheld iPhone direct-flash portrait of {woman} wearing {chain} and an iced-out watch, looking straight into the camera lens in a pitch-black room",
            f"candid smartphone flash snapshot of {woman} adjusting {chain} over her black ski mask, direct LED flash highlights, dark shadows",
        ]
        anim_focus = "the masked woman's eyes, the glittering Cuban chain, and subtle analog shutter stutter"
    elif mode == "car_jewelry":
        scene_variants = [
            f"candid iPhone POV photo inside the cockpit of {car} at night, a hand wearing an iced-out watch and heavy Cuban bracelet gripping the carbon steering wheel, direct phone flash",
            f"candid handheld iPhone flash photo of {chain} draped neatly across the center horn badge of the steering wheel inside {car} at night",
            f"candid smartphone flash photo showing a hand flexing {chain} in the foreground with {car} parked in the dark background {setting}",
            f"candid iPhone camera roll photo of {chain} and an iced watch resting on the carbon fiber center console inside {car}, direct LED flash",
        ]
        anim_focus = "the diamond chain in the cockpit, subtle steering wheel reflections, and gentle shutter pulse"
    else:  # woman_car_jewelry
        scene_variants = [
            f"candid iPhone camera roll photo with direct flash of {woman} wearing {chain} standing closely beside {car} {setting}, looking directly into the smartphone lens",
            f"raw candid smartphone photo taken on iPhone of {woman} wearing {chain} leaning on the front fender of {car} {setting}, harsh direct frontal flash",
            f"candid iPhone flash snapshot inside {car} at night showing {woman} in the passenger seat wearing {chain}, direct camera flash illuminating the interior",
            f"candid handheld iPhone photo of {woman} wearing {chain} posing casually next to {car} in a dark underground garage, harsh direct flash, deep black shadows",
        ]
        anim_focus = "the masked woman, the modern sports car, and the iced-out Cuban chain with subtle shutter micro-stutter"

    scene = random.choice(scene_variants)
    print(f"[Lithen Prompt Router] Mode='{mode}' -> {scene[:95]}...")

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

_ARTWORK_LOCK = threading.Lock()

def safe_copy_file(src, dst, retries=6, delay=0.15):
    """Safely copies src to dst on Windows, retrying if dst is momentarily locked by browser or sync."""
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

def apply_lithen_finishing_grade(src_path, dst_path, subtle=False):
    """Applies the exact Lithen underground rap cover aesthetic from the 3 reference screenshots:
    - 1:1 square album cover (1080x1080) centered on a pitch-black 16:9 widescreen frame (1920x1080)
    - Pure monochrome luminance (hue=s=0) mapped to rotating Cyan-Emerald Flash, Dark Olive/Forest Film, or Blown-Out Mint Flash LUTs
    - Heavy analog film grain (no Parental Advisory sticker)."""
    global _LITHEN_GRADE_DECK
    if not _LITHEN_GRADE_DECK:
        _LITHEN_GRADE_DECK = ["cyan_flash", "olive_film", "mint_flash"]
        random.shuffle(_LITHEN_GRADE_DECK)
    grade_style = _LITHEN_GRADE_DECK.pop()

    if grade_style == "cyan_flash":
        # Reference 1: Monochrome Cyan-Teal NightShot Flash + subtle Dutch tilt + heavy analog film grain
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
        # Reference 2: Dark Olive / Forest Green Vintage Film + lifted matte blacks + analog grain
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
        # Reference 3: Blown-out Harsh Direct Flash Mint/Sage Green + heavy analog grain
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

def generate_live_hf_artwork(hf_key, project_name):
    """Generates a 100% brand-new live 16:9 Lithen-style artwork (supports HF Token Router, fast non-blocking FLUX Spaces, and unlimited keyless 2.5s live AI generator)."""
    img_prompt, anim_prompt = build_lithen_prompts()
    uid = f"{int(time.time() * 1000)}_{random.randint(100, 999)}"

    # 1. If user configured a Hugging Face Token (hf_...), try direct HF Serverless Inference Router first
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
            except Exception as e:
                print(f"[HuggingFace Router] Weiter zu nächstem Live-Generator ({e})")
                break

    # 2. Fast Non-Blocking FLUX.1 Gradio Space API (line-by-line SSE reader that immediately skips on ZeroGPU quota/heartbeat)
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
            req = urllib.request.Request(
                call_url,
                data=json.dumps({"data": space_data}).encode("utf-8"),
                headers=headers,
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=6) as resp:
                event_id = json.loads(resp.read().decode("utf-8")).get("event_id")

            if event_id:
                sse_req = urllib.request.Request(f"{call_url}/{event_id}", headers=headers)
                with urllib.request.urlopen(sse_req, timeout=10) as sse:
                    current_event = None
                    while time.time() - t0 < 12.0:
                        raw_line = sse.readline()
                        if not raw_line:
                            break
                        line = raw_line.decode("utf-8", errors="replace").strip()
                        if line.startswith("event: "):
                            current_event = line[7:].strip()
                            if current_event in ("error", "heartbeat"):
                                break
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
                                        try:
                                            os.remove(raw_webp)
                                        except Exception:
                                            pass
                                        print(f"[FLUX.1 Live] Neues Lithen-Cover generiert ({space_base}): {pool_name}")
                                        return pool_path, anim_prompt
        except Exception as e:
            print(f"[FLUX.1 Space API] Weiter zu Direkt-Generator ({space_base}: {e})")

    # 3. Unlimited Keyless Live AI Generator (~2.5s response time, zero ZeroGPU quota limit)
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
                    try:
                        os.remove(raw_jpg)
                    except Exception:
                        pass
                    print(f"[Live AI Generator] Neues Lithen-Cover generiert (2.5s Direkt-API): {pool_name}")
                    return pool_path, anim_prompt
    except Exception as e:
        print(f"[Live AI Generator] Fallback auf Pool: {e}")

    return None, None

GEMINI_IMAGE_QUOTA_ZERO = False

def generate_live_gemini_artwork(api_key, project_name):
    """Calls Google Gemini Image Generation if the API key has image quota enabled (Pay-as-you-go / Tier 1)."""
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
            try:
                err_body = e.read().decode("utf-8", errors="replace")
            except Exception:
                pass
            if e.code == 429 and "limit: 0" in err_body:
                GEMINI_IMAGE_QUOTA_ZERO = True
                print("[Info] Google Free-Tier API Key hat limit: 0 fuer Bild-Modelle -> nutze Hugging Face / Lithen Night-Cam Pool.")
                return None, None
        except Exception:
            pass

    return None, None

def get_active_project_artwork_hashes(exclude_project=None):
    """Returns MD5 hashes of artworks currently displayed in active projects (PROJECTS_DIR)."""
    active = set()
    if os.path.exists(PROJECTS_DIR):
        for d in os.listdir(PROJECTS_DIR):
            if exclude_project and d == exclude_project:
                continue
            art_file = os.path.join(PROJECTS_DIR, d, "artwork.jpg")
            if os.path.isfile(art_file):
                h = file_md5(art_file)
                if h:
                    active.add(h)
    return active

def get_all_used_artwork_hashes(exclude_project=None):
    cfg = get_config()
    used = set(cfg.get("used_artwork_hashes", []))
    gdrive = cfg.get("gdrive_path", "").strip().strip('"').strip("'")

    search_roots = [PROJECTS_DIR, TRASH_DIR]
    if gdrive and os.path.exists(gdrive):
        search_roots.append(gdrive)

    for root_dir in search_roots:
        if not os.path.exists(root_dir):
            continue
        for d in os.listdir(root_dir):
            if exclude_project and d == exclude_project:
                continue
            art_file = os.path.join(root_dir, d, "artwork.jpg")
            if os.path.isfile(art_file):
                h = file_md5(art_file)
                if h:
                    used.add(h)
    return used

def synthesize_unique_vvs_edition(src_img_path, dest_img_path):
    """Synthesizes a 100% unique Lithen lo-fi old digital camera green night edition."""
    return apply_lithen_finishing_grade(src_img_path, dest_img_path, subtle=False)

def natural_sort_key(s):
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', os.path.basename(s))]

def assign_unique_artwork(p_dir, project_name, force_new=False):
    with _ARTWORK_LOCK:
        cfg = get_config()
        hf_key = cfg.get("hf_api_key", "").strip() or os.environ.get("HF_TOKEN", "").strip() or os.environ.get("HUGGINGFACE_API_KEY", "").strip()
        api_key = cfg.get("gemini_api_key", "").strip() or os.environ.get("GEMINI_API_KEY", "").strip()

        # 1. ALWAYS try Live AI generation first (works with hf_key, FLUX Space, and 2.5s Keyless Live AI API)
        live_path, live_prompt = generate_live_hf_artwork(hf_key, project_name)
        if live_path and os.path.exists(live_path):
            safe_copy_file(live_path, os.path.join(p_dir, "artwork.jpg"))
            h = file_md5(live_path)
            used_list = cfg.get("used_artwork_hashes", [])
            if h and h not in used_list:
                used_list.append(h)
                cfg["used_artwork_hashes"] = used_list
                save_config(cfg)
            return live_prompt

        # 2. Try Live Gemini Image generation if Gemini API key has image quota enabled
        if api_key:
            live_path, live_prompt = generate_live_gemini_artwork(api_key, project_name)
            if live_path and os.path.exists(live_path):
                safe_copy_file(live_path, os.path.join(p_dir, "artwork.jpg"))
                h = file_md5(live_path)
                used_list = cfg.get("used_artwork_hashes", [])
                if h and h not in used_list:
                    used_list.append(h)
                    cfg["used_artwork_hashes"] = used_list
                    save_config(cfg)
                return live_prompt

        # 3. Pick strictly unused Lithen Green-Night image from artwork_pool (NEVER repeat an active project's image!)
        active_hashes = get_active_project_artwork_hashes(exclude_project=project_name)
        used_hashes = get_all_used_artwork_hashes(exclude_project=None if force_new else project_name)
        current_art = os.path.join(p_dir, "artwork.jpg")
        if os.path.isfile(current_art):
            cur_h = file_md5(current_art)
            if cur_h:
                active_hashes.add(cur_h)
                if force_new:
                    used_hashes.add(cur_h)

        pool_images = sorted(
            [
                os.path.join(ARTWORK_POOL_DIR, f)
                for f in os.listdir(ARTWORK_POOL_DIR)
                if f.lower().endswith((".jpg", ".png")) and not f.startswith("_") and os.path.isfile(os.path.join(ARTWORK_POOL_DIR, f))
            ],
            key=natural_sort_key
        )

        # First priority: never used anywhere (not in used_hashes AND not in active_hashes)
        chosen_art = None
        for img_path in pool_images:
            h = file_md5(img_path)
            if h not in used_hashes and h not in active_hashes:
                chosen_art = img_path
                break

        # Second priority: not used by any active project in PROJECTS_DIR right now
        if not chosen_art:
            non_active_candidates = [img_path for img_path in pool_images if file_md5(img_path) not in active_hashes]
            if non_active_candidates:
                chosen_art = random.choice(non_active_candidates)

        if chosen_art:
            chosen_h = file_md5(chosen_art)
            if chosen_h in used_hashes and synthesize_unique_vvs_edition(chosen_art, current_art):
                pass
            else:
                safe_copy_file(chosen_art, current_art)
            h = file_md5(current_art)
            used_list = list(get_all_used_artwork_hashes())
            if h and h not in used_list:
                used_list.append(h)
            cfg["used_artwork_hashes"] = used_list
            save_config(cfg)
            bname = os.path.basename(chosen_art)
            if bname in POOL_PROMPTS:
                return POOL_PROMPTS[bname]
            _, anim_prompt = build_lithen_prompts()
            return anim_prompt
        elif pool_images:
            base_art = random.choice(pool_images)
            if not synthesize_unique_vvs_edition(base_art, current_art):
                safe_copy_file(base_art, current_art)
            bname = os.path.basename(base_art)
            if bname in POOL_PROMPTS:
                return POOL_PROMPTS[bname]
        _, anim_prompt = build_lithen_prompts()
        return anim_prompt

    return DEFAULT_LITHEN_ANIM_PROMPT

def sync_project_to_drive(project_name):
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
            # Nur kopieren wenn neu oder geändert
            if not os.path.exists(d) or os.path.getsize(s) != os.path.getsize(d):
                shutil.copy2(s, d)
            synced_files.append(item)

    return True, synced_files

def is_project_backed_up(project_name):
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

RENDER_JOBS = {}
RENDER_LOCK = threading.Lock()

def format_mmss(seconds):
    seconds = max(0, int(seconds))
    m, s = divmod(seconds, 60)
    return f"{m:02d}:{s:02d}"

def get_audio_duration(mp3_path):
    try:
        res = subprocess.run(
            [FFMPEG_PATH, "-i", mp3_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        m = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", res.stderr)
        if m:
            h, mins, secs = int(m.group(1)), int(m.group(2)), float(m.group(3))
            return max(5.0, h * 3600 + mins * 60 + secs)
    except Exception:
        pass
    return 150.0

def run_ffmpeg_tracked(cmd, target_duration, job, stage_prefix, weight_start, weight_end):
    """Runs FFmpeg with -progress pipe:1 and updates RENDER_JOBS live."""
    full_cmd = [cmd[0], "-y", "-progress", "pipe:1", "-nostats"] + cmd[2:]
    proc = subprocess.Popen(
        full_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1
    )
    cur_sec = 0.0
    tail_lines = []
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

    proc.wait()
    return proc.returncode == 0, "\n".join(tail_lines)

def build_main_video_cmd(p_dir):
    mp3_path = os.path.join(p_dir, "beat.mp3")
    output_video = os.path.join(p_dir, "final_youtube_video.mp4")
    video_loop = os.path.join(p_dir, "video_loop.mp4")
    artwork_path = os.path.join(p_dir, "artwork.jpg")

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
        sparkle_loop = os.path.join(BASE_DIR, "sparkle_loop_20s.mp4")
        return [
            FFMPEG_PATH, "-y",
            "-loop", "1", "-r", "30", "-i", artwork_path,
            "-stream_loop", "-1", "-i", sparkle_loop,
            "-i", mp3_path,
            "-filter_complex", "[0:v]scale=2560:1440,format=gbrp[bg];[1:v]scale=2560:1440,format=gbrp[sp];[bg][sp]blend=all_mode=addition,format=yuv420p[v]",
            "-map", "[v]", "-map", "2:a",
            "-c:v", "libx264", "-preset", "veryfast",
            "-c:a", "aac", "-b:a", "320k",
            "-pix_fmt", "yuv420p",
            "-shortest",
            "-movflags", "+faststart",
            output_video
        ]

def build_short_video_cmd(p_dir, beat_duration, short_start=12.0, short_duration=30.0):
    mp3_path = os.path.join(p_dir, "beat.mp3")
    output_short = os.path.join(p_dir, "short_reel_video.mp4")
    video_loop = os.path.join(p_dir, "video_loop.mp4")
    main_video = os.path.join(p_dir, "final_youtube_video.mp4")
    artwork_path = os.path.join(p_dir, "artwork.jpg")

    project_name = os.path.basename(p_dir)
    analysis = analyze_beat_audio(p_dir, project_name, force=False)
    bpm = analysis.get("bpm", 140)
    key_str = analysis.get("key", "C Minor")

    actual_start = float(short_start) if beat_duration > (float(short_start) + 15.0) else 0.0
    clip_dur = min(float(short_duration), max(10.0, beat_duration - actual_start))
    fade_out_st = max(0.0, clip_dur - 2.0)
    af_filter = f"afade=t=in:st=0:d=1.0,afade=t=out:st={fade_out_st:.2f}:d=2.0"

    # White bottom-center typography:
    # - From 5s: <KEY> · <BPM> BPM (smooth fade-in)
    # - From 10s: "listen full version now" (smooth fade-in)
    info_text = f"{key_str.upper()}  ·  {bpm} BPM"
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

    source_vid = video_loop if os.path.exists(video_loop) else (main_video if os.path.exists(main_video) else None)
    if source_vid:
        cmd = [
            FFMPEG_PATH, "-y",
            "-stream_loop", "-1", "-i", source_vid,
            "-ss", f"{actual_start:.2f}", "-t", f"{clip_dur:.2f}", "-i", mp3_path,
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-t", f"{clip_dur:.2f}",
            "-c:v", "libx264", "-preset", "veryfast",
            "-vf", vf_9_16,
            "-af", af_filter,
            "-c:a", "aac", "-b:a", "320k",
            "-pix_fmt", "yuv420p",
            "-shortest",
            "-movflags", "+faststart",
            output_short
        ]
    else:
        cmd = [
            FFMPEG_PATH, "-y",
            "-loop", "1", "-r", "30", "-i", artwork_path,
            "-ss", f"{actual_start:.2f}", "-t", f"{clip_dur:.2f}", "-i", mp3_path,
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-t", f"{clip_dur:.2f}",
            "-c:v", "libx264", "-preset", "veryfast",
            "-vf", vf_9_16,
            "-af", af_filter,
            "-c:a", "aac", "-b:a", "320k",
            "-pix_fmt", "yuv420p",
            "-shortest",
            "-movflags", "+faststart",
            output_short
        ]
    return cmd, clip_dur

def render_pipeline_worker(project_name, mode="both", short_start=12.0, short_duration=30.0):
    p_dir = os.path.join(PROJECTS_DIR, project_name)
    mp3_path = os.path.join(p_dir, "beat.mp3")
    beat_duration = get_audio_duration(mp3_path)

    job = RENDER_JOBS[project_name]
    try:
        # Stage 1: Main 1440p 16:9 YouTube Video
        if mode in ("both", "main_only"):
            job["stage"] = "main_video"
            job["stage_label"] = "1/3 · Rendere 1440p YouTube Hauptvideo (16:9)..." if mode == "both" else "1/2 · Rendere 1440p YouTube Hauptvideo (16:9)..."
            w_end = 65 if mode == "both" else 92
            cmd_main = build_main_video_cmd(p_dir)
            ok, err_log = run_ffmpeg_tracked(cmd_main, beat_duration, job, "main", 2, w_end)
            if not ok:
                raise RuntimeError(f"Fehler beim Rendern des Hauptvideos: {err_log[-300:]}")
            job["main_percent"] = 100

        # Stage 2: 9:16 Vertical Short / Instagram Reel
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
        if mode == "both":
            job["stage_label"] = "Pipeline abgeschlossen: 1440p Hauptvideo & 9:16 Short/Reel fertig!"
        elif mode == "short_only":
            job["stage_label"] = "9:16 Short / Instagram Reel fertig gerendert!"
        else:
            job["stage_label"] = "1440p YouTube Hauptvideo fertig gerendert!"
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

def start_render_pipeline(project_name, mode="both", short_start=12.0, short_duration=30.0):
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
            "short_percent": 0,
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

PITCH_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

def analyze_beat_audio(p_dir, safe_name, force=False):
    """Detects BPM, Musical Key (Tonart), Spectral Mood, and Bar-Accurate Timestamps from beat.mp3."""
    analysis_file = os.path.join(p_dir, "analysis.json")
    if not force and os.path.exists(analysis_file):
        try:
            with open(analysis_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass

    mp3_path = os.path.join(p_dir, "beat.mp3")
    duration = get_audio_duration(mp3_path) if os.path.exists(mp3_path) else 150.0

    bpm = 140
    key_str = "C Minor"
    sub_ratio = 0.45
    mid_ratio = 0.35
    high_ratio = 0.20
    crest = 4.5

    if os.path.exists(mp3_path):
        try:
            start_s = 10.0 if duration > 35.0 else 0.0
            cmd = [
                FFMPEG_PATH, "-nostdin", "-ss", str(start_s), "-t", "40",
                "-i", mp3_path, "-ac", "1", "-ar", "22050", "-f", "s16le", "-"
            ]
            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=20)
            pcm = np.frombuffer(proc.stdout, dtype=np.int16).astype(np.float32) / 32768.0

            if len(pcm) > 22050 * 4:
                sr = 22050
                # 1. Onset Envelope Autocorrelation for BPM Detection
                hop = 256
                n_frames = len(pcm) // hop
                frames = pcm[:n_frames * hop].reshape((n_frames, hop))
                rms_env = np.sqrt(np.mean(frames ** 2, axis=1) + 1e-9)
                onset = np.maximum(0.0, np.diff(rms_env))
                onset = onset - np.mean(onset)

                fps = sr / float(hop)  # ~86.133 Hz
                min_lag = int(fps * 60.0 / 185.0)
                max_lag = int(fps * 60.0 / 75.0)
                if len(onset) > max_lag + 10:
                    fft_len = 1 << (len(onset) * 2 - 1).bit_length()
                    spec = np.fft.rfft(onset, n=fft_len)
                    acorr = np.fft.irfft(spec * np.conj(spec), n=fft_len)[:max_lag + 1]
                    window_ac = acorr[min_lag:max_lag + 1]
                    best_lag = min_lag + int(np.argmax(window_ac))
                    raw_bpm = 60.0 * fps / float(best_lag)
                    while raw_bpm < 106.0:
                        raw_bpm *= 2.0
                    while raw_bpm > 182.0:
                        raw_bpm /= 2.0
                    bpm = int(round(raw_bpm))

                # 2. Krumhansl-Schmuckler Chromagram for Key (Tonart) Detection & Spectral Ratios
                win_size = 4096
                step = 2048
                n_stft = max(1, (len(pcm) - win_size) // step)
                hann = np.hanning(win_size)
                freqs = np.fft.rfftfreq(win_size, d=1.0 / sr)
                chroma = np.zeros(12, dtype=np.float64)

                sub_mask = (freqs >= 28) & (freqs <= 115)
                mid_mask = (freqs > 200) & (freqs <= 1800)
                high_mask = (freqs > 3200) & (freqs <= 10000)
                sub_e, mid_e, high_e = 0.0, 0.0, 0.0

                harm_mask = (freqs >= 65.0) & (freqs <= 1600.0)
                harm_freqs = freqs[harm_mask]
                midi_bins = np.round(12.0 * np.log2(harm_freqs / 440.0) + 69.0).astype(int) % 12

                for i in range(0, n_stft * step, step):
                    seg = pcm[i:i + win_size] * hann
                    mag = np.abs(np.fft.rfft(seg))
                    mag_sq = mag ** 2
                    sub_e += float(np.sum(mag_sq[sub_mask]))
                    mid_e += float(np.sum(mag_sq[mid_mask]))
                    high_e += float(np.sum(mag_sq[high_mask]))
                    harm_mag = mag[harm_mask]
                    for pc in range(12):
                        chroma[pc] += float(np.sum(harm_mag[midi_bins == pc]))

                tot_e = sub_e + mid_e + high_e + 1e-9
                sub_ratio = round(sub_e / tot_e, 3)
                mid_ratio = round(mid_e / tot_e, 3)
                high_ratio = round(high_e / tot_e, 3)
                crest = round(float(np.max(np.abs(pcm)) / (np.sqrt(np.mean(pcm ** 2)) + 1e-6)), 2)

                # Krumhansl-Kessler profiles (weighted for modern Minor-dominant Trap/Hip-Hop)
                minor_prof = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])
                major_prof = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
                if np.sum(chroma) > 0:
                    chroma_norm = (chroma - np.mean(chroma)) / (np.std(chroma) + 1e-9)
                    best_score = -999.0
                    for root in range(12):
                        rot = np.roll(chroma_norm, -root)
                        min_sc = float(np.dot(rot, (minor_prof - np.mean(minor_prof)) / np.std(minor_prof))) * 1.08
                        maj_sc = float(np.dot(rot, (major_prof - np.mean(major_prof)) / np.std(major_prof)))
                        if min_sc > best_score:
                            best_score = min_sc
                            key_str = f"{PITCH_NAMES[root]} Minor"
                        if maj_sc > best_score + 0.35:
                            best_score = maj_sc
                            key_str = f"{PITCH_NAMES[root]} Major"
        except Exception as e:
            print("Audio DSP analysis fallback:", e)

    # Check if producer filename explicitly specifies BPM or Key (e.g. back13_f_164, back18_c_153, back19_e_110)
    tokens = re.split(r'[_\-\s]+', safe_name.lower())
    for tok in reversed(tokens):
        if tok.isdigit() and 75 <= int(tok) <= 195:
            bpm = int(tok)
            break
    note_map = {
        "c": "C Minor", "cm": "C Minor", "csharp": "C# Minor", "db": "C# Minor",
        "d": "D Minor", "dm": "D Minor", "dsharp": "D# Minor", "eb": "D# Minor",
        "e": "E Minor", "em": "E Minor", "f": "F Minor", "fm": "F Minor",
        "fsharp": "F# Minor", "gb": "F# Minor", "g": "G Minor", "gm": "G Minor",
        "gsharp": "G# Minor", "ab": "G# Minor", "a": "A Minor", "am": "A Minor",
        "asharp": "A# Minor", "bb": "A# Minor", "b": "B Minor", "bm": "B Minor"
    }
    for tok in tokens[1:]:
        if tok in note_map:
            key_str = note_map[tok]
            break

    # Classify Sonic Vibe & Instruments from BPM + Spectral Ratios
    if bpm >= 156:
        if high_ratio > 0.12:
            vibe = "Hypnotic Up-Tempo Rage & Dark Futuristic Trap"
            instruments = "Heavy Distorted 808s, Wide Synth Leads & Crisp Fast Hi-Hats"
        else:
            vibe = "Hard Driving Dark Street Trap & Heavy 808 Bounce"
            instruments = "Deep Sub-808s, Dark Bell Plucks & Orchestral Brass Accents"
    elif bpm >= 136:
        if mid_ratio > 0.32:
            vibe = "Melodic Luxury Trap & Cinematic Night Atmosphere"
            instruments = "Atmospheric Vintage Keys, Lush Choir Pads & Punchy Spinz 808"
        else:
            vibe = "Dark Heavy VVS Trap & Nocturnal Club Bounce"
            instruments = "Sub-Heavy 808s, Haunting Flute/String Motif & Crisp Percussion"
    else:
        if mid_ratio > 0.30:
            vibe = "Smooth Late-Night Melodic Trap & Soulful Bounce"
            instruments = "Warm Rhodes Chords, Ambient Vocal Textures & Deep Glide 808"
        else:
            vibe = "Dark Slow-Burn Psychedelic Luxury Trap"
            instruments = "Filtered Analog Synths, Deep Sub-Bass & Spacious Trap Drums"

    # Compute Bar-Accurate Timestamps from BPM (4 beats per bar)
    bar_sec = 240.0 / float(max(80, bpm))
    t_intro = 0
    t_hook1 = int(round(8 * bar_sec))
    t_verse1 = int(round(24 * bar_sec))
    t_hook2 = int(round(40 * bar_sec))
    t_verse2 = int(round(56 * bar_sec))
    t_outro = int(round(min(duration - 10, max(t_verse2 + 8 * bar_sec, duration - 8 * bar_sec))))

    timestamps = [
        ("0:00", "Intro"),
        (format_mmss(t_hook1), "Hook / Drop"),
        (format_mmss(min(int(duration * 0.35), t_verse1)), "Verse 1"),
        (format_mmss(min(int(duration * 0.55), t_hook2)), "Hook 2"),
        (format_mmss(min(int(duration * 0.75), t_verse2)), "Verse 2"),
        (format_mmss(max(int(duration * 0.86), t_outro)), "Outro"),
    ]

    result = {
        "bpm": bpm,
        "key": key_str,
        "duration": round(duration, 1),
        "duration_str": format_mmss(duration),
        "drop_sec": round(float(t_hook1), 1),
        "vibe": vibe,
        "instruments": instruments,
        "sub_ratio": sub_ratio,
        "mid_ratio": mid_ratio,
        "high_ratio": high_ratio,
        "crest": crest,
        "timestamps": timestamps,
    }
    try:
        with open(analysis_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
    except Exception:
        pass
    return result

def call_gemini_metadata_agent(api_key, safe_name, analysis):
    """Calls Gemini LLM Agent to craft bespoke YouTube Titles, Artist Pairings, Description & IG Reel Caption based on actual audio analysis."""
    if not api_key:
        return None
    bpm = analysis["bpm"]
    key_str = analysis["key"]
    vibe = analysis["vibe"]
    instruments = analysis["instruments"]
    ts_lines = "\n".join([f"{t} - {lbl}" for t, lbl in analysis["timestamps"]])

    prompt = (
        f"Du bist ein erfahrener Hip-Hop/Trap A&R und YouTube SEO-Strategist für den Producer-Kanal 'prodbyJMD'.\n"
        f"Analysiere folgendes Instrumental und erstelle EINZIGARTIGE, abwechslungsreiche YouTube- und Instagram-Metadaten.\n\n"
        f"Gemessene Audio-Daten des Beats '{safe_name.upper()}':\n"
        f"- Tempo: {bpm} BPM\n"
        f"- Tonart (Key): {key_str}\n"
        f"- Klangcharakter / Vibe: {vibe}\n"
        f"- Dominante Elemente: {instruments}\n"
        f"- Länge: {analysis['duration_str']}\n\n"
        f"WICHTIGE REGELN FÜR KÜNSTLER-AUSWAHL & VARIATION:\n"
        f"- Wähle KEINE langweiligen Standard-Templates! Wähle für die 3 Titel-Optionen 3 KOMPLETT UNTERSCHIEDLICHE, aber zum Tempo ({bpm} BPM), Key ({key_str}) und Vibe ({vibe}) perfekt passende Künstler-Paarungen (z.B. aus: Don Toliver, Nemzzz, Central Cee, Key Glock, Offset, Baby Keem, Ken Carson, Yeat, Metro Boomin, Future, Lil Baby, 21 Savage, Sleepy Hallow, Destroy Lonely, Luciano, Pashanim, Reezy, Gunna, Lil Durk, Est Gee, Playboi Carti, Bryson Tiller, Young Thug, Travis Scott).\n"
        f"- Erfinde für jeden der 3 Titel einen starken, zum Vibe passenden englischen Song-Beinamen in Anführungszeichen.\n"
        f"- Nutze exakt das folgende Markdown-Format:\n\n"
        f"# 💎 Release Metadata: {safe_name.upper()} ({bpm} BPM · {key_str})\n\n"
        f"## 🎯 Individuelle YouTube Titel-Vorschläge (KI-kuratiert)\n"
        f"1. [FREE] <Artist A> x <Artist B> Type Beat 2026 - \"<Creative Name 1>\" | {bpm} BPM ({key_str})\n"
        f"2. [FREE] <Artist C> x <Artist D> Type Beat - \"<Creative Name 2>\" (prod. prodbyJMD)\n"
        f"3. <Artist E> x <Artist F> Type Beat 2026 - \"<Creative Name 3>\" | <Vibe Keyword> Instrumental\n\n"
        f"---\n\n"
        f"## 📝 YouTube Beschreibung (16:9 Hauptvideo)\n"
        f"```text\n"
        f"💎 Beat kaufen / Lease: [DEIN BEATSTARS LINK]\n"
        f"📸 Instagram: @prodbyJMD\n"
        f"📧 Kontakt / Business: [DEINE MAILADRESSE]\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🎹 Beat & Audio-Analyse:\n"
        f"• Projekt: \"{safe_name.upper()}\"\n"
        f"• Prod. by: prodbyJMD\n"
        f"• Tempo: {bpm} BPM\n"
        f"• Tonart (Key): {key_str}\n"
        f"• Sound / Vibe: {vibe}\n"
        f"• Produktion: {instruments}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"⏳ Timestamps (berechnet auf {bpm} BPM):\n"
        f"{ts_lines}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"⚠️ USAGE TERMS:\n"
        f"Free for non-profit use on YouTube and SoundCloud only (credit \"prod. prodbyJMD\" in title).\n"
        f"For commercial use (Spotify, Apple Music, etc.), purchase a license via BeatStars.\n\n"
        f"#typebeat #prodbyjmd #<artist1>typebeat #<artist2>typebeat\n"
        f"```\n\n"
        f"---\n\n"
        f"## 📱 Instagram Reel & YouTube Shorts Caption (9:16)\n"
        f"```text\n"
        f"<Individueller 2-zeiliger Hook-Text passend zu {bpm} BPM & {key_str} + Frage welche Artists drauf passen>\n\n"
        f"🎹 {bpm} BPM | {key_str} | Prod. by @prodbyJMD\n"
        f"🔗 Full 1440p Beat on YouTube: prodbyJMD\n\n"
        f"<12 passende Hashtags inkl. #prodbyjmd #reelsinstagram #shorts>\n"
        f"```\n\n"
        f"---\n\n"
        f"## 🏷️ YouTube Studio Tags (Komma-getrennt)\n"
        f"<15 spezifische SEO Tags passend zu den gewählten Künstlern, {bpm} bpm, {key_str}, prodbyjmd>\n"
    )

    for model_name in ["gemini-3.5-flash", "gemini-flash-latest", "gemini-3.6-flash"]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.92}
        }
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                cands = data.get("candidates", [])
                if cands:
                    parts = cands[0].get("content", {}).get("parts", [])
                    text = "".join([p.get("text", "") for p in parts]).strip()
                    if len(text) > 200:
                        return text
        except Exception as e:
            print(f"Gemini metadata agent ({model_name}) fallback:", e)
    return None

def generate_metadata_markdown(safe_name, p_dir=None, force_refresh=False):
    if p_dir is None:
        p_dir = os.path.join(PROJECTS_DIR, safe_name)

    analysis = analyze_beat_audio(p_dir, safe_name, force=force_refresh)
    cfg = get_config()
    api_key = cfg.get("gemini_api_key", "").strip() or os.environ.get("GEMINI_API_KEY", "").strip()

    # 1. Try Live Gemini AI Agent first
    ai_md = call_gemini_metadata_agent(api_key, safe_name, analysis)
    if ai_md:
        return ai_md

    # 2. Acoustic A&R Agent (uses real measured BPM, Key, Spectral Ratios & unique beat seed for wide artist diversity)
    bpm = analysis["bpm"]
    key_str = analysis["key"]
    vibe = analysis["vibe"]
    instruments = analysis["instruments"]
    ts_lines = "\n".join([f"{t} - {lbl}" for t, lbl in analysis["timestamps"]])

    seed_int = int(hashlib.md5(f"{safe_name}_{bpm}_{key_str}_{analysis['sub_ratio']}_{analysis['mid_ratio']}".encode()).hexdigest()[:8], 16)
    rng = random.Random(seed_int)

    if bpm >= 156:
        # Fast / High-Energy / Opium / Up-Tempo Street Trap pools
        pool_a = [
            ("Yeat x Ken Carson", "OVERLOAD", "Futuristic Rage & Heavy 808"),
            ("Playboi Carti x Destroy Lonely", "NIGHTVISION", "Dark Opium Synth"),
            ("Future x Lil Durk", "NO MERCY", "Hard Up-Tempo Street Trap"),
            ("Key Glock x Young Dolph", "GLOCKOMA", "Hard Memphis 808 Bounce"),
            ("Nemzzz x Central Cee", "LONDON NIGHTS", "Melodic Fast Bounce"),
            ("Travis Scott x Baby Keem", "HYPNOTIC", "High Energy Stadium Trap"),
            ("Offset x 21 Savage", "RICOCHET", "Dark Fast Hi-Hat Trap"),
            ("Luciano x Reezy", "MAYBACH", "Heavy Euro-Trap Bounce"),
        ]
    elif bpm >= 136:
        # Mid-Fast / Melodic Luxury / Dark Trap pools
        pool_a = [
            ("Don Toliver x Metro Boomin", "MIDNIGHT VVS", "Cinematic Dark Luxury"),
            ("Gunna x Lil Baby", "CARTIER LENS", "Smooth Luxury Trap"),
            ("Future x Offset", "OBSIDIAN", "Dark Heavy 808 Trap"),
            ("Central Cee x Dave", "MAYFAIR", "Nocturnal Melodic Trap"),
            ("Baby Keem x Kendrick Lamar", "CROWN JEWELS", "Left-Field Hard Trap"),
            ("Pashanim x Nemzzz", "PARISIENNE", "Atmospheric Late-Night Vibe"),
            ("21 Savage x Est Gee", "COLD BLOODED", "Gritty Dark Piano Trap"),
            ("Young Thug x Gunna", "EMERALD CUT", "Wavy Melodic Guitar & 808"),
        ]
    else:
        # Slower / Late-Night / Psychedelic / Smooth Bounce pools
        pool_a = [
            ("Don Toliver x Travis Scott", "AFTERHOURS", "Psychedelic Late-Night"),
            ("Sleepy Hallow x Sheff G", "BLUE SMOKE", "Melodic Sample Bounce"),
            ("Bryson Tiller x PARTYNEXTDOOR", "VELVET ROOM", "Dark Trapsoul & 808"),
            ("Future x Drake", "PENTHOUSE VIEW", "Late-Night Luxury Flow"),
            ("Lil Tecca x Cash Cobain", "CHAMPAGNE", "Bouncy Melodic Vibe"),
            ("Metro Boomin x The Weeknd", "ECLIPSE", "Cinematic Dark Synth"),
            ("Reezy x Luciano", "MONACO", "Smooth Nightrider Trap"),
            ("Baby Keem x Don Toliver", "STARLIGHT", "Ambient Melodic Trap"),
        ]

    picks = rng.sample(pool_a, 3)
    (art1, code1, sub1), (art2, code2, sub2), (art3, code3, sub3) = picks
    lead_artists = f"{art1.split(' x ')[0]}, {art1.split(' x ')[1]} or {art2.split(' x ')[0]}"

    tag_artists = [
        art1.split(" x ")[0].lower(), art1.split(" x ")[1].lower(),
        art2.split(" x ")[0].lower(), art2.split(" x ")[1].lower(),
        art3.split(" x ")[0].lower()
    ]
    seo_tags = ", ".join([
        f"{a} type beat 2026" for a in tag_artists
    ] + [
        f"{bpm} bpm type beat", f"{key_str.lower()} type beat",
        f"{safe_name.lower()} instrumental", "dark luxury trap beat",
        "prodbyjmd", "prodbyjmd beats"
    ])

    ht_1 = "#" + tag_artists[0].replace(" ", "") + "typebeat"
    ht_2 = "#" + tag_artists[1].replace(" ", "") + "typebeat"
    ht_3 = "#" + tag_artists[2].replace(" ", "") + "typebeat"

    return (
        f"# 💎 Release Metadata: {safe_name.upper()} ({bpm} BPM · {key_str})\n\n"
        f"## 🎯 Individuelle YouTube Titel-Vorschläge (Audio-analysiert)\n"
        f"1. [FREE] {art1} Type Beat 2026 - \"{code1}\" | {bpm} BPM ({key_str})\n"
        f"2. [FREE] {art2} Type Beat - \"{code2} ({safe_name.upper()})\" (prod. prodbyJMD)\n"
        f"3. {art3} Type Beat 2026 - \"{code3}\" | {sub3} Instrumental\n\n"
        f"---\n\n"
        f"## 📝 YouTube Beschreibung (16:9 Hauptvideo)\n"
        f"```text\n"
        f"💎 Beat kaufen / Lease: [DEIN BEATSTARS LINK]\n"
        f"📸 Instagram: @prodbyJMD\n"
        f"📧 Kontakt / Business: [DEINE MAILADRESSE]\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🎹 Beat & Audio-Analyse:\n"
        f"• Titel: \"{safe_name.upper()}\" ({code1})\n"
        f"• Prod. by: prodbyJMD\n"
        f"• Tempo: {bpm} BPM\n"
        f"• Tonart (Key): {key_str}\n"
        f"• Vibe: {vibe}\n"
        f"• Elemente: {instruments}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"⏳ Timestamps (berechnet auf {bpm} BPM):\n"
        f"{ts_lines}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"⚠️ USAGE TERMS:\n"
        f"Free for non-profit use on YouTube and SoundCloud only (credit \"prod. prodbyJMD\" in title).\n"
        f"For commercial use (Spotify, Apple Music, etc.), purchase a license via BeatStars.\n\n"
        f"#typebeat #prodbyjmd {ht_1} {ht_2} {ht_3}\n"
        f"```\n\n"
        f"---\n\n"
        f"## 📱 Instagram Reel & YouTube Shorts Caption (9:16)\n"
        f"```text\n"
        f"💎 \"{code1}\" ({safe_name.upper()}) – {bpm} BPM in {key_str} ❄️🔥\n"
        f"Who goes crazy on this {sub1.lower()} bounce? {lead_artists}? 👇\n\n"
        f"🎹 {bpm} BPM · {key_str} · Prod. by @prodbyJMD\n"
        f"🔗 Full 1440p Beat on YouTube: prodbyJMD\n\n"
        f"#typebeat #trapbeats #flstudio #beatmaker {ht_1} {ht_2} {ht_3} #darktrap #vvs #prodbyjmd #reelsinstagram #shorts\n"
        f"```\n\n"
        f"---\n\n"
        f"## 🏷️ YouTube Studio Tags (Komma-getrennt)\n"
        f"{seo_tags}\n"
    )

class FlytHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        # Suppress noisy polling logs for /api/render_status
        if len(args) > 0 and "/api/render_status" in str(args[0]):
            return
        super().log_message(format, *args)

    def handle_one_request(self):
        try:
            super().handle_one_request()
        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
            self.close_connection = True

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Range")
        super().end_headers()

    def send_json(self, data, status=200):
        body = json.dumps(data).encode("utf-8")
        try:
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
            pass

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/favicon.ico":
            self.send_response(204)
            self.end_headers()
            return

        elif path == "/api/config":
            self.send_json(get_config())
            return

        elif path == "/api/render_status":
            # Clean up old finished jobs after 15 seconds so UI stays tidy
            now = time.time()
            active_any = False
            snapshot = {}
            for k, v in list(RENDER_JOBS.items()):
                if v.get("active"):
                    active_any = True
                elif v.get("finished_at") and (now - v["finished_at"] > 12):
                    continue
                snapshot[k] = v
            self.send_json({"active_any": active_any, "jobs": snapshot})
            return

        elif path == "/api/projects":
            cfg = get_config()
            completed_set = set(cfg.get("completed_projects", []))
            projects = []
            if os.path.exists(PROJECTS_DIR):
                for name in sorted(os.listdir(PROJECTS_DIR), reverse=True):
                    if name in completed_set:
                        continue
                    p_dir = os.path.join(PROJECTS_DIR, name)
                    if os.path.isdir(p_dir):
                        analysis = analyze_beat_audio(p_dir, name, force=False)
                        dur_sec = float(analysis.get("duration_sec", 0) or 0)
                        dur_m = int(dur_sec // 60)
                        dur_s = int(dur_sec % 60)
                        dur_str = f"{dur_m}:{dur_s:02d}" if dur_sec > 0 else "--:--"
                        p_data = {
                            "name": name,
                            "path": p_dir,
                            "bpm": analysis.get("bpm"),
                            "key": analysis.get("key"),
                            "vibe": analysis.get("vibe"),
                            "drop_sec": analysis.get("drop_sec", 12.0),
                            "duration_sec": dur_sec,
                            "duration_str": dur_str,
                            "has_mp3": os.path.exists(os.path.join(p_dir, "beat.mp3")),
                            "has_artwork": os.path.exists(os.path.join(p_dir, "artwork.jpg")),
                            "has_prompt": os.path.exists(os.path.join(p_dir, "gemini_prompt.txt")),
                            "has_video_loop": os.path.exists(os.path.join(p_dir, "video_loop.mp4")),
                            "has_final_video": os.path.exists(os.path.join(p_dir, "final_youtube_video.mp4")),
                            "has_short_video": os.path.exists(os.path.join(p_dir, "short_reel_video.mp4")),
                            "has_metadata": os.path.exists(os.path.join(p_dir, "metadata.md")),
                            "has_thumbnail": os.path.exists(os.path.join(p_dir, thumbnail_gen.SELECTED_NAME)),
                            "is_backed_up": is_project_backed_up(name),
                            "render_job": RENDER_JOBS.get(name),
                            "prompt_text": "",
                            "metadata_text": ""
                        }
                        if p_data["has_prompt"]:
                            try:
                                with open(os.path.join(p_dir, "gemini_prompt.txt"), "r", encoding="utf-8") as f:
                                    p_data["prompt_text"] = f.read()
                            except Exception:
                                pass
                        if p_data["has_metadata"]:
                            try:
                                with open(os.path.join(p_dir, "metadata.md"), "r", encoding="utf-8") as f:
                                    p_data["metadata_text"] = f.read()
                            except Exception:
                                pass
                        projects.append(p_data)
            self.send_json(projects)
            return

        elif path == "/api/thumbnails":
            project_name = urllib.parse.parse_qs(parsed.query).get("project", [""])[0]
            p_dir = os.path.join(PROJECTS_DIR, project_name)
            if not project_name or not os.path.isdir(p_dir):
                self.send_json({"error": "Project not found"}, 400)
                return
            self.send_json(thumbnail_gen.thumbnail_state(p_dir, project_name))
            return

        elif path.startswith("/projects/"):
            rel_path = urllib.parse.unquote(path[len("/projects/"):])
            file_path = os.path.join(PROJECTS_DIR, rel_path)
            if os.path.exists(file_path) and os.path.isfile(file_path):
                file_size = os.path.getsize(file_path)
                if file_path.endswith((".jpg", ".jpeg")):
                    ctype = "image/jpeg"
                elif file_path.endswith(".png"):
                    ctype = "image/png"
                elif file_path.endswith(".mp4"):
                    ctype = "video/mp4"
                elif file_path.endswith(".mp3"):
                    ctype = "audio/mpeg"
                else:
                    ctype = "text/plain; charset=utf-8"

                range_header = self.headers.get("Range")
                start_byte = 0
                end_byte = file_size - 1
                status_code = 200

                if range_header and range_header.startswith("bytes="):
                    try:
                        r_parts = range_header[6:].split(",")[0].split("-")
                        if r_parts[0].strip():
                            start_byte = int(r_parts[0].strip())
                        if len(r_parts) > 1 and r_parts[1].strip():
                            end_byte = min(file_size - 1, int(r_parts[1].strip()))
                        if 0 <= start_byte <= end_byte < file_size:
                            status_code = 206
                    except Exception:
                        start_byte = 0
                        end_byte = file_size - 1
                        status_code = 200

                content_len = max(0, end_byte - start_byte + 1)
                try:
                    self.send_response(status_code)
                    self.send_header("Content-Type", ctype)
                    self.send_header("Accept-Ranges", "bytes")
                    if status_code == 206:
                        self.send_header("Content-Range", f"bytes {start_byte}-{end_byte}/{file_size}")
                    self.send_header("Cache-Control", "no-cache")
                    self.send_header("Content-Length", str(content_len))
                    self.end_headers()
                    with open(file_path, "rb") as f:
                        f.seek(start_byte)
                        remaining = content_len
                        while remaining > 0:
                            chunk = f.read(min(65536, remaining))
                            if not chunk:
                                break
                            self.wfile.write(chunk)
                            remaining -= len(chunk)
                except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
                    pass
                return
            else:
                self.send_error(404, "File not found")
                return

        elif path == "/" or path == "/index.html":
            html_file = os.path.join(BASE_DIR, "index.html")
            if os.path.exists(html_file):
                try:
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
                    self.send_header("Content-Length", str(os.path.getsize(html_file)))
                    self.end_headers()
                    with open(html_file, "rb") as f:
                        shutil.copyfileobj(f, self.wfile)
                except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
                    pass
                return

        super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        if path == "/api/config":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8")
            data = json.loads(body)
            cfg = get_config()
            if "gdrive_path" in data:
                cfg["gdrive_path"] = data["gdrive_path"].strip().strip('"').strip("'")
            if "hf_api_key" in data:
                cfg["hf_api_key"] = data["hf_api_key"].strip()
            if "gemini_api_key" in data:
                cfg["gemini_api_key"] = data["gemini_api_key"].strip()
            save_config(cfg)
            self.send_json({"success": True, "config": cfg})
            return

        elif path == "/api/complete_project":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"
            data = json.loads(body)
            project_name = data.get("project")
            if not project_name:
                self.send_json({"error": "No project name"}, 400)
                return
            try:
                sync_project_to_drive(project_name)
            except Exception:
                pass
            cfg = get_config()
            comp = cfg.get("completed_projects", [])
            if project_name not in comp:
                comp.append(project_name)
                cfg["completed_projects"] = comp
                save_config(cfg)
            self.send_json({"success": True, "project": project_name})
            return

        elif path == "/api/regenerate_metadata":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"
            data = json.loads(body)
            project_name = data.get("project")
            if not project_name:
                self.send_json({"error": "No project name"}, 400)
                return
            p_dir = os.path.join(PROJECTS_DIR, project_name)
            if not os.path.exists(p_dir):
                self.send_json({"error": "Project not found"}, 400)
                return
            meta_text = generate_metadata_markdown(project_name, p_dir=p_dir, force_refresh=True)
            with open(os.path.join(p_dir, "metadata.md"), "w", encoding="utf-8") as f:
                f.write(meta_text)
            try:
                sync_project_to_drive(project_name)
            except Exception:
                pass
            self.send_json({"success": True, "project": project_name, "metadata_text": meta_text})
            return

        elif path == "/api/regenerate_artwork":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"
            data = json.loads(body)
            project_name = data.get("project")
            if not project_name:
                self.send_json({"error": "No project name"}, 400)
                return
            p_dir = os.path.join(PROJECTS_DIR, project_name)
            if not os.path.exists(p_dir):
                self.send_json({"error": "Project not found"}, 400)
                return
            try:
                prompt_text = assign_unique_artwork(p_dir, project_name, force_new=True)
                with open(os.path.join(p_dir, "gemini_prompt.txt"), "w", encoding="utf-8") as f:
                    f.write(prompt_text)
                threading.Thread(target=sync_project_to_drive, args=(project_name,), daemon=True).start()
                self.send_json({"success": True, "project": project_name, "prompt_text": prompt_text})
            except Exception as e:
                print(f"[Error in /api/regenerate_artwork]: {e}")
                self.send_json({"error": str(e)}, 500)
            return

        elif path == "/api/generate_thumbnails":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"
            data = json.loads(body)
            project_name = data.get("project")
            p_dir = os.path.join(PROJECTS_DIR, project_name or "")
            if not project_name or not os.path.isdir(p_dir):
                self.send_json({"error": "Project not found"}, 400)
                return
            artist = (data.get("artist") or "").strip()
            if not artist:
                artist = thumbnail_gen.thumbnail_state(p_dir, project_name).get("default_artist", "")
            count = max(1, min(6, int(data.get("count", 4))))
            cfg = get_config()
            gemini_key = cfg.get("gemini_api_key", "").strip() or os.environ.get("GEMINI_API_KEY", "").strip()
            hf_key = cfg.get("hf_api_key", "").strip() or os.environ.get("HF_TOKEN", "").strip()
            job = thumbnail_gen.start_job(project_name, p_dir, artist, count, FFMPEG_PATH, gemini_key, hf_key)
            self.send_json({"success": True, "job": job})
            return

        elif path == "/api/select_thumbnail":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"
            data = json.loads(body)
            project_name = data.get("project")
            p_dir = os.path.join(PROJECTS_DIR, project_name or "")
            if not project_name or not os.path.isdir(p_dir):
                self.send_json({"error": "Project not found"}, 400)
                return
            if not thumbnail_gen.select_variant(p_dir, data.get("file", "")):
                self.send_json({"error": "Thumbnail not found"}, 400)
                return
            threading.Thread(target=sync_project_to_drive, args=(project_name,), daemon=True).start()
            self.send_json({"success": True})
            return

        elif path == "/api/sync":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"
            data = json.loads(body)
            project_name = data.get("project")

            if project_name:
                ok, res = sync_project_to_drive(project_name)
            else:
                ok = True
                res = []
                for p in os.listdir(PROJECTS_DIR):
                    if os.path.isdir(os.path.join(PROJECTS_DIR, p)):
                        s_ok, s_res = sync_project_to_drive(p)
                        if s_ok: res.append(p)

            self.send_json({"success": ok, "result": res}, 200 if ok else 400)
            return

        elif path == "/api/delete_project":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8")
            data = json.loads(body)
            project_name = data.get("project")

            if not project_name:
                self.send_json({"error": "No project name"}, 400)
                return

            p_dir = os.path.join(PROJECTS_DIR, project_name)
            if os.path.exists(p_dir):
                try:
                    sync_project_to_drive(project_name)
                except Exception:
                    pass

                dest_trash = os.path.join(TRASH_DIR, project_name)
                if os.path.exists(dest_trash):
                    shutil.rmtree(dest_trash, ignore_errors=True)
                shutil.move(p_dir, dest_trash)

            self.send_json({"success": True, "message": "Projekt aus der UI entfernt. Daten auf Google Drive bleiben gesichert."})
            return

        elif path == "/api/upload_mp3":
            raw_filename = query.get("name", [""])[0]
            filename = urllib.parse.unquote(raw_filename) if raw_filename else "beat.mp3"
            base_name = os.path.splitext(filename)[0]
            safe_name = "".join([c for c in base_name if c.isalnum() or c in ("-", "_")]).strip()
            if not safe_name: safe_name = "beat_" + str(len(os.listdir(PROJECTS_DIR)) + 1)

            cfg = get_config()
            if safe_name in cfg.get("completed_projects", []):
                cfg["completed_projects"].remove(safe_name)
                save_config(cfg)

            p_dir = os.path.join(PROJECTS_DIR, safe_name)
            os.makedirs(p_dir, exist_ok=True)

            length = int(self.headers.get("Content-Length", 0))
            mp3_bytes = self.rfile.read(length)
            with open(os.path.join(p_dir, "beat.mp3"), "wb") as f:
                f.write(mp3_bytes)

            prompt_text = assign_unique_artwork(p_dir, safe_name, force_new=False)
            with open(os.path.join(p_dir, "gemini_prompt.txt"), "w", encoding="utf-8") as f:
                f.write(prompt_text)

            meta_text = generate_metadata_markdown(safe_name, p_dir=p_dir, force_refresh=True)
            with open(os.path.join(p_dir, "metadata.md"), "w", encoding="utf-8") as f:
                f.write(meta_text)

            try:
                sync_project_to_drive(safe_name)
            except Exception:
                pass

            self.send_json({"success": True, "project": safe_name})
            return

        elif path == "/api/upload_video":
            project_name = query.get("project", [""])[0]
            if not project_name or not os.path.exists(os.path.join(PROJECTS_DIR, project_name)):
                self.send_json({"error": "Project not found"}, 400)
                return

            length = int(self.headers.get("Content-Length", 0))
            video_bytes = self.rfile.read(length)

            p_dir = os.path.join(PROJECTS_DIR, project_name)
            target_path = os.path.join(p_dir, "video_loop.mp4")
            with open(target_path, "wb") as f:
                f.write(video_bytes)

            analysis = analyze_beat_audio(p_dir, project_name, force=False)
            drop_start = analysis.get("drop_sec", 12.0)

            # Start background 2-stage render pipeline (1440p Main + 9:16 Short/Reel + Drive Sync)
            job = start_render_pipeline(project_name, mode="both", short_start=drop_start, short_duration=30.0)
            self.send_json({"success": True, "async": True, "job": job})
            return

        elif path == "/api/render":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"
            data = json.loads(body)
            project_name = data.get("project")
            mode = data.get("mode", "both")  # "both", "main_only", "short_only"

            if not project_name or not os.path.exists(os.path.join(PROJECTS_DIR, project_name)):
                self.send_json({"error": "Project not found"}, 400)
                return

            p_dir = os.path.join(PROJECTS_DIR, project_name)
            analysis = analyze_beat_audio(p_dir, project_name, force=False)
            default_drop = analysis.get("drop_sec", 12.0)
            short_start = float(data.get("short_start", default_drop))
            short_duration = float(data.get("short_duration", 30.0))

            job = start_render_pipeline(project_name, mode=mode, short_start=short_start, short_duration=short_duration)
            self.send_json({"success": True, "async": True, "job": job})
            return

        elif path == "/api/open_folder":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8")
            data = json.loads(body)
            project_name = data.get("project")
            p_dir = os.path.join(PROJECTS_DIR, project_name) if project_name else PROJECTS_DIR
            subprocess.Popen(f'explorer.exe "{p_dir}"')
            self.send_json({"success": True})
            return

class QuietThreadingHTTPServer(ThreadingHTTPServer):
    def handle_error(self, request, client_address):
        import sys
        exc = sys.exc_info()[1]
        if isinstance(exc, (ConnectionResetError, ConnectionAbortedError, BrokenPipeError)):
            return
        super().handle_error(request, client_address)

def run_server(port=4488):
    server = QuietThreadingHTTPServer(("127.0.0.1", port), FlytHandler)
    print(f"FLYT Server running at http://localhost:{port}")
    server.serve_forever()

if __name__ == "__main__":
    run_server()
