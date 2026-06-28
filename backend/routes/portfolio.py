from fastapi import APIRouter, HTTPException, UploadFile, File, Request
from pydantic import BaseModel
from typing import Dict, Any, Optional
import sys
import os
import shutil
from services.storage import upload_file_to_storage

# Adjust path to import main's load_data / save_data
# Alternatively, I can move data logic here, but let's keep it simple
router = APIRouter()

@router.get("/")
def get_portfolio():
    import time
    t0 = time.time()
    from database import load_data
    from fastapi.responses import JSONResponse
    data = load_data()
    print(f"[DEBUG] get_portfolio load_data took: {time.time() - t0:.4f}s")

    # Strip private/admin-only keys from public response
    PRIVATE_KEYS = {
        "activityLog", "analytics", "contactMessages",
        "resumeSettings", "cover_letter", "hiddenProjects", "projectSummaries",
    }
    public = {k: v for k, v in data.items() if k not in PRIVATE_KEYS}
    res = JSONResponse(content=public, headers={"Cache-Control": "public, max-age=30"})
    print(f"[DEBUG] get_portfolio total took: {time.time() - t0:.4f}s")
    return res

from fastapi import BackgroundTasks

@router.post("/")
def update_portfolio(data: Dict[str, Any], background_tasks: BackgroundTasks):
    from database import save_data, load_data
    
    current_data = load_data()
    
    # Deep update dict
    def deep_update(d, u):
        for k, v in u.items():
            if isinstance(v, dict) and k in d and isinstance(d[k], dict):
                d[k] = deep_update(d.get(k, {}), v)
            else:
                d[k] = v
        return d
        
    updated = deep_update(current_data, data)
    save_data(updated)
    
    from routes.dynamic_sections import log_activity
    sections_updated = list(data.keys())
    log_activity(f"Manually updated config/profile", "Settings", data)
    
    from services.groq_service import auto_regenerate_summary_task
    background_tasks.add_task(auto_regenerate_summary_task)
    
    return {"status": "success", "data": updated}

@router.post("/photo")
async def upload_photo(request: Request, file: UploadFile = File(...)):
    from database import save_data, load_data

    # Safe file name
    file_extension = file.filename.split(".")[-1].lower() if "." in file.filename else "jpg"
    if file_extension not in ["jpg", "jpeg", "png", "webp"]:
        raise HTTPException(status_code=400, detail="Only JPG, PNG, or WEBP are allowed.")

    filename = f"profile_photo.{file_extension}"
    file_content = await file.read()
    base_url = str(request.base_url).rstrip('/')
    
    photo_url = await upload_file_to_storage(file_content, filename, "profile", base_url=base_url)

    # Save to data.json instantly
    current_data = load_data()
    if "profile" in current_data:
        current_data["profile"]["photo"] = photo_url
        save_data(current_data)

    return {"status": "success", "photo_url": photo_url}
