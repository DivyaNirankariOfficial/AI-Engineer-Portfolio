import sqlite3

def check():
    conn = sqlite3.connect('portfolio.db')
    c = conn.cursor()
    
    # 1. Check for PROTECTED_TERMS hallucination
    c.execute("SELECT id, field_name, translated_text FROM translations WHERE translated_text LIKE '%PROTECTED_TERMS%'")
    rows = c.fetchall()
    deleted = 0
    for row in rows:
        print(f"Deleting PROTECTED_TERMS bug for id {row[0]}")
        c.execute("DELETE FROM translations WHERE id=?", (row[0],))
        deleted += 1
        
    # 2. Check for "4+" in profile summaries
    c.execute("SELECT id, field_name, translated_text FROM translations WHERE (field_name='summary' OR field_name='pers_summary' OR field_name='career_summary') AND (translated_text LIKE '%4+%' OR translated_text LIKE '%4年%')")
    rows2 = c.fetchall()
    for row in rows2:
        print(f"Deleting '4+' experience bug for id {row[0]}")
        c.execute("DELETE FROM translations WHERE id=?", (row[0],))
        deleted += 1
        
    conn.commit()
    print(f"Deleted {deleted} rows")

if __name__ == '__main__':
    check()
