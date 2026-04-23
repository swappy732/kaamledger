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

if __name__ == '__main__':
    app.run(debug=True)