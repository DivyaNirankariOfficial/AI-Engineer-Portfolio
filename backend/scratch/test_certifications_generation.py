import os
import sys
import asyncio
import json
import sqlite3

# Ensure sys.stdout handles UTF-8 on Windows
if sys.platform.startswith('win'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add the parent directory to the path so we can import services
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.pdf_playwright import generate_resume_playwright
from pypdf import PdfReader

async def main():
    print("Loading original portfolio data...")
    conn = sqlite3.connect('portfolio.db')
    c = conn.cursor()
    c.execute('SELECT data FROM portfolio_data WHERE id = 1')
    raw_data = c.fetchone()[0]
    conn.close()

    data = json.loads(raw_data)
    
    # Inject mock certifications
    data['certifications'] = [
        {
            "id": "cert_1",
            "name": "AWS Certified Solutions Architect",
            "issuer": "Amazon Web Services",
            "year": "2023",
            "visible": True
        },
        {
            "id": "cert_2",
            "name": "Certified Kubernetes Administrator (CKA)",
            "issuer": "Cloud Native Computing Foundation",
            "year": "2024",
            "visible": True
        },
        {
            "id": "cert_3",
            "name": "Oracle Java SE Programmer",
            "issuer": "Oracle",
            "year": "",
            "visible": True
        }
    ]

    print("Generating Chinese resume with certifications...")
    # Call generate_resume_playwright for China region with lang=zh
    pdf_bytes = await generate_resume_playwright(
        data=data,
        region="china",
        lang="zh",
        include_cover=False
    )
    
    output_dir = "test_outputs"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    output_path = os.path.join(output_dir, "china_zh_certs_test.pdf")
    with open(output_path, "wb") as f:
        f.write(pdf_bytes.getvalue())
        
    print(f"Saved generated PDF to {output_path}")

    # Read and verify PDF text
    reader = PdfReader(output_path)
    full_text = ""
    for page in reader.pages:
        full_text += page.extract_text()
        
    print("\n--- EXTRACTED PDF TEXT ---")
    print(full_text)
    print("--------------------------\n")
    
    # Check for expected headers and items
    # Column headers
    # "证书/考试" (L.cert_exam_label) and "备注" (L.remarks_label)
    checks = {
        "证书/考试": "证书/考试" in full_text,
        "备注": "备注" in full_text,
        "AWS Certified Solutions Architect": "AWS Certified Solutions Architect" in full_text,
        "Amazon Web Services (2023年)": "Amazon Web Services (2023年)" in full_text or "Amazon Web Services (2023)" in full_text,
        "Certified Kubernetes Administrator (CKA)": "Certified Kubernetes Administrator (CKA)" in full_text,
        "Cloud Native Computing Foundation (2024年)": "Cloud Native Computing Foundation (2024年)" in full_text or "Cloud Native Computing Foundation (2024)" in full_text,
        "Oracle Java SE Programmer": "Oracle Java SE Programmer" in full_text,
        "Oracle": "Oracle" in full_text and "Oracle (" not in full_text
    }
    
    print("Verification results:")
    all_ok = True
    for name, passed in checks.items():
        print(f"  {name}: {'PASSED' if passed else 'FAILED'}")
        if not passed:
            all_ok = False
            
    if all_ok:
        print("\nSUCCESS: All certifications table assertions passed!")
    else:
        print("\nFAILURE: Some assertions failed.")

if __name__ == "__main__":
    asyncio.run(main())
