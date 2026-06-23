import httpx
import os
import asyncio
from datetime import datetime, timezone, timedelta
import dateutil.parser
from dotenv import load_dotenv
from services.github import _github_refresh_lock

async def refresh_github_contributions_cache(username: str):
    """
    Background task to refresh GitHub contributions cache.
    Uses the shared _github_refresh_lock to prevent stampede.
    If the refresh fails, we keep the stale cache and set cache status = 'error'.
    """
    from services.github import set_local_cache_with_meta, set_local_cache_meta
    
    if _github_refresh_lock.locked():
        return
    async with _github_refresh_lock:
        try:
            print(f"[github_graphql] Starting background contributions refresh for {username}...")
            set_local_cache_meta("github_contributions", "refreshing")
            
            res = await fetch_github_contributions_raw(username)
            import services.github as github_module
            if res and isinstance(res, dict) and "error" in res:
                err_msg = res["error"]
                print(f"[github_graphql] GraphQL contributions fetch returned error: {err_msg}. Serving stale cache.")
                github_module._github_sync_error = True
                set_local_cache_meta("github_contributions", "error", error_msg=err_msg)
            elif res:
                expires_at = (datetime.now(timezone.utc) + timedelta(hours=6)).isoformat()
                set_local_cache_with_meta("github_contributions", res, expires_at, "fresh")
                github_module._github_sync_error = False
                print(f"[github_graphql] Background contributions refresh for {username} succeeded.")
            else:
                github_module._github_sync_error = True
                set_local_cache_meta("github_contributions", "error", error_msg="Fetch returned empty (GraphQL error)")
        except Exception as e:
            err_msg = str(e)
            print(f"[github_graphql] Error during background contributions refresh for {username}: {err_msg}. Serving stale cache.")
            import services.github as github_module
            github_module._github_sync_error = True
            set_local_cache_meta("github_contributions", "error", error_msg=err_msg)

async def fetch_github_contributions(username: str) -> dict:
    """
    SQLite-first contributions fetcher.
    Returns cached dict instantly and spawns a background update if expired.
    If there is no cache at all, it fetches synchronously.
    """
    from database import get_local_cache
    from services.github import set_local_cache_with_meta, set_local_cache_meta
    
    # 1. Try reading from SQLite cache first
    cache_data = get_local_cache("github_contributions")
    if cache_data:
        payload = cache_data["payload"]
        expires_at_str = cache_data["expires_at"]
        
        # Check if cache has expired
        try:
            exp_dt = dateutil.parser.isoparse(expires_at_str)
            if exp_dt.tzinfo is None:
                exp_dt = exp_dt.replace(tzinfo=timezone.utc)
            is_expired = datetime.now(timezone.utc) > exp_dt
        except Exception as e:
            print(f"[github_graphql] Error parsing expires_at for contributions: {e}")
            is_expired = True
            
        if is_expired:
            if not _github_refresh_lock.locked():
                print(f"[github_graphql] Cache expired for contributions. Spawning background refresh task for {username}...")
                set_local_cache_meta("github_contributions", "stale")
                asyncio.create_task(refresh_github_contributions_cache(username))
            else:
                print(f"[github_graphql] Cache expired for contributions but refresh is already in progress. Serving stale cache.")
                
        return payload

    # 2. Cache miss — fetch synchronously on first load
    print(f"[github_graphql] Cache miss for contributions. Fetching synchronously for {username}...")
    async with _github_refresh_lock:
        # Double check cache inside lock
        cache_data = get_local_cache("github_contributions")
        if cache_data:
            return cache_data["payload"]
            
        set_local_cache_meta("github_contributions", "refreshing")
        res = await fetch_github_contributions_raw(username)
        import services.github as github_module
        if res and isinstance(res, dict) and "error" in res:
            github_module._github_sync_error = True
            set_local_cache_meta("github_contributions", "error", error_msg=res["error"])
            return res
        elif res:
            expires_at = (datetime.now(timezone.utc) + timedelta(hours=6)).isoformat()
            set_local_cache_with_meta("github_contributions", res, expires_at, "fresh")
            github_module._github_sync_error = False
            return res
        else:
            github_module._github_sync_error = True
            set_local_cache_meta("github_contributions", "error", error_msg="Synchronous fetch failed (returned None)")
            return {"error": "Failed to fetch contributions"}

async def fetch_github_contributions_raw(username: str):
    load_dotenv(override=True)
    github_token = os.getenv("GITHUB_TOKEN")
    
    if not github_token or github_token == "your_github_token_here_optional":
        return {"error": "GITHUB_TOKEN not configured properly"}

    query = """
    query($login: String!) {
      user(login: $login) {
        contributionsCollection {
          contributionCalendar {
            totalContributions
            weeks {
              contributionDays {
                date
                contributionCount
                color
              }
            }
          }
        }
      }
    }
    """
    
    headers = {"Authorization": f"bearer {github_token}"}
    data = None  # initialise before try so except block can always reference it
    async with httpx.AsyncClient(timeout=12.0) as client:
        try:
            response = await client.post(
                "https://api.github.com/graphql",
                json={"query": query, "variables": {"login": username}},
                headers=headers
            )
            data = response.json()
            
            if "message" in data and data["message"] == "Bad credentials":
                return {"error": "Invalid GitHub Token - Bad Credentials"}
            
            if "errors" in data:
                return {"error": data["errors"][0]["message"]}
                
            return data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
        except httpx.TimeoutException:
            return {"error": "GitHub GraphQL request timed out — check network connectivity"}
        except Exception as e:
            raw = str(data) if data is not None else "no response received"
            return {"error": f"Exception: {str(e)} - Raw Response: {raw}"}

