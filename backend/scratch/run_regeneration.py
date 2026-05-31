import asyncio
import sys
import os

# Add backend directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.pregenerator import regenerate_all

async def main():
    try:
        print("Starting regeneration...")
        result = await regenerate_all(triggered_by="manual_scratch")
        print("Result:", result)
    except Exception as e:
        print("Error during regeneration:", e)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
