import os
import mimetypes
from supabase_client import supabase, supabase_url

async def upload_file_to_storage(file_content: bytes, filename: str, folder: str, base_url: str = None) -> str:
    """
    Uploads a file to Supabase Storage if configured, otherwise falls back to local uploads folder.
    Returns the public URL (or relative local path/dynamic local URL if local fallback).
    """
    bucket_name = "portfolio-assets"
    
    # 1. Try Supabase Storage first
    if supabase is not None:
        try:
            # Determine mime type
            mime_type, _ = mimetypes.guess_type(filename)
            if not mime_type:
                mime_type = "image/jpeg"  # default fallback for images
                
            file_path = f"{folder}/{filename}"
            
            # Upload to Supabase bucket
            # Using content-type in file_options and upsert
            supabase.storage.from_(bucket_name).upload(
                path=file_path,
                file=file_content,
                file_options={"upsert": "true", "content-type": mime_type}
            )
            
            # Construct public URL
            try:
                url_obj = supabase.storage.from_(bucket_name).get_public_url(file_path)
                if isinstance(url_obj, str):
                    public_url = url_obj
                elif hasattr(url_obj, "public_url"):
                    public_url = url_obj.public_url
                elif isinstance(url_obj, dict) and "public_url" in url_obj:
                    public_url = url_obj["public_url"]
                else:
                    public_url = str(url_obj)
            except Exception:
                # Manual fallback URL construction
                url_base = supabase_url or "https://placeholder.supabase.co"
                public_url = f"{url_base.rstrip('/')}/storage/v1/object/public/{bucket_name}/{file_path}"
                
            print(f"[Storage] Successfully uploaded to Supabase: {public_url}")
            return public_url
        except Exception as e:
            print(f"[Storage] Supabase upload failed: {e}. Falling back to local filesystem...")
            
    # 2. Local Fallback
    # Save physically on the local server filesystem
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    upload_dir = os.path.join(base_dir, "uploads")
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
        
    local_path = os.path.join(upload_dir, filename)
    with open(local_path, "wb") as buffer:
        buffer.write(file_content)
        
    # Return local URL dynamically if base_url is provided, else legacy static relative path
    if base_url:
        return f"{base_url.rstrip('/')}/uploads/{filename}"
    return f"uploads/{filename}"
