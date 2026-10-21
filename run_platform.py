import os
import sys
import uvicorn

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

def main():
    print("=" * 60)
    print("        FLYT STUDIO PLATFORM 2.0 (FastAPI + React)")
    print("        Local URL: http://localhost:4488")
    print("=" * 60)
    uvicorn.run("backend.main:app", host="127.0.0.1", port=4488, log_level="info")

if __name__ == "__main__":
    main()
