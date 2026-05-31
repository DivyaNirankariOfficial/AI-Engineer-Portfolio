import sqlite3
import json
import re

def strip_tags(obj):
    if isinstance(obj, str):
        # Only strip span tags from direct edit to avoid stripping intended HTML if any
        if "<span class=\"de-editable\"" in obj:
            return re.sub(r'<[^>]+>', '', obj)
        return obj
    elif isinstance(obj, dict):
        for k, v in obj.items():
            obj[k] = strip_tags(v)
        return obj
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            obj[i] = strip_tags(v)
        return obj
    else:
        return obj

def check():
    conn = sqlite3.connect('portfolio.db')
    c = conn.cursor()
        
    c.execute("SELECT data FROM portfolio_data WHERE id=1")
    row = c.fetchone()
    if row:
        data = json.loads(row[0])
        cleaned_data = strip_tags(data)
        c.execute("UPDATE portfolio_data SET data=? WHERE id=1", (json.dumps(cleaned_data, ensure_ascii=False),))
        print("Cleaned all span tags from portfolio_data")
            
    conn.commit()

if __name__ == '__main__':
    check()
