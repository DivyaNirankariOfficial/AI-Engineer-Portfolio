import sqlite3

def query():
    conn = sqlite3.connect('d:/project/backend/portfolio.db')
    c = conn.cursor()
    c.execute("SELECT id, locale, field_name, original_text, translated_text FROM translations WHERE original_text LIKE '%28%' OR original_text LIKE '%age%' OR field_name LIKE '%age%'")
    rows = c.fetchall()
    print("Found rows in translations table:")
    for row in rows:
        print(row)
    conn.close()

if __name__ == '__main__':
    query()
