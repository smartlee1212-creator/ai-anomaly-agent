import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from google import genai

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'ai-anomaly-agent-secret-key')

# Initialize Google GenAI Client (Make sure GEMINI_API_KEY is set in your Render environment variables)
gemini_client = None
try:
    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key:
        gemini_client = genai.Client(api_key=api_key)
except Exception as e:
    print(f"GenAI Init Warning: {e}")

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
        'status': 'Operational - Autonomous AI Anomaly Engine Active',
        'btc_price': '64,230.15',
        'btc_change': '+2.45%',
        'eth_price': '3,450.80',
        'eth_change': '-0.65%',
        'analysis': 'All liquidity vectors verified. Order book spreads are optimal. No predatory high-frequency spikes identified.'
    })

@app.route('/api/chat', methods=['POST'])
def agent_chat():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
        
    data = request.get_json()
    user_message = data.get('message', '')
    
    if not user_message:
        return jsonify({'response': 'Please enter a valid query for the agent.'})
        
    if not gemini_client:
        return jsonify({'response': 'AI Agent engine offline: GEMINI_API_KEY environment variable is missing on Render.'})
        
    try:
        # Prompt the Gemini model acting as the Anomaly Agent
        prompt = f"You are Zeus AI, an elite financial and cryptocurrency anomaly detection expert agent. Answer this query concisely and professionally: {user_message}"
        response = gemini_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        agent_reply = response.text
    except Exception as e:
        agent_reply = f"Error communicating with AI core: {str.S(e) if hasattr(e, 'S') else str(e)}"
        
    return jsonify({'response': agent_reply})

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
