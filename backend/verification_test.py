import os
import requests
import time

BASE_URL = "http://localhost:8000/api/resume/download"
OUTPUT_DIR = "backend/test_outputs"

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# 12 Variations:
# Regions: japan, korea, china, international
# Languages: en, native (ja, ko, zh)
# Cover Letter: true, false (selected cases)

variations = [
    # Japan (Rirekisho + Shokumu)
    ("japan", "ja", "true"),
    ("japan", "ja", "false"),
    ("japan", "en", "true"),
    ("japan", "en", "false"),
    
    # Korea
    ("korea", "ko", "true"),
    ("korea", "en", "true"),
    
    # China
    ("china", "zh", "true"),
    ("china", "en", "true"),
    
    # ATS / International
    ("international", "en", "true"),
    ("international", "en", "false"),
    ("ats_usa", "en", "false"),
    ("ats_uk", "en", "false")
]

def run_tests():
    print(f"Starting Verification Test (12 variations)... Output: {OUTPUT_DIR}")
    
    for region, lang, cover in variations:
        filename = f"{region}_{lang}_cover{cover}.pdf"
        filepath = os.path.join(OUTPUT_DIR, filename)
        
        # Add a cache buster v={timestamp}
        url = f"{BASE_URL}/{region}?lang={lang}&cover={cover}&download=true&v={int(time.time())}"
        print(f"Generating {filename}...")
        
        try:
            start_time = time.time()
            response = requests.get(url, timeout=120)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                with open(filepath, "wb") as f:
                    f.write(response.content)
                print(f"DONE: Saved {filename} ({len(response.content) // 1024} KB) in {duration:.1f}s")
            else:
                print(f"FAIL: {filename}: Status {response.status_code}")
                # print(response.text)
        except Exception as e:
            print(f"ERROR generating {filename}: {e}")
        
        # Small delay to prevent overwhelming the translator/semaphore
        time.sleep(1)

if __name__ == "__main__":
    run_tests()
