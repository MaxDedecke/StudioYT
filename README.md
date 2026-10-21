# 💎 FLYT STUDIO 2.0
> **Die All-in-One Content- & Release-Plattform für Hip-Hop- & Trap-Producer.**  
> Automatisiert Audio-Analyse, KI-Artworks, 1440p YouTube-Videos, 9:16 Shorts/Reels, Thumbnail-Generierung und Google Drive Backups.

---

## 🚀 Quick Start

### 1. Plattform starten
Doppelklick auf:
```bash
start_dashboard.bat
```
oder im Terminal:
```bash
python run_platform.py
```
Öffnet automatisch das Studio im Browser unter **`http://localhost:4488`**.

---

## 🛠️ Tech Stack & Architektur

- **Backend:** [FastAPI](https://fastapi.tiangolo.com/) (Python 3.12) + [Uvicorn](https://www.uvicorn.org/)
- **Datenbank:** SQLite (`flyt.db`) mit automatischer Hintergrund-Synchronisation existierender Beats
- **Frontend:** [React 19](https://react.dev/) + [TypeScript](https://www.typescriptlang.org/) + [Tailwind CSS v4](https://tailwindcss.com/) + [Vite](https://vitejs.dev/) + [Lucide Icons](https://lucide.dev/)
- **Video & Audio Processing:** [FFmpeg](https://ffmpeg.org/) (2560x1440p Widescreen & 1080x1920 9:16 Vertical mit animierter Typografie)
- **Audio DSP Engine:** Automatische BPM-Erkennung (Autokorrelation), Krumhansl-Schmuckler Tonart-Erkennung, Sub/Mid/High Frequenzanalyse & Bar-Accurate Timestamps
- **KI & Generatoren:** Google Gemini 2.5/3.5 Flash, Black Forest Labs FLUX.1-schnell & Hugging Face Router

---

## ✨ Features

### 1. Producer Beat-Pipeline
- **MP3 Drag & Drop:** Einfach MP3 aus FL Studio / DAW reinziehen.
- **DSP Audio-Analyse:** Automatische Erkennung von Tempo (BPM), Tonart (Key, z. B. `C Minor`), Vibe und Songstruktur (Intro, Hook, Verse, Outro).
- **Interaktiver Audio-Player:** Direktes Anhören mit Spul-/Scrub-Funktion.

### 2. Lithen Night-Cam Artwork Generator
- Authentischer Candid iPhone 15 Pro Direct-Flash Look bei Nacht.
- Rotierende Szenen: Maskierte Personen (Balaclava/Seidentuch), moderne Supercars/JDM (GT3 RS, GT-R R34, RX-7) und schwere VVS Cuban Chains.
- Analoges Grain-Grading mit 1:1 Cover auf 16:9 Schwarzbalken.

### 3. Video Render Studio
- **1440p Hauptvideo (16:9):** Kristallklares 2560x1440 Master mit 320 kbps Audio für YouTube VP9/AV1 Codec-Bevorzugung.
- **9:16 Short & Instagram Reel (1080x1920):** Vertikaler Schnitt mit animierter Typografie (`<TONART> · <BPM> BPM` und `listen full version now`).
- **Schnittpunkte wählbar:** Startzeitpunkt (0:00, 0:12 Drop, 0:15, 0:30) und Dauer (30s, 45s, 58s) direkt in der Vorschau recutten.
- **Range-Streaming:** Ruckelfreies Vor- und Zurückspulen der MP4-Videos direkt im Browser.

### 4. YouTube Thumbnail Studio
- **Feed-optimiert:** 4:5 Hochformat mittig auf 16:9-Schwarzbalken (1280x720) ohne Text für maximale Klickrate.
- **Artist-Vibe Szenen:** Erkennt Künstler aus dem Beat (z. B. Future, Drake, Travis Scott, Don Toliver, Metro Boomin, Juice WRLD, Carti, Ken Carson, Yeat, etc.).
- **Live Feed-Vorschau:** Zeigt generierte Thumbnails sofort mit Titel, Beat-Länge und Kanal-Branding an.
- **1-Klick-Auswahl:** Speichert als `thumbnail.jpg` und synchronisiert automatisch mit der Cloud.

### 5. SEO & Release Suite
- **KI-Titelvorschläge:** 3 einzigartige Type-Beat-Titel mit kreativen Song-Beinamen.
- **1-Klick Copy:**
  - Komplette YouTube-Beschreibung inkl. BeatStars-Lease-Template & Timestamps.
  - Instagram Reel / YouTube Shorts Caption mit Hashtags.
  - Komma-getrennte YouTube Studio SEO-Tags.
- Direkte Verlinkung zum YouTube Studio Upload und Instagram.

### 6. Cloud Backup & Archivierung
- **Google Drive Sync:** Sichert Beats, Artworks, Thumbnails und finale Videos automatisch im Google Drive Ordner.
- **Archiv:** Fertige Beats können mit `✓` abgeschlossen und ausgeblendet werden.

---

## 📁 Projektstruktur

```
flyt/
├── backend/
│   ├── config.py             # Pfade & Config-Verwaltung
│   ├── database.py           # SQLite Schema & Sync
│   ├── main.py               # FastAPI App, Range-Streaming & SPA Static-Mount
│   ├── routers/              # REST Endpunkte (projects, render, thumbnails, metadata)
│   └── services/             # Audio DSP, Artwork, Render-Engine & Thumbnail-Service
├── frontend/
│   ├── src/
│   │   ├── components/       # UI Komponenten (ProjectCard, Modals, Filters, Scrubber)
│   │   ├── api.ts            # Getypte Backend-API Calls
│   │   ├── types.ts          # TypeScript Typen
│   │   └── App.tsx           # Haupt-View
│   └── dist/                 # Gebündeltes Produktions-Bundle
├── projects/                 # Lokaler Beat-Speicher (durch .gitignore geschützt)
├── artwork_pool/             # VVS Artwork Pool
├── run_platform.py           # Uvicorn Starter
└── start_dashboard.bat       # 1-Klick Starter für Windows
```

---

## 🔒 Datenschutz & Sicherheit

Alle Beats (`.mp3`), Videos (`.mp4`), Projekt-Dateien und sensible API-Keys (`config.json`) sind standardmäßig in `.gitignore` eingetragen und werden niemals versehentlich in GitHub hochgeladen.
