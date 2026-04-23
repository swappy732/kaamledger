import sqlite3

def init_db():
    conn = sqlite3.connect('kaamledger.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS workers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            skill TEXT NOT NULL,
            aadhaar_last4 TEXT NOT NULL,
            qr_code TEXT,
            registered_on TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()
    print('Database ready!')

if __name__ == '__main__':
    init_db()