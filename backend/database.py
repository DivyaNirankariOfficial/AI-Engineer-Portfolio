import json
import os
import shutil
import sqlite3
import time
from datetime import datetime
from filelock import FileLock

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "portfolio.db")
LOCK_FILE = os.path.join(BASE_DIR, "portfolio.db.lock")

# ── In-memory data cache ──────────────────────────────────────────────────────
# load_data() is called on EVERY request. Caching in RAM eliminates the SQLite
# round-trip + JSON parse overhead. Invalidated whenever save_data() is called.
_data_cache: dict | None = None
_data_cache_ts: float = 0.0
DATA_CACHE_TTL = 60  # seconds — safety net; admin saves always invalidate immediately

def _invalidate_cache():
    global _data_cache, _data_cache_ts
    _data_cache = None
    _data_cache_ts = 0.0

def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS portfolio_data (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                data TEXT NOT NULL,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )"""
        )
        conn.execute(
            """CREATE TABLE IF NOT EXISTS translations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                field_name TEXT NOT NULL,
                locale TEXT NOT NULL,
                original_text TEXT NOT NULL,
                translated_text TEXT NOT NULL,
                is_verified INTEGER DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(field_name, locale, original_text)
            )"""
        )
        conn.execute(
            """CREATE TABLE IF NOT EXISTS pdf_cache (
                id TEXT PRIMARY KEY,
                pdf_blob BLOB NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )"""
        )
        # Check if local_cache has the new metadata fields
        cursor = conn.cursor()
        try:
            cursor.execute("PRAGMA table_info(local_cache)")
            cols = [row[1] for row in cursor.fetchall()]
            if cols and "last_success_at" not in cols:
                print("[database] Migrating local_cache table: dropping old schema...")
                cursor.execute("DROP TABLE local_cache")
                conn.commit()
        except Exception as e:
            print(f"[database] Migration check error: {e}")

        conn.execute(
            """CREATE TABLE IF NOT EXISTS local_cache (
                cache_key TEXT PRIMARY KEY,
                payload TEXT NOT NULL,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                expires_at TEXT NOT NULL,
                last_success_at TEXT,
                last_error TEXT,
                status TEXT
            )"""
        )
        conn.execute(
            """CREATE TABLE IF NOT EXISTS github_projects (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                techStack TEXT,
                stars INTEGER DEFAULT 0,
                url TEXT,
                html_url TEXT,
                homepage TEXT,
                language TEXT,
                topics TEXT,
                updated_at TEXT,
                default_branch TEXT,
                image TEXT,
                has_image INTEGER DEFAULT 0,
                is_github INTEGER DEFAULT 1
            )"""
        )
        conn.commit()

init_db()

DEFAULT_DATA = {
    "profile": {
        "name": "Divya Nirankari",
        "role": "Software Engineer & AI/ML Engineer",
        "email": "dvnirankari@gmail.com",
        "phone": "+91 9265768306",
        "alternate_phone": "",
        "location": "Surat, Gujarat, India",
        "summary": "Python and AI/ML Engineer building production-ready machine learning systems, with a deep focus on Healthcare AI and biomedical signal processing. At Logixbuilt Infotech, I developed high-throughput REST APIs (10k+ daily requests, 99.9% uptime) and reduced database response times by 40% through PostgreSQL query optimisation. As a freelance engineer, I have designed ECG cardiac abnormality detection models achieving 94% F1-score using 1D CNN and ResNet architectures on the PhysioNet dataset, and built real-time AI-powered chatbots integrated across WhatsApp, Telegram, and Messenger. I am currently authoring a research paper on deep learning-based ECG analysis and am actively studying Japanese, with the goal of contributing to Japan's world-class AI research and healthcare technology ecosystem.",
        "bio": "Python and AI/ML Engineer specialising in Healthcare AI and biomedical signal processing. I build production-grade ML systems and scalable backends — from ECG cardiac detection models to real-time chatbot integrations.",
        "personal": {
            "dob": "1998-01-05",
            "gender": "female",
            "nationality": "India",
            "marital_status": "Single",
            "political_status": "",
            # Note: WeChat and KakaoTalk IDs are intentionally different platform-specific handles.
            "wechat_id": "",
            "military_service": "No",
            "japanese_era_dates": False,
            "name_furigana": "ディヴィア・ニランカリ",
            "nationality_ja": "インド",
            "address_furigana": "インド グジャラート州 スーラト",
            "commute_time": "",
            "dependents_count": 0,
            "has_spouse": False,
            "spouse_dependency": False,
            "self_pr_ja": "",
            "self_pr_ja_detailed": "",
            "career_summary_ja": "",
            "desired_conditions_ja": "貴社の規定に従います。"
        },
        "visa_info": {
            "visaType": "",
            "visaIssueDate": "",
            "visaExpiryDate": ""
        },
        "visa": {
            "JP": "Requires Engineer / Specialist in Humanities / International Services visa sponsorship",
            "KR": "Requires E-7 Specially Designated Activities visa sponsorship",
            "CN": "需要工作签证（Z签证），需由用人单位协助办理。",
            "CN_EN": "Requires Z-visa sponsorship for employment in China.",
            "US": "Requires H-1B visa sponsorship",
            "UK": "Requires Skilled Worker visa sponsorship",
            "DE": "Eligible for EU Blue Card; requires employer sponsorship",
            "AE": "Requires employer-sponsored employment visa",
            "IN": "Indian citizen — no visa required",
            "GLOBAL": "Relocation sponsorship required"
        },
        "github": "https://github.com/DivyaNirankariOfficial",
        "github_username": "DivyaNirankariOfficial"
    },
    "connections": [
        {"id": "conn_1", "platform": "GitHub", "url": "https://github.com/DivyaNirankariOfficial", "handle": "DivyaNirankariOfficial", "visible": True, "order": 0},
        {"id": "conn_2", "platform": "LinkedIn", "url": "https://www.linkedin.com/in/divya-nirankari/", "handle": "Divya Nirankari", "visible": True, "order": 1},
        {"id": "conn_3", "platform": "Email", "url": "mailto:dvnirankari@gmail.com", "handle": "dvnirankari@gmail.com", "visible": True, "order": 2},
        {"id": "conn_4", "platform": "YouTube", "url": "", "handle": "", "visible": False, "order": 3},
        {"id": "conn_5", "platform": "Instagram", "url": "", "handle": "", "visible": False, "order": 4},
        {"id": "conn_6", "platform": "KakaoTalk", "url": "", "handle": "", "visible": False, "order": 5}
    ],
    "about": [
        "I am a Python and AI/ML Engineer with a deep focus on Healthcare AI, building systems that bridge cutting-edge research with real-world impact.",
        "My core expertise is in biomedical signal processing — I have designed ECG cardiac abnormality detection models using 1D CNN and ResNet architectures, achieving 94% F1-score on the PhysioNet dataset.",
        "On the backend, I architect scalable FastAPI systems, Redis-cached data pipelines, and production ML inference APIs deployed for international clients. As my work evolves, I am increasingly interested in NeuroAI, brain-inspired intelligence, and the intersection of biological and artificial learning systems."
    ],
    "stats": {
        "card_1_value": "12+",
        "card_1_label": "Systems Built",
        "card_2_value": "94%",
        "card_2_label": "ECG F1-Score",
        "card_3_value": "Healthcare AI",
        "card_3_label": "Biomedical Signal Processing",
        "card_4_value": "AI + Backend",
        "card_4_label": "Research to Production"
    },
    "skills": ["Python", "JavaScript", "React", "FastAPI", "PyTorch", "TensorFlow", "SQL", "Docker", "AWS"],
    "skillCategories": [
        {
            "label": "AI & Machine Learning",
            "items": ["PyTorch", "TensorFlow", "Scikit-learn", "CNN", "1D ResNet", "LSTM", "Random Forest", "NLP", "Computer Vision", "Biomedical Signal Processing (ECG)", "Model Evaluation", "Hyperparameter Tuning"],
            "visible": True, "order": 1
        },
        {
            "label": "Backend & APIs",
            "items": ["Python", "FastAPI", "Django", "REST APIs", "GraphQL", "PostgreSQL", "Redis", "MongoDB", "SQL"],
            "visible": True, "order": 2
        },
        {
            "label": "Data & ML Ops",
            "items": ["Pandas", "NumPy", "SciPy", "Data Preprocessing", "Feature Engineering", "Git", "AWS", "K6 API Testing"],
            "visible": True, "order": 3
        }
    ],
    "sections_visibility": {
        "about": True,
        "skills": True,
        "projects": True,
        "contact": True,
        "experience": True,
        "achievements": False,
        "activity": False,
        "timeline": True,
        "research": False,
        "exploring": True,
        "testimonials": False,
        "blog": False
    },
    "project_visibility": {},
    "researchInterests": [],
    "currentlyExploring": [
        {
            "id": "explore_1",
            "theme": "NeuroAI",
            "description": "Exploring how insights from neuroscience can contribute to more capable AI systems.",
            "visible": True
        },
        {
            "id": "explore_2",
            "theme": "Healthcare AI",
            "description": "Interested in applying machine learning to real-world healthcare challenges.",
            "visible": True
        },
        {
            "id": "explore_3",
            "theme": "Brain-Inspired Learning",
            "description": "Studying how biological learning mechanisms can inform artificial intelligence.",
            "visible": True
        },
        {
            "id": "explore_4",
            "theme": "Human-Robot Interaction",
            "description": "Exploring intelligent systems that collaborate naturally with people.",
            "visible": True
        }
    ],
    "researchNarrative": {
        "enabled": False,
        "title": "Research Direction",
        "content": "Beyond my current work, I am increasingly interested in NeuroAI, brain-inspired intelligence, and intelligent systems. I am particularly drawn to understanding how insights from biological systems can inform the development of more capable, adaptive, and efficient AI."
    },
    "testimonials": [],
    "blogPosts": [],
    "languages": [
        {"id": "lang_1", "name": "English", "level": "Fluent / Professional", "percentage": 95, "visible": True, "order": 1},
        {"id": "lang_2", "name": "Hindi", "level": "Native", "percentage": 100, "visible": True, "order": 2},
        {"id": "lang_3", "name": "Gujarati", "level": "Native", "percentage": 100, "visible": True, "order": 3},
        {"id": "lang_4", "name": "Korean", "level": "Basic", "percentage": 10, "visible": True, "order": 4},
        {"id": "lang_5", "name": "Japanese", "level": "Beginner (Currently Learning)", "percentage": 8, "visible": True, "order": 5},
        {"id": "lang_6", "name": "Mandarin Chinese", "level": "Beginner (Currently Learning)", "percentage": 8, "visible": True, "order": 6}
    ],
    "experience": [
        {
            "id": "exp_1",
            "company": "Logixbuilt Infotech",
            "role": "Python Software Engineer",
            "startDate": "Mar 2022",
            "endDate": "Apr 2023",
            "resign_reason_ja": "一身上の都合により退社",
            "bullets": [
                "Developed REST APIs using FastAPI handling 10k+ daily requests with 99.9% uptime.",
                "Optimized PostgreSQL queries reducing average response time by 40%.",
                "Built automated testing pipelines using pytest cutting bug detection time by 50%."
            ],
            "visible": True
        },
        {
            "id": "exp_2",
            "company": "Freelance",
            "role": "Python & AI/ML Engineer",
            "startDate": "Jan 2023",
            "endDate": "Present",
            "bullets": [
                "Designed production-grade ML models for international clients using PyTorch and FastAPI.",
                "Built real-time chatbot system integrated with WhatsApp, Telegram, Facebook Messenger.",
                "Developed ECG cardiac abnormality detection model achieving 94% F1-score on PhysioNet dataset.",
                "Architected scalable backend systems with Redis caching and PostgreSQL data pipelines."
            ],
            "visible": True
        }
    ],
    "education": [
        {
            "id": "edu_1",
            "university": "Veer Narmad South Gujarat University",
            "degree": "Master of Computer Applications (MCA)",
            "major": "Computer Application",
            "year": "2022 – 2024",
            "awarded": "2024",
            "gpa": "A+",
            "notes": "Specialization in Artificial Intelligence",
            "visible": True,
            "order": 1
        },
        {
            "id": "edu_2",
            "university": "Vivekanand College of Computer Science",
            "degree": "Bachelor of Computer Applications (BCA)",
            "major": "Computer Application",
            "year": "2019 – 2022",
            "awarded": "2022",
            "gpa": "",
            "notes": "",
            "visible": True,
            "order": 2
        }
    ],
    "certifications": [],
    "achievements": [
        {"id": "ach_award_1", "title": "Data Structure Excellence Award", "year": "2018", "issuer": "Gujarat University", "description": "Academic excellence award in Data Structures", "visible": True},
        {"id": "ach_award_2", "title": "Database Management System Award", "year": "2018", "issuer": "Gujarat University", "description": "Academic excellence award in DBMS", "visible": True},
        {"id": "ach_award_3", "title": "Student of the Year", "year": "2019", "issuer": "Gujarat University", "description": "Awarded Student of the Year across the department", "visible": True},
        {"id": "ach_4", "title": "Most Diligent Employee", "year": "2022", "issuer": "Logixbuilt Infotech", "description": "Awarded Most Diligent Employee at Logixbuilt Infotech", "visible": True}
    ],
    "contactMessages": [],
    "analytics": [],
    "activityLog": [],
    "projects": [],
    "hiddenProjects": [],
    "projectSummaries": {},
    "settings": {"hero3d": True}
}

def load_data_from_sqlite():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT data FROM portfolio_data WHERE id = 1")
        row = cursor.fetchone()
        if not row:
            conn.execute(
                "INSERT INTO portfolio_data (id, data, updated_at) VALUES (1, ?, CURRENT_TIMESTAMP)",
                (json.dumps(DEFAULT_DATA, ensure_ascii=False),)
            )
            conn.commit()
            return DEFAULT_DATA.copy()
        return json.loads(row[0])

def load_data():
    global _data_cache, _data_cache_ts

    # ── Fast path: return from RAM cache ─────────────────────────────────────
    if _data_cache is not None and (time.time() - _data_cache_ts) < DATA_CACHE_TTL:
        return _data_cache

    with FileLock(LOCK_FILE, timeout=10):
        data = None
        
        # 1. Try reading directly from SQLite first
        try:
            with sqlite3.connect(DB_FILE) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT data FROM portfolio_data WHERE id = 1")
                row = cursor.fetchone()
                if row:
                    data = json.loads(row[0])
        except Exception as e:
            print(f"[database] SQLite direct read failed: {e}")

        # 2. Warm SQLite synchronously if it is completely empty
        if data is None:
            print("[database] SQLite cache empty. Syncing synchronously from Supabase...")
            try:
                from supabase_client import supabase
                if supabase is not None:
                    response = (
                        supabase
                        .table("portfolio_data")
                        .select("data")
                        .eq("id", 1)
                        .execute()
                    )
                    if response.data and len(response.data) > 0:
                        data = response.data[0]["data"]
                        if isinstance(data, str):
                            data = json.loads(data)
                        # Sync back to SQLite
                        with sqlite3.connect(DB_FILE) as conn:
                            conn.execute(
                                "INSERT OR REPLACE INTO portfolio_data (id, data, updated_at) VALUES (1, ?, CURRENT_TIMESTAMP)",
                                (json.dumps(data, ensure_ascii=False),)
                            )
                            conn.commit()
            except Exception as e:
                print(f"[database] Supabase sync fallback failed: {e}")

        # 3. Final fallback to DEFAULT_DATA if both failed
        if data is None:
            try:
                data = load_data_from_sqlite()
            except Exception as e:
                print(f"[database] SQLite fallback failed: {e}")
                data = DEFAULT_DATA.copy()

        # Run migration/normalization checks on `data`
        changed = False
    
        if "profile" in data:
            profile = data["profile"]
            if "personal" not in profile:
                profile["personal"] = DEFAULT_DATA["profile"]["personal"].copy()
                changed = True
            if "visa_info" not in profile:
                profile["visa_info"] = DEFAULT_DATA["profile"]["visa_info"].copy()
                changed = True
            if "visa" not in profile:
                profile["visa"] = DEFAULT_DATA["profile"]["visa"].copy()
                changed = True
            flat_to_personal = ["dob", "dateOfBirth", "gender", "nationality", "military_service", "marital_status"]
            for field in flat_to_personal:
                if field in profile:
                    target_field = "dob" if field == "dateOfBirth" else field
                    profile["personal"][target_field] = profile.pop(field)
                    changed = True
            flat_to_visa = ["visaType", "visaIssueDate", "visaExpiryDate"]
            for field in flat_to_visa:
                if field in profile:
                    profile["visa_info"][field] = profile.pop(field)
                    changed = True
            japan_fields = {
                "name_furigana": "", "nationality_ja": "", "address_furigana": "",
                "commute_time": "", "dependents_count": 0, "has_spouse": False,
                "spouse_dependency": False, "self_pr_ja": "", "self_pr_ja_detailed": "",
                "career_summary_ja": "", "desired_conditions_ja": "貴社の規定に従います。"
            }
            if "personal" in profile:
                for k, v in japan_fields.items():
                    if k not in profile["personal"]:
                        profile["personal"][k] = v
                        changed = True
        for k, v in DEFAULT_DATA.items():
            if k not in data:
                data[k] = v
                changed = True

        # ── Sync github / github_username in profile from connections ────────────
        connections = data.get("connections", [])
        github_conn = next((c for c in connections if c.get("platform", "").lower() == "github"), None)
        if github_conn:
            github_url = github_conn.get("url", "")
            github_handle = github_conn.get("handle", "")
            
            # Determine username from handle, fallback to url parsing
            username = github_handle
            if not username and github_url:
                username = github_url.rstrip("/").split("/")[-1]
                
            profile = data.setdefault("profile", {})
            if profile.get("github") != github_url or profile.get("github_username") != username:
                profile["github"] = github_url
                profile["github_username"] = username
                changed = True

        # ── Trim activityLog to 50 entries max ────────────────────────────
        if "activityLog" in data and len(data["activityLog"]) > 50:
            data["activityLog"] = data["activityLog"][:50]
            changed = True
                    
        if changed:
            _save_data_internal(data)

    # ── Calculate dynamic Stats (Metric Flux) ──────────────────────────────────
    if "stats" not in data:
        data["stats"] = {}

    # Calculate dynamic project count
    manual_count = sum(1 for p in data.get("projects", []) if p.get("visible") is not False)
    github_count = sum(1 for k, v in data.get("project_visibility", {}).items() if v is not False)
    total_projects = manual_count + github_count
    dynamic_project_count = f"{max(total_projects, 12)}+"

    # Set default values if not present
    if "card_1_value" not in data["stats"]:
        data["stats"]["card_1_value"] = dynamic_project_count
    if "card_1_label" not in data["stats"]:
        data["stats"]["card_1_label"] = "Systems Built"

    if "card_2_value" not in data["stats"]:
        data["stats"]["card_2_value"] = "94%"
    if "card_2_label" not in data["stats"]:
        data["stats"]["card_2_label"] = "ECG F1-Score"

    if "card_3_value" not in data["stats"]:
        data["stats"]["card_3_value"] = "Healthcare AI"
    if "card_3_label" not in data["stats"]:
        data["stats"]["card_3_label"] = "Biomedical Signal Processing"

    if "card_4_value" not in data["stats"]:
        data["stats"]["card_4_value"] = "AI + Backend"
    if "card_4_label" not in data["stats"]:
        data["stats"]["card_4_label"] = "Research to Production"

    # ── Update RAM cache ──────────────────────────────────────────────────────
    _data_cache = data
    _data_cache_ts = time.time()
    return data

def save_data(data):
    _invalidate_cache()  # Bust RAM cache immediately
    with FileLock(LOCK_FILE, timeout=10):
        _save_data_internal(data)

def _save_data_internal(data):
    # Trim activityLog before every save
    if "activityLog" in data and len(data["activityLog"]) > 50:
        data["activityLog"] = data["activityLog"][:50]

    # 1. Save to Supabase (Primary)
    try:
        from supabase_client import supabase
        if supabase is not None:
            supabase.table("portfolio_data").upsert({
                "id": 1,
                "data": data,
                "updated_at": datetime.now().isoformat()
            }).execute()
        else:
            raise ValueError("Supabase client is not initialized")
    except Exception as e:
        print(f"Supabase save failed: {e}")
        raise RuntimeError(f"Supabase save failed: {e}") from e

    # 2. Save to SQLite (Local backup)
    try:
        with sqlite3.connect(DB_FILE) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO portfolio_data (id, data, updated_at) VALUES (1, ?, CURRENT_TIMESTAMP)",
                (json.dumps(data, ensure_ascii=False),)
            )
            conn.commit()
    except Exception as e:
        print(f"SQLite save failed: {e}")

    _clear_pdf_cache_db_internal()

    try:
        from services.pregenerator import trigger_pdf_regeneration
        trigger_pdf_regeneration()
    except Exception as e:
        print(f"[database] Failed to trigger PDF pregeneration on save: {e}")


def log_resume_download(ip: str, country: str, region: str, format_label: str):
    """
    Logs a resume download event into the analytics list.
    Keeps only the last 100 entries to prevent file bloat.
    """
    with FileLock(LOCK_FILE, timeout=10):
        # Load fresh data
        data = None
        supabase_success = False
        try:
            from supabase_client import supabase
            if supabase is not None:
                response = (
                    supabase
                    .table("portfolio_data")
                    .select("data")
                    .eq("id", 1)
                    .execute()
                )
                if response.data and len(response.data) > 0:
                    data = response.data[0]["data"]
                    if isinstance(data, str):
                        data = json.loads(data)
                    supabase_success = True
        except Exception as e:
            print(f"Supabase load for log failed: {e}")

        if not supabase_success or data is None:
            try:
                data = load_data_from_sqlite()
            except Exception as e:
                print(f"SQLite load for log failed: {e}")
                data = DEFAULT_DATA.copy()
                
        if "analytics" not in data:
            data["analytics"] = []
            
        event_entry = {
            "timestamp": datetime.now().isoformat(),
            "event": "resume_download",
            "ip": ip,
            "country": country,
            "region": region,
            "format": format_label
        }
        
        data["analytics"].insert(0, event_entry)
        
        if len(data["analytics"]) > 100:
            data["analytics"] = data["analytics"][:100]
            
        # Save to both
        # 1. Supabase
        try:
            from supabase_client import supabase
            if supabase is not None:
                supabase.table("portfolio_data").upsert({
                    "id": 1,
                    "data": data,
                    "updated_at": datetime.now().isoformat()
                }).execute()
        except Exception as e:
            print(f"Supabase save for log failed: {e}")

        # 2. SQLite
        try:
            with sqlite3.connect(DB_FILE) as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO portfolio_data (id, data, updated_at) VALUES (1, ?, CURRENT_TIMESTAMP)",
                    (json.dumps(data, ensure_ascii=False),)
                )
                conn.commit()
        except Exception as e:
            print(f"SQLite save for log failed: {e}")
            
        _invalidate_cache()
            
    return event_entry

def get_cached_translation(field_name: str, locale: str, original_text: str):
    with FileLock(LOCK_FILE, timeout=10):
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT translated_text, is_verified FROM translations WHERE field_name = ? AND locale = ? AND original_text = ?",
                (field_name, locale, original_text)
            )
            return cursor.fetchone()

def save_translation(field_name: str, locale: str, original_text: str, translated_text: str, is_verified: bool = False):
    with FileLock(LOCK_FILE, timeout=10):
        with sqlite3.connect(DB_FILE) as conn:
            conn.execute(
                """INSERT OR REPLACE INTO translations 
                   (field_name, locale, original_text, translated_text, is_verified, updated_at) 
                   VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)""",
                (field_name, locale, original_text, translated_text, 1 if is_verified else 0)
            )
            conn.commit()

def mark_translation_verified(field_name: str, locale: str, original_text: str):
    with FileLock(LOCK_FILE, timeout=10):
        with sqlite3.connect(DB_FILE) as conn:
            conn.execute(
                "UPDATE translations SET is_verified = 1, updated_at = CURRENT_TIMESTAMP WHERE field_name = ? AND locale = ? AND original_text = ?",
                (field_name, locale, original_text)
            )
            conn.commit()

def get_cached_pdf_db(cache_key: str, ttl_seconds: int = 300):
    with FileLock(LOCK_FILE, timeout=10):
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT pdf_blob, created_at FROM pdf_cache WHERE id = ?",
                (cache_key,)
            )
            row = cursor.fetchone()
            if row:
                pdf_blob, created_at = row
                # Check TTL
                created_dt = datetime.fromisoformat(created_at.replace(" ", "T")) if " " in created_at else datetime.fromisoformat(created_at)
                if (datetime.now() - created_dt).total_seconds() < ttl_seconds:
                    return pdf_blob
                else:
                    # Expired
                    conn.execute("DELETE FROM pdf_cache WHERE id = ?", (cache_key,))
                    conn.commit()
            return None

def save_cached_pdf_db(cache_key: str, pdf_blob: bytes):
    with FileLock(LOCK_FILE, timeout=10):
        with sqlite3.connect(DB_FILE) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO pdf_cache (id, pdf_blob, created_at) VALUES (?, ?, CURRENT_TIMESTAMP)",
                (cache_key, sqlite3.Binary(pdf_blob))
            )
            conn.commit()

def _clear_pdf_cache_db_internal():
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("DELETE FROM pdf_cache")
        conn.commit()

def clear_pdf_cache_db():
    with FileLock(LOCK_FILE, timeout=10):
        _clear_pdf_cache_db_internal()

def get_all_translations():
    with FileLock(LOCK_FILE, timeout=10):
        with sqlite3.connect(DB_FILE) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM translations ORDER BY created_at DESC")
            return [dict(row) for row in cursor.fetchall()]

def delete_translation_db(t_id: int):
    with FileLock(LOCK_FILE, timeout=10):
        with sqlite3.connect(DB_FILE) as conn:
            conn.execute("DELETE FROM translations WHERE id = ?", (t_id,))
            conn.commit()

def set_local_cache(key: str, payload: dict, expires_at: str):
    """Inserts or replaces a generic JSON cache payload with expiration."""
    with FileLock(LOCK_FILE, timeout=10):
        with sqlite3.connect(DB_FILE) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO local_cache (cache_key, payload, updated_at, expires_at) VALUES (?, ?, CURRENT_TIMESTAMP, ?)",
                (key, json.dumps(payload, ensure_ascii=False), expires_at)
            )
            conn.commit()

def get_local_cache(key: str) -> dict | None:
    """Retrieves generic local cache payload, updated_at and expires_at."""
    with FileLock(LOCK_FILE, timeout=10):
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT payload, updated_at, expires_at FROM local_cache WHERE cache_key = ?", (key,))
            row = cursor.fetchone()
            if row:
                payload, updated_at, expires_at = row
                try:
                    loaded_payload = json.loads(payload) if payload else None
                except Exception:
                    loaded_payload = payload
                return {
                    "payload": loaded_payload,
                    "updated_at": updated_at,
                    "expires_at": expires_at
                }
            return None

def get_local_cache_with_health(key: str) -> dict | None:
    """Retrieves cache payload, metadata, success_at, error, and status columns."""
    with FileLock(LOCK_FILE, timeout=10):
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT payload, updated_at, expires_at, last_success_at, last_error, status FROM local_cache WHERE cache_key = ?", (key,))
            row = cursor.fetchone()
            if row:
                payload, updated_at, expires_at, last_success_at, last_error, status = row
                try:
                    loaded_payload = json.loads(payload) if payload else None
                except Exception:
                    loaded_payload = payload
                return {
                    "payload": loaded_payload,
                    "updated_at": updated_at,
                    "expires_at": expires_at,
                    "last_success_at": last_success_at,
                    "last_error": last_error,
                    "status": status
                }
            return None


