from flask import Flask, request, jsonify, send_file, render_template, send_from_directory
import sqlite3
import qrcode
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
import io

app = Flask(__name__)

def get_db():
    conn = sqlite3.connect('kaamledger.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register-worker')
def register_worker_page():
    return render_template('register.html')

@app.route('/verify')
def verify_page():
    return render_template('verify.html')

@app.route('/confirm-job')
def confirm_job_page():
    return render_template('confirm.html')

@app.route('/confirm/<int:worker_id>')
def whatsapp_confirm(worker_id):
    return render_template('whatsapp_confirm.html')

@app.route('/myqr/<int:worker_id>')
def my_qr(worker_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM workers WHERE id = ?', (worker_id,))
    worker = cursor.fetchone()
    conn.close()

    if worker is None:
        return jsonify({'error': 'Worker not found'}), 404

    return render_template('myqr.html', worker=worker)


@app.route('/qrcode/<int:worker_id>')
def serve_qr(worker_id):
    return send_from_directory('qrcodes', f'worker_{worker_id}.png')

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

    qr_data = f'https://kaamledger.onrender.com/confirm/{worker_id}'
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

@app.route('/certificate/<int:worker_id>', methods=['GET'])
def generate_certificate(worker_id):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM workers WHERE id = ?', (worker_id,))
    worker = cursor.fetchone()

    if worker is None:
        return jsonify({'error': 'Worker not found'}), 404

    cursor.execute('''
        SELECT * FROM jobs WHERE worker_id = ?
        ORDER BY confirmed_on DESC
    ''', (worker_id,))
    jobs = cursor.fetchall()
    conn.close()

    total_jobs = len(jobs)
    total_earnings = sum(job['amount_paid'] for job in jobs)
    avg_rating = round(sum(job['rating'] for job in jobs) / total_jobs, 1) if total_jobs > 0 else 0

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("KaamLedger", styles['Title']))
    elements.append(Paragraph("Verified Work History Certificate", styles['Heading2']))
    elements.append(Spacer(1, 20))

    elements.append(Paragraph(f"Name: {worker['name']}", styles['Normal']))
    elements.append(Paragraph(f"Skill: {worker['skill']}", styles['Normal']))
    elements.append(Paragraph(f"Phone: {worker['phone']}", styles['Normal']))
    elements.append(Spacer(1, 20))

    elements.append(Paragraph(f"Total Jobs Completed: {total_jobs}", styles['Normal']))
    elements.append(Paragraph(f"Total Earnings: Rs. {total_earnings}", styles['Normal']))
    elements.append(Paragraph(f"Average Rating: {avg_rating} / 5", styles['Normal']))
    elements.append(Spacer(1, 20))

    elements.append(Paragraph("Job History", styles['Heading3']))

    table_data = [['Job Type', 'Amount Paid', 'Rating', 'Date']]
    for job in jobs:
        table_data.append([
            job['job_type'],
            f"Rs. {job['amount_paid']}",
            f"{job['rating']}/5",
            job['confirmed_on'][:10]
        ])

    table = Table(table_data, colWidths=[150, 100, 80, 120])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 20))
    elements.append(Paragraph(f"Verification ID: KL-{worker_id:04d}-{total_jobs}", styles['Normal']))
    elements.append(Paragraph("This certificate is auto-generated by KaamLedger.", styles['Normal']))

    doc.build(elements)
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name=f'kaamledger_certificate_{worker_id}.pdf',
        mimetype='application/pdf'
    )

if __name__ == '__main__':
    app.run(debug=True)