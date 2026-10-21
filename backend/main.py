import os
import mimetypes
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse, FileResponse
from backend.config import BASE_DIR, PROJECTS_DIR
from backend.database import init_db
from backend.routers import projects, render, artwork, metadata, thumbnails, config, system

app = FastAPI(title="FLYT Studio Platform", version="2.0.0")

# Enable CORS for Vite dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    init_db()

# Register API Routers
app.include_router(projects.router)
app.include_router(render.router)
app.include_router(artwork.router)
app.include_router(metadata.router)
app.include_router(thumbnails.router)
app.include_router(config.router)
app.include_router(system.router)

# Custom HTTP Range streaming for media files in /projects/{project_name}/{filename}
def range_file_streamer(file_path: str, range_header: str):
    file_size = os.path.getsize(file_path)
    start_byte = 0
    end_byte = file_size - 1

    if range_header and range_header.startswith("bytes="):
        try:
            parts = range_header[6:].split(",")[0].split("-")
            if parts[0].strip():
                start_byte = int(parts[0].strip())
            if len(parts) > 1 and parts[1].strip():
                end_byte = min(file_size - 1, int(parts[1].strip()))
        except Exception:
            start_byte = 0
            end_byte = file_size - 1

    content_len = max(0, end_byte - start_byte + 1)
    
    def file_iterator():
        with open(file_path, "rb") as f:
            f.seek(start_byte)
            remaining = content_len
            while remaining > 0:
                chunk = f.read(min(65536, remaining))
                if not chunk:
                    break
                yield chunk
                remaining -= len(chunk)

    ctype, _ = mimetypes.guess_type(file_path)
    if not ctype:
        if file_path.endswith((".jpg", ".jpeg")):
            ctype = "image/jpeg"
        elif file_path.endswith(".png"):
            ctype = "image/png"
        elif file_path.endswith(".mp4"):
            ctype = "video/mp4"
        elif file_path.endswith(".mp3"):
            ctype = "audio/mpeg"
        else:
            ctype = "application/octet-stream"

    status_code = 206 if range_header else 200
    headers = {
        "Content-Type": ctype,
        "Accept-Ranges": "bytes",
        "Content-Length": str(content_len),
        "Cache-Control": "no-cache",
        "Access-Control-Allow-Origin": "*",
    }
    if status_code == 206:
        headers["Content-Range"] = f"bytes {start_byte}-{end_byte}/{file_size}"

    return StreamingResponse(file_iterator(), status_code=status_code, headers=headers)

@app.get("/projects/{full_path:path}")
def serve_project_file(full_path: str, request: Request):
    clean_path = os.path.normpath(full_path).lstrip("\\/.")
    file_path = os.path.join(PROJECTS_DIR, clean_path)
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    range_header = request.headers.get("range")
    return range_file_streamer(file_path, range_header)

@app.get("/media/{full_path:path}")
def serve_media_file(full_path: str, request: Request):
    return serve_project_file(full_path, request)

# Serve Frontend SPA
FRONTEND_DIST = os.path.join(BASE_DIR, "frontend", "dist")

if os.path.isdir(FRONTEND_DIST):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIST, "assets")), name="assets")

    @app.get("/{full_path:path}")
    def serve_spa(full_path: str):
        target = os.path.join(FRONTEND_DIST, full_path)
        if os.path.isfile(target):
            return FileResponse(target)
        index_file = os.path.join(FRONTEND_DIST, "index.html")
        if os.path.isfile(index_file):
            return FileResponse(index_file)
        return {"error": "Frontend not built yet. Run 'npm run build' inside frontend/"}
else:
    # Fallback to legacy index.html if frontend hasn't been built yet
    @app.get("/")
    def serve_legacy_root():
        legacy_html = os.path.join(BASE_DIR, "index.html")
        if os.path.isfile(legacy_html):
            return FileResponse(legacy_html)
        return {"app": "FLYT Studio Platform API"}
