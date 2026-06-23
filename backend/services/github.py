import httpx
import os
import re
import base64
import time
import asyncio
from services.cache_service import get_cached_project_bullets, set_cached_project_bullets

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

_github_refresh_lock = asyncio.Lock()
_github_sync_error = False


# ─────────────────────────────────────────────
# README IMAGE PARSING HELPERS
# ─────────────────────────────────────────────

# Patterns to find images in README markdown, in priority order
_IMAGE_PATTERNS = [
    # 1. HTML img tag  <img src="...">
    re.compile(r'<img[^>]+src=["\']([^"\']+)["\']', re.IGNORECASE),
    # 2. Markdown image  ![alt](url)
    re.compile(r'!\[[^\]]*\]\(([^)]+)\)'),
    # 3. Markdown image with title  ![alt](url "title")
    re.compile(r'!\[[^\]]*\]\(([^\s)]+)\s+"[^"]*"\)'),
]

# File extensions we accept as images
_IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg'}

# Paths we skip — badges, logos, icons that aren't project screenshots
_SKIP_PATTERNS = re.compile(
    r'(badge|shield|travis|coveralls|codecov|npm|pypi|license|'
    r'logo|icon|avatar|banner|hits|visitor|made.with|built.with|'
    r'vercel\.app|buymeacoffee\.com|ko-fi\.com|paypalobjects\.com|'
    r'discordapp\.com/api/guilds|herokuapp\.com)',
    re.IGNORECASE
)


def _is_valid_image_url(url: str) -> bool:
    """Returns True if URL looks like a real project screenshot, not a badge."""
    if not url:
        return False
    # Must have an image extension or be a known image host
    has_ext = any(url.lower().endswith(ext) for ext in _IMAGE_EXTENSIONS)
    is_image_host = any(host in url for host in [
        'raw.githubusercontent.com',
        'user-images.githubusercontent.com',
        'imgur.com',
        'i.imgur.com',
    ])
    if not (has_ext or is_image_host):
        return False
    # Skip badges and icons
    if _SKIP_PATTERNS.search(url):
        return False
    return True


def _resolve_image_url(raw_url: str, username: str, repo: str, default_branch: str = "main") -> str:
    """
    Converts any README image reference to a fully qualified raw URL.

    Handles:
    - Already absolute URLs  → return as-is
    - Relative paths like  screenshots/demo.png
      → https://raw.githubusercontent.com/{username}/{repo}/{branch}/{path}
    - Paths starting with ./  → strip ./ and resolve
    """
    url = raw_url.strip()

    # Already absolute
    if url.startswith('http://') or url.startswith('https://'):
        # Convert github.com blob URLs to raw URLs
        if 'github.com' in url and '/blob/' in url:
            url = url.replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
        return url

    # Relative path — resolve to raw.githubusercontent.com
    path = url.lstrip('.').lstrip('/')
    return f"https://raw.githubusercontent.com/{username}/{repo}/{default_branch}/{path}"


def _extract_first_image(readme_content: str, username: str, repo: str, branch: str) -> str | None:
    """
    Extracts the first valid project screenshot from README markdown content.
    Returns a fully resolved raw URL, or None if no suitable image found.
    """
    for pattern in _IMAGE_PATTERNS:
        matches = pattern.findall(readme_content)
        for raw_url in matches:
            # Skip data URIs
            if raw_url.startswith('data:'):
                continue
            resolved = _resolve_image_url(raw_url, username, repo, branch)
            if _is_valid_image_url(resolved):
                return resolved
    return None


# ─────────────────────────────────────────────
# README FETCHER
# ─────────────────────────────────────────────

async def fetch_readme_image(
    client: httpx.AsyncClient,
    headers: dict,
    username: str,
    repo: str,
    default_branch: str = "main"
) -> str | None:
    """
    Fetches the README for a repo and extracts the first project screenshot.

    Tries default_branch first, then falls back to 'master' if not found.
    Returns image URL string or None — never raises.
    """
    for branch in [default_branch, "master", "main"]:
        try:
            url = f"https://api.github.com/repos/{username}/{repo}/readme"
            response = await client.get(url, headers=headers, timeout=8.0)

            if response.status_code == 401 and "Authorization" in headers:
                # Retry without token
                headers_no_auth = {k: v for k, v in headers.items() if k != "Authorization"}
                response = await client.get(url, headers=headers_no_auth, timeout=8.0)

            if response.status_code == 404:
                continue
            response.raise_for_status()

            data = response.json()
            # README content is base64 encoded by GitHub API
            content_b64 = data.get("content", "")
            if not content_b64:
                return None

            readme_text = base64.b64decode(content_b64).decode("utf-8", errors="replace")
            image_url = _extract_first_image(readme_text, username, repo, branch)
            if image_url:
                return image_url

        except Exception as e:
            print(f"[fetch_readme_image] {repo} ({branch}): {e}")
            continue

    return None


# ─────────────────────────────────────────────
# IN-MEMORY README IMAGE CACHE
# ─────────────────────────────────────────────

_readme_image_cache: dict = {}       # repo_name → image_url or None
_readme_image_cache_ts: dict = {}    # repo_name → timestamp
_README_CACHE_TTL = 3600             # 1 hour — READMEs don't change often


def _get_cached_readme_image(repo: str) -> tuple[bool, str | None]:
    """Returns (found, value). found=True means cache hit (even if value is None)."""
    if repo not in _readme_image_cache:
        return False, None
    if time.time() - _readme_image_cache_ts.get(repo, 0) > _README_CACHE_TTL:
        del _readme_image_cache[repo]
        del _readme_image_cache_ts[repo]
        return False, None
    return True, _readme_image_cache[repo]


def _set_cached_readme_image(repo: str, url: str | None) -> None:
    _readme_image_cache[repo] = url
    _readme_image_cache_ts[repo] = time.time()


def clear_readme_image_cache() -> None:
    """Call this when GitHub webhook fires to force fresh README fetches."""
    _readme_image_cache.clear()
    _readme_image_cache_ts.clear()

def clear_readme_cache_for_repo(repo: str) -> None:
    """Selectively clears the README image cache for a specific repo."""
    _readme_image_cache.pop(repo, None)
    _readme_image_cache_ts.pop(repo, None)


# ─────────────────────────────────────────────
# IN-MEMORY REPOSITORIES CACHE
# ─────────────────────────────────────────────
_repos_cache: dict = {}
_repos_cache_ts: dict = {}
_REPOS_CACHE_TTL = 3600  # Cache for 1 hour

def clear_github_repos_cache() -> None:
    global _repos_cache, _repos_cache_ts
    _repos_cache = {}
    _repos_cache_ts = {}

from datetime import datetime, timezone, timedelta
import dateutil.parser
import sqlite3
import json
from database import DB_FILE, LOCK_FILE
from filelock import FileLock

def set_github_projects_db(projects: list):
    """Saves the given list of projects as structured rows in github_projects table."""
    with FileLock(LOCK_FILE, timeout=10):
        with sqlite3.connect(DB_FILE) as conn:
            conn.execute("DELETE FROM github_projects")
            for p in projects:
                conn.execute(
                    """INSERT OR REPLACE INTO github_projects 
                       (id, name, description, techStack, stars, url, html_url, homepage, language, topics, updated_at, default_branch, image, has_image, is_github)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        p.get("id"),
                        p.get("name"),
                        p.get("description"),
                        p.get("techStack"),
                        p.get("stars", 0),
                        p.get("url"),
                        p.get("html_url"),
                        p.get("homepage"),
                        p.get("language"),
                        json.dumps(p.get("topics", [])),
                        p.get("updated_at"),
                        p.get("default_branch"),
                        p.get("image"),
                        1 if p.get("has_image") else 0,
                        1 if p.get("is_github") else 0
                    )
                )
            conn.commit()

def get_github_projects_db() -> list:
    """Retrieves all cached github projects from github_projects table."""
    with FileLock(LOCK_FILE, timeout=10):
        with sqlite3.connect(DB_FILE) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM github_projects")
            rows = cursor.fetchall()
            projects = []
            for r in rows:
                p = dict(r)
                try:
                    p["topics"] = json.loads(p["topics"]) if p["topics"] else []
                except Exception:
                    p["topics"] = []
                p["has_image"] = bool(p["has_image"])
                p["is_github"] = bool(p["is_github"])
                projects.append(p)
            return projects

def set_local_cache_meta(key: str, status: str, error_msg: str | None = None, expires_at: str | None = None):
    """Updates the cache health metadata row in local_cache without changing payload."""
    with FileLock(LOCK_FILE, timeout=10):
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT payload, last_success_at, expires_at FROM local_cache WHERE cache_key = ?", (key,))
            row = cursor.fetchone()
            
            payload = json.dumps("OK")
            last_success_at = None
            current_expires_at = expires_at or ""
            
            if row:
                payload_val, last_success_at_val, expires_at_val = row
                payload = payload_val
                last_success_at = last_success_at_val
                if not expires_at:
                    current_expires_at = expires_at_val
            
            now_str = datetime.now(timezone.utc).isoformat()
            if status in ["fresh", "stale"] and not last_success_at:
                last_success_at = now_str
            elif status in ["fresh"]:
                last_success_at = now_str
                
            conn.execute(
                """INSERT OR REPLACE INTO local_cache 
                   (cache_key, payload, updated_at, expires_at, last_success_at, last_error, status) 
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    key,
                    payload,
                    now_str,
                    current_expires_at,
                    last_success_at,
                    error_msg,
                    status
                )
            )
            conn.commit()

def set_local_cache_with_meta(key: str, payload: dict, expires_at: str, status: str, error_msg: str | None = None):
    """Inserts or replaces a generic JSON cache payload with detailed health metadata."""
    with FileLock(LOCK_FILE, timeout=10):
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT last_success_at FROM local_cache WHERE cache_key = ?", (key,))
            row = cursor.fetchone()
            
            last_success_at = None
            if row:
                last_success_at = row[0]
            
            now_str = datetime.now(timezone.utc).isoformat()
            if status in ["fresh", "stale"] and not last_success_at:
                last_success_at = now_str
            elif status in ["fresh"]:
                last_success_at = now_str
                
            conn.execute(
                """INSERT OR REPLACE INTO local_cache 
                   (cache_key, payload, updated_at, expires_at, last_success_at, last_error, status) 
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    key,
                    json.dumps(payload, ensure_ascii=False),
                    now_str,
                    expires_at,
                    last_success_at,
                    error_msg,
                    status
                )
            )
            conn.commit()

async def refresh_github_projects_cache(username: str):
    """
    Background task to refresh GitHub projects cache.
    Uses the global _github_refresh_lock to prevent stampede.
    If the refresh fails, we keep the stale cache and set cache status = 'error'.
    """
    global _github_sync_error
    if _github_refresh_lock.locked():
        return
    async with _github_refresh_lock:
        try:
            print(f"[github] Starting background projects refresh for {username}...")
            set_local_cache_meta("github_projects_meta", "refreshing")
            
            projects = await fetch_github_projects_raw(username)
            if projects is not None:
                set_github_projects_db(projects)
                expires_at = (datetime.now(timezone.utc) + timedelta(hours=6)).isoformat()
                set_local_cache_meta("github_projects_meta", "fresh", expires_at=expires_at)
                _github_sync_error = False
                print(f"[github] Background projects refresh for {username} succeeded.")
            else:
                print(f"[github] Background projects refresh for {username} failed (returned None). Serving stale cache.")
                _github_sync_error = True
                set_local_cache_meta("github_projects_meta", "error", error_msg="Fetch returned None (GitHub API error)")
        except Exception as e:
            err_msg = str(e)
            print(f"[github] Error during background projects refresh for {username}: {err_msg}. Serving stale cache.")
            _github_sync_error = True
            set_local_cache_meta("github_projects_meta", "error", error_msg=err_msg)

async def fetch_github_projects(username: str) -> list:
    """
    SQLite-first projects fetcher.
    Returns cached list instantly from structured projects table
    and spawns a background update if expired.
    If there is no cache at all, it fetches synchronously.
    """
    from database import get_local_cache
    
    # 1. Try reading from SQLite cache metadata first
    meta_data = get_local_cache("github_projects_meta")
    if meta_data:
        projects = get_github_projects_db()
        expires_at_str = meta_data["expires_at"]
        
        # Check if cache has expired
        try:
            exp_dt = dateutil.parser.isoparse(expires_at_str)
            if exp_dt.tzinfo is None:
                exp_dt = exp_dt.replace(tzinfo=timezone.utc)
            is_expired = datetime.now(timezone.utc) > exp_dt
        except Exception as e:
            print(f"[github] Error parsing expires_at for projects: {e}")
            is_expired = True
            
        if is_expired:
            if not _github_refresh_lock.locked():
                print(f"[github] Cache expired for projects. Spawning background refresh task for {username}...")
                set_local_cache_meta("github_projects_meta", "stale")
                asyncio.create_task(refresh_github_projects_cache(username))
            else:
                print(f"[github] Cache expired for projects but refresh is already in progress. Serving stale cache.")
                
        return projects

    # 2. Cache miss — fetch synchronously on first load
    print(f"[github] Cache miss for projects. Fetching synchronously for {username}...")
    async with _github_refresh_lock:
        # Double check cache inside lock
        meta_data = get_local_cache("github_projects_meta")
        if meta_data:
            return get_github_projects_db()
            
        set_local_cache_meta("github_projects_meta", "refreshing")
        projects = await fetch_github_projects_raw(username)
        global _github_sync_error
        if projects is not None:
            set_github_projects_db(projects)
            expires_at = (datetime.now(timezone.utc) + timedelta(hours=6)).isoformat()
            set_local_cache_meta("github_projects_meta", "fresh", expires_at=expires_at)
            _github_sync_error = False
            return projects
        else:
            _github_sync_error = True
            set_local_cache_meta("github_projects_meta", "error", error_msg="Synchronous fetch failed (returned None)")
            return []

async def fetch_github_projects_raw(username: str) -> list | None:
    """
    Retrieves repositories directly from the GitHub API.
    Returns list on success, or None on failure.
    """
    token = os.getenv("GITHUB_TOKEN") or GITHUB_TOKEN
    headers = {"Accept": "application/vnd.github.v3+json"}

    if token:
        headers["Authorization"] = f"token {token}"

    url = f"https://api.github.com/users/{username}/repos?sort=updated&per_page=15"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=10.0)
            response.raise_for_status()
            repos = response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401 and "Authorization" in headers:
                print("[fetch_github_projects_raw] Got 401 Unauthorized with token, retrying without token...")
                headers_no_auth = {k: v for k, v in headers.items() if k != "Authorization"}
                try:
                    response = await client.get(url, headers=headers_no_auth, timeout=10.0)
                    response.raise_for_status()
                    repos = response.json()
                except Exception as retry_e:
                    print(f"[fetch_github_projects_raw] Error fetching repo list on retry: {retry_e}")
                    return None
            else:
                print(f"[fetch_github_projects_raw] HTTP error fetching repo list: {e}")
                return None
        except Exception as e:
            print(f"[fetch_github_projects_raw] Error fetching repo list: {e}")
            return None

        # Filter forks
        repos = [r for r in repos if not r.get("fork")]

        async def enrich_repo(r: dict) -> dict:
            repo_name = r.get("name", "")
            default_branch = r.get("default_branch", "main")

            # Check cache first
            cached_hit, cached_image = _get_cached_readme_image(repo_name)
            if cached_hit:
                image_url = cached_image
            else:
                # Fetch README image — runs concurrently with other repos
                image_url = await fetch_readme_image(
                    client, headers, username, repo_name, default_branch
                )
                _set_cached_readme_image(repo_name, image_url)

            return {
                "id": f"gh_{r.get('id')}",
                "name": repo_name,
                "summary": r.get("description") or "Open source project on GitHub.",
                "description": r.get("description") or "",
                "techStack": r.get("language") or "Code",
                "stars": r.get("stargazers_count", 0),
                "url": r.get("html_url"),
                "html_url": r.get("html_url"),
                "homepage": r.get("homepage"),
                "language": r.get("language"),
                "topics": r.get("topics", []),
                "updated_at": r.get("updated_at"),
                "default_branch": default_branch,
                # NEW — README image for portfolio cards and resume
                "image": image_url,          # None if no image found
                "has_image": image_url is not None,
                "is_github": True,
            }

        # Run all README fetches concurrently (httpx client is shared — efficient)
        try:
            enriched = await asyncio.gather(
                *[enrich_repo(r) for r in repos],
                return_exceptions=False
            )
            return list(enriched)
        except Exception as e:
            print(f"[fetch_github_projects_raw] Enrichment failed: {e}")
            return None

