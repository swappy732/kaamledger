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

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            worker_id INTEGER NOT NULL,
            employer_phone TEXT NOT NULL,
            job_type TEXT NOT NULL,
            amount_paid REAL NOT NULL,
            rating INTEGER NOT NULL,
            confirmed_on TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (worker_id) REFERENCES workers (id)
        )
    ''')

    conn.commit()
    conn.close()
    print('Database ready!')

if __name__ == '__main__':
    init_db()