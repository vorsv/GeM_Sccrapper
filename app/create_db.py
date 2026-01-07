import sqlite3

def init_db():
    conn = sqlite3.connect("tenders.db")
    c = conn.cursor()
    
    # Added 'start_date' to the schema
    c.execute('''
        CREATE TABLE IF NOT EXISTS tenders (
            bid_no TEXT PRIMARY KEY,
            title TEXT,           -- This stores the 'Keyword Matched'
            items TEXT,
            department TEXT,
            start_date TEXT,      -- NEW COLUMN
            end_date TEXT,
            link TEXT,
            status TEXT DEFAULT 'New',
            pdf_path TEXT,
            found_at TEXT
        )
    ''')
    conn.commit()
    conn.close()
    print("✅ New Database created with 'start_date' column.")

if __name__ == "__main__":
    init_db()