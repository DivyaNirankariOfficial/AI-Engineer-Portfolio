import asyncio
import os
import sys
import json
from dotenv import load_dotenv

# Force UTF-8 stdout
if sys.platform.startswith('win'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

load_dotenv("d:/project/backend/.env")

# Add backend directory to sys.path
sys.path.append("d:/project/backend")

from database import load_data
from services.cover_letter_service import generate_dynamic_cover_letter

async def main():
    data = load_data()
    print("Testing generate_dynamic_cover_letter for region='china', lang='en'...")
    cl_en = await generate_dynamic_cover_letter('china', 'en', data)
    print("\n--- CHINA EN ---")
    print(cl_en)
    
    print("\nTesting generate_dynamic_cover_letter for region='china', lang='zh'...")
    cl_zh = await generate_dynamic_cover_letter('china', 'zh', data)
    print("\n--- CHINA ZH ---")
    print(cl_zh)

if __name__ == "__main__":
    asyncio.run(main())
