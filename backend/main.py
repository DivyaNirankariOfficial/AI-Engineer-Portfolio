import json
import os
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import List, Optional
import httpx
from datetime import datetime
import hashlib
from dotenv import load_dotenv
load_dotenv()  # MUST be before any service imports that call os.getenv at module level
import asyncio
import sys

# Fix for Playwright NotImplementedError in Windows Async loops
if sys.version_info[0] == 3 and sys.version_info[1] >= 8 and sys.platform.startswith('win'):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from routes.portfolio import router as portfolio_router
from routes.projects import router as projects_router
from routes.admin import router as admin_router
from routes.dynamic_sections import router as dynamic_sections_router
from routes.platform import router as platform_router
from routes.resume import router as resume_router
from fastapi.staticfiles import StaticFiles
from database import load_data, save_data

app = FastAPI(title="Divya Nirankari Portfolio API")

# Gzip compress all responses > 1KB — reduces JSON payload ~70%
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Mount static files
if not os.path.exists("uploads"):
    os.makedirs("uploads")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from database import load_data

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")

def run_github_cache_cron():
    """Runs a background loop that refreshes GitHub cache every 6 hours."""
    import time
    import asyncio
    from database import load_data
    
    # Wait 30 seconds after startup to avoid interfering with initial boot warmup
    time.sleep(30)
    
    while True:
        try:
            print("[cron] Starting scheduled 6-hour GitHub cache refresh...")
            data = load_data()
            github_handle = data.get("profile", {}).get("github", "")
            username = github_handle.split("/")[-1] if github_handle else "DivyaNirankariOfficial"
            
            # Start a new asyncio event loop for this thread to call our async functions
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            from services.github import refresh_github_projects_cache
            from services.github_graphql import refresh_github_contributions_cache
            
            loop.run_until_complete(refresh_github_projects_cache(username))
            loop.run_until_complete(refresh_github_contributions_cache(username))
            
            loop.close()
            print("[cron] Scheduled GitHub cache refresh completed successfully.")
        except Exception as e:
            print(f"[cron] Error in scheduled GitHub cache refresh: {e}")
            
        time.sleep(6 * 3600)

@app.on_event("startup")
def startup_event():
    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR)

    import threading

    def warmup_and_pregen():
        """Warm up database cache and Playwright, then trigger cold-start PDF pre-generation."""
        try:
            print("[startup] Syncing SQLite cache from Supabase in background...")
            from database import load_data, _invalidate_cache
            _invalidate_cache()
            data = load_data()
            print("[startup] SQLite cache sync completed successfully.")
            
            # Warm up GitHub cache in background
            github_handle = data.get("profile", {}).get("github", "")
            username = github_handle.split("/")[-1] if github_handle else "DivyaNirankariOfficial"
            print(f"[startup] Warming up GitHub cache for {username}...")
            
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            from services.github import fetch_github_projects
            from services.github_graphql import fetch_github_contributions
            
            loop.run_until_complete(fetch_github_projects(username))
            loop.run_until_complete(fetch_github_contributions(username))
            loop.close()
            print("[startup] GitHub cache warmup completed.")
            
        except Exception as e:
            print(f"[startup] SQLite cache sync/warmup failed: {e}")

        from pathlib import Path
        import os
        print("========== PLAYWRIGHT DEBUG ==========")
        print(
            "PLAYWRIGHT CACHE EXISTS:",
            Path("/opt/render/.cache/ms-playwright").exists()
        )

        print(
            "PLAYWRIGHT_BROWSERS_PATH:",
            os.environ.get("PLAYWRIGHT_BROWSERS_PATH")
        )

        cache = Path("/opt/render/.cache/ms-playwright")
        if cache.exists():
            try:
                print("CACHE CONTENTS:", list(cache.iterdir()))
            except Exception as e:
                print("CACHE ERROR:", e)

        print("======================================")
        import asyncio

        # Step 1: Playwright warmup (prevents first request timeout)
        try:
            from services.pdf_playwright import _generate_pdf_sync
            _generate_pdf_sync("<html><body>warmup</body></html>", "A4", {"top": "0"})
            print("Playwright warmed up successfully.")
        except Exception as e:
            print(f"Playwright warmup failed: {e}")

        # Step 2: Cold-start pre-generation (only if no PDFs exist yet)
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            from services.pregenerator import regenerate_if_empty
            loop.run_until_complete(regenerate_if_empty())
            loop.close()
        except Exception as e:
            print(f"Cold-start pre-generation failed: {e}")

    threading.Thread(target=warmup_and_pregen, daemon=True).start()
    threading.Thread(target=run_github_cache_cron, daemon=True).start()

app.include_router(portfolio_router, prefix="/api/portfolio", tags=["portfolio"])
app.include_router(projects_router, prefix="/api/projects", tags=["projects"])
app.include_router(admin_router, prefix="/api/admin", tags=["admin"])
app.include_router(dynamic_sections_router, prefix="/api/dynamic", tags=["dynamic"])
app.include_router(platform_router, prefix="/api/platform", tags=["platform"])
app.include_router(resume_router, prefix="/api/resume", tags=["resume"])
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")
app.mount("/static/templates", StaticFiles(directory=os.path.join(BASE_DIR, "resume_templates")), name="templates")

# Dynamic resume download is handled in routes/resume.py via resume_router

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
