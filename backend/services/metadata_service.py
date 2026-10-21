import os
import json
import random
import hashlib
import urllib.request
from typing import Optional, Dict, Any
from backend.config import PROJECTS_DIR, get_config
from backend.services.audio_service import analyze_beat_audio

def call_gemini_metadata_agent(api_key: str, safe_name: str, analysis: Dict[str, Any]) -> Optional[str]:
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
        f"- Länge: {analysis.get('duration_str', '2:30')}\n\n"
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

    for model_name in ["gemini-2.5-flash", "gemini-3.5-flash", "gemini-flash-latest"]:
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
            print(f"[Metadata Gemini ({model_name})] Fallback:", e)
    return None

def generate_metadata_markdown(safe_name: str, p_dir: Optional[str] = None, force_refresh: bool = False) -> str:
    if p_dir is None:
        p_dir = os.path.join(PROJECTS_DIR, safe_name)

    analysis = analyze_beat_audio(p_dir, safe_name, force=force_refresh)
    cfg = get_config()
    api_key = cfg.get("gemini_api_key", "").strip() or os.environ.get("GEMINI_API_KEY", "").strip()

    # 1. Try Live Gemini
    ai_md = call_gemini_metadata_agent(api_key, safe_name, analysis)
    if ai_md:
        return ai_md

    # 2. Acoustic A&R Fallback
    bpm = analysis["bpm"]
    key_str = analysis["key"]
    vibe = analysis["vibe"]
    instruments = analysis["instruments"]
    ts_lines = "\n".join([f"{t} - {lbl}" for t, lbl in analysis["timestamps"]])

    seed_int = int(hashlib.md5(f"{safe_name}_{bpm}_{key_str}_{analysis['sub_ratio']}_{analysis['mid_ratio']}".encode()).hexdigest()[:8], 16)
    rng = random.Random(seed_int)

    if bpm >= 156:
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
