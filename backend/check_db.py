import sqlite3

def check():
    conn = sqlite3.connect('portfolio.db')
    c = conn.cursor()
    c.execute("SELECT id, field_name, original_text, translated_text FROM translations WHERE locale='ko'")
    rows = c.fetchall()
    deleted = 0
    for row in rows:
        if not row[3] or row[3].strip() == '':
            c.execute("DELETE FROM translations WHERE id=?", (row[0],))
            deleted += 1
    
    # Also for Chinese resume empty project bug
    c.execute("SELECT id, field_name, original_text, translated_text FROM translations WHERE locale='zh'")
    rows_zh = c.fetchall()
    for row in rows_zh:
        if not row[3] or row[3].strip() == '':
            c.execute("DELETE FROM translations WHERE id=?", (row[0],))
            deleted += 1
            
    conn.commit()
    print(f"Deleted {deleted} empty translations")

if __name__ == '__main__':
    check()
