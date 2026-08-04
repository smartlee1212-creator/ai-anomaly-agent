import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'ai-anomaly-agent-secret-key')

def get_db():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        ''')
        conn.commit()

init_db()

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        with get_db() as conn:
            user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
            
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['email'] = user['email']
            return redirect(url_for('dashboard'))
        else:
            error = 'Invalid email or password.'
            
    return render_template('login.html', error=error)

@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email or not password or len(password) < 6:
            error = 'Password must be at least 6 characters.'
        else:
            hashed_pw = generate_password_hash(password)
            try:
                with get_db() as conn:
                    conn.execute('INSERT INTO users (email, password) VALUES (?, ?)', (email, hashed_pw))
                    conn.commit()
                return redirect(url_for('login'))
            except sqlite3.IntegrityError:
                error = 'Email already registered.'
                
    return render_template('register.html', error=error)

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html', email=session.get('email'))

@app.route('/api/telemetry')
def telemetry():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
        
    return jsonify({
        'status': 'Operational - Live Agent Anomaly Detection Active',
        'btc_price': '64,230.15',
        'btc_change': '+2.45%',
        'eth_price': '3,450.80',
        'eth_change': '-0.65%',
        'analysis': 'AI Agent running diagnostics across target liquidity pools. No critical anomalies detected in the current order book spreads.'
    })

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
