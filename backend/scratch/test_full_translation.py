import os
import sys
import asyncio
from pathlib import Path
from pypdf import PdfReader

# Setup sys path so we can import from backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database import load_data
from services.pregenerator import _build_merged_projects, _generate_one, OUTPUT_DIR

# Force UTF-8 stdout for Windows consoles
if sys.platform.startswith('win'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

async def test_generation():
    print("Loading data...")
    data = load_data()
    
    print("Building merged projects...")
    merged_projects = await _build_merged_projects(data)
    
    # 1. Generate Japan Japanese Resume
    print("\n1. Generating Japan Japanese Resume...")
    output_path_ja = OUTPUT_DIR / "test_japan_ja.pdf"
    success_ja = await _generate_one(data, merged_projects, "japan", "ja", True, output_path_ja)
    print(f"Japan JA Generation: {'SUCCESS' if success_ja else 'FAILED'}")

    # 2. Generate Korea Korean Resume
    print("\n2. Generating Korea Korean Resume...")
    output_path_ko = OUTPUT_DIR / "test_korea_ko.pdf"
    success_ko = await _generate_one(data, merged_projects, "korea", "ko", True, output_path_ko)
    print(f"Korea KO Generation: {'SUCCESS' if success_ko else 'FAILED'}")

    # 3. Verify content
    if success_ko:
        print("\n==================== VERIFYING KOREAN RESUME ====================")
        reader = PdfReader(output_path_ko)
        full_text = ""
        for page in reader.pages:
            full_text += page.extract_text()
            
        print("--- Skills Section ---")
        lines = full_text.split('\n')
        skills_found = False
        for idx, line in enumerate(lines):
            if "보유 기술" in line or "Skills" in line or "숙련도" in line:
                skills_found = True
                print("CONTEXT:")
                start = max(0, idx - 2)
                end = min(len(lines), idx + 10)
                for c_line in lines[start:end]:
                    print("  >", c_line)
                break
        if not skills_found:
            print("Warning: Skills section heading not found in Korean PDF text!")

        print("\n--- Projects Section ---")
        projects_found = False
        for idx, line in enumerate(lines):
            if "프로젝트명" in line:
                projects_found = True
                print("CONTEXT:")
                start = max(0, idx)
                end = min(len(lines), idx + 8)
                for c_line in lines[start:end]:
                    print("  >", c_line)
                break
        if not projects_found:
            print("Warning: Projects section heading not found in Korean PDF text!")

if __name__ == "__main__":
    import sqlite3
    from database import DB_FILE, LOCK_FILE
    from filelock import FileLock
    
    print("Clearing unverified translations from database...")
    with FileLock(LOCK_FILE, timeout=10):
        with sqlite3.connect(DB_FILE) as conn:
            conn.execute("DELETE FROM translations WHERE is_verified = 0")
            conn.commit()
    print("Cache cleared. Starting generation test...\n")
    
    asyncio.run(test_generation())
