from flask import Flask, request, jsonify
import sqlite3
import qrcode
import os

app = Flask(__name__)

def get_db():
    conn = sqlite3.connect('kaamledger.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def home():
    return 'KaamLedger is running!'

@app.route('/register', methods=['POST'])
def register_worker():
    data = request.get_json()
    name = data['name']
    phone = data['phone']
    skill = data['skill']
    aadhaar_last4 = data['aadhaar_last4']

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO workers (name, phone, skill, aadhaar_last4)
        VALUES (?, ?, ?, ?)
    ''', (name, phone, skill, aadhaar_last4))
    conn.commit()
    worker_id = cursor.lastrowid

    qr_data = f'http://127.0.0.1:5000/worker/{worker_id}'
    qr_img = qrcode.make(qr_data)
    os.makedirs('qrcodes', exist_ok=True)
    qr_path = f'qrcodes/worker_{worker_id}.png'
    qr_img.save(qr_path)

    cursor.execute('UPDATE workers SET qr_code = ? WHERE id = ?',
                   (qr_path, worker_id))
    conn.commit()
    conn.close()

    return jsonify({
        'message': 'Worker registered!',
        'worker_id': worker_id,
        'qr_code': qr_path
    })

@app.route('/worker/<int:worker_id>', methods=['GET'])
def get_worker(worker_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM workers WHERE id = ?', (worker_id,))
    worker = cursor.fetchone()
    conn.close()

    if worker is None:
        return jsonify({'error': 'Worker not found'}), 404

    return jsonify({
        'id': worker['id'],
        'name': worker['name'],
        'phone': worker['phone'],
        'skill': worker['skill'],
        'registered_on': worker['registered_on']
    })
@app.route('/confirm', methods=['POST'])
def confirm_job():
    data = request.get_json()
    worker_id = data['worker_id']
    employer_phone = data['employer_phone']
    job_type = data['job_type']
    amount_paid = data['amount_paid']
    rating = data['rating']

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO jobs (worker_id, employer_phone, job_type, amount_paid, rating)
        VALUES (?, ?, ?, ?, ?)
    ''', (worker_id, employer_phone, job_type, amount_paid, rating))
    conn.commit()
    conn.close()

    return jsonify({
        'message': 'Job confirmed successfully!',
        'worker_id': worker_id,
        'job_type': job_type,
        'amount_paid': amount_paid
    })

@app.route('/history/<int:worker_id>', methods=['GET'])
def job_history(worker_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM jobs WHERE worker_id = ?
        ORDER BY confirmed_on DESC
    ''', (worker_id,))
    jobs = cursor.fetchall()
    conn.close()

    result = []
    for job in jobs:
        result.append({
            'job_id': job['id'],
            'job_type': job['job_type'],
            'amount_paid': job['amount_paid'],
            'rating': job['rating'],
            'employer_phone': job['employer_phone'],
            'confirmed_on': job['confirmed_on']
        })

    return jsonify({
        'worker_id': worker_id,
        'total_jobs': len(result),
        'jobs': result
    })
if __name__ == '__main__':
    app.run(debug=True)