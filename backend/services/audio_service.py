import os
import re
import json
import subprocess
import numpy as np
from typing import Dict, Any, Tuple, List
from backend.config import FFMPEG_PATH

PITCH_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

def format_mmss(seconds: float) -> str:
    seconds = max(0, int(seconds))
    m, s = divmod(seconds, 60)
    return f"{m:02d}:{s:02d}"

def get_audio_duration(mp3_path: str) -> float:
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

def analyze_beat_audio(p_dir: str, safe_name: str, force: bool = False) -> Dict[str, Any]:
    """Detects BPM, Musical Key (Tonart), Spectral Mood, and Bar-Accurate Timestamps from beat.mp3."""
    analysis_file = os.path.join(p_dir, "analysis.json")
    manual_bpm = None
    manual_key = None
    if os.path.exists(analysis_file):
        try:
            with open(analysis_file, "r", encoding="utf-8") as f:
                prev = json.load(f)
                if not force:
                    return prev
                if prev.get("manual_override"):
                    manual_bpm = prev.get("bpm")
                    manual_key = prev.get("key")
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

                # 2. Krumhansl-Schmuckler Chromagram for Key Detection & Spectral Ratios
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
            print("[Audio Analysis] DSP fallback:", e)

    # Check if producer filename explicitly specifies BPM or Key
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

    # Classify Sonic Vibe & Instruments
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

    if manual_bpm is not None:
        bpm = int(manual_bpm)
    if manual_key is not None:
        key_str = str(manual_key)

    result = {
        "bpm": bpm,
        "key": key_str,
        "duration": round(duration, 1),
        "duration_sec": round(duration, 1),
        "duration_str": format_mmss(duration),
        "drop_sec": round(float(t_hook1), 1),
        "vibe": vibe,
        "instruments": instruments,
        "sub_ratio": sub_ratio,
        "mid_ratio": mid_ratio,
        "high_ratio": high_ratio,
        "crest": crest,
        "timestamps": timestamps,
        "manual_override": bool(manual_bpm or manual_key),
    }
    try:
        with open(analysis_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
    except Exception:
        pass
    return result
