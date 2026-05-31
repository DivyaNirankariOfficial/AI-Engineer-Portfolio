import sqlite3
import json

def check():
    conn = sqlite3.connect('portfolio.db')
    c = conn.cursor()
    
    c.execute("SELECT id FROM translations WHERE translated_text LIKE '%<span%'")
    rows = c.fetchall()
    for row in rows:
        c.execute("DELETE FROM translations WHERE id=?", (row[0],))
    print(f"Deleted {len(rows)} translation bugs containing <span")
        
    c.execute("SELECT data FROM portfolio_data WHERE id=1")
    row = c.fetchone()
    if row:
        if "<span" in row[0]:
            print("Found <span in portfolio_data!")
            data = json.loads(row[0])
            personal = data.get('profile', {}).get('personal', {})
            for k, v in personal.items():
                if isinstance(v, str) and "<span" in v:
                    import re
                    clean = re.sub(r'<[^>]+>', '', v)
                    personal[k] = clean
            c.execute("UPDATE portfolio_data SET data=? WHERE id=1", (json.dumps(data, ensure_ascii=False),))
            print("Cleaned portfolio_data")
            
    conn.commit()

if __name__ == '__main__':
    check()
