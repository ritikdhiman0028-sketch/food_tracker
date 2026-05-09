"""
Food Tracker - Flask Backend with SQLite
Run: python app.py
Then open: http://localhost:5000
"""

from flask import Flask, jsonify, request, render_template, session, redirect, url_for
import sqlite3, os, uuid, hashlib
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'food-tracker-secret-key-2024'

DB_PATH = os.path.join(os.path.dirname(__file__), 'food_tracker.db')

# Admin credentials
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'admin123'

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def init_db():
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id       TEXT PRIMARY KEY,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS foods (
                id      TEXT PRIMARY KEY,
                name    TEXT NOT NULL,
                protein REAL NOT NULL DEFAULT 0,
                carbs   REAL NOT NULL DEFAULT 0,
                fat     REAL NOT NULL DEFAULT 0,
                user_id TEXT
            );
            CREATE TABLE IF NOT EXISTS dates (
                id      TEXT PRIMARY KEY,
                date    TEXT NOT NULL,
                user_id TEXT,
                UNIQUE(date, user_id)
            );
            CREATE TABLE IF NOT EXISTS date_foods (
                id      INTEGER PRIMARY KEY AUTOINCREMENT,
                date_id TEXT NOT NULL REFERENCES dates(id) ON DELETE CASCADE,
                food_id TEXT NOT NULL REFERENCES foods(id) ON DELETE CASCADE
            );
        """)

def get_current_user():
    return session.get('user')

def get_current_user_id():
    user = session.get('user')
    if user:
        return user.get('id')
    # Guest: assign a persistent session-scoped guest ID so data is isolated
    if 'guest_id' not in session:
        session['guest_id'] = 'guest_' + uuid.uuid4().hex[:12]
    return session['guest_id']

def is_admin():
    user = session.get('user')
    return user and user.get('role') == 'admin'

@app.route('/login')
def login_page():
    if session.get('user'):
        return redirect('/')
    return render_template('login.html')

@app.route('/api/auth/login', methods=['POST'])
def login():
    body = request.get_json()
    username = (body.get('username') or '').strip()
    password = (body.get('password') or '').strip()
    role = body.get('role', 'user')

    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400

    if role == 'admin':
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['user'] = {'id': 'admin', 'username': ADMIN_USERNAME, 'role': 'admin'}
            return jsonify({'ok': True, 'role': 'admin', 'username': ADMIN_USERNAME})
        return jsonify({'error': 'Invalid admin credentials'}), 401

    with get_db() as conn:
        row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        if not row or row['password'] != hash_password(password):
            return jsonify({'error': 'Invalid username or password'}), 401
        session['user'] = {'id': row['id'], 'username': row['username'], 'role': 'user'}
    return jsonify({'ok': True, 'role': 'user', 'username': username})

@app.route('/api/auth/register', methods=['POST'])
def register():
    body = request.get_json()
    username = (body.get('username') or '').strip()
    password = (body.get('password') or '').strip()

    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400
    if len(username) < 3:
        return jsonify({'error': 'Username must be at least 3 characters'}), 400
    if len(password) < 4:
        return jsonify({'error': 'Password must be at least 4 characters'}), 400

    uid = 'u_' + uuid.uuid4().hex[:10]
    try:
        with get_db() as conn:
            conn.execute("INSERT INTO users (id, username, password) VALUES (?, ?, ?)",
                         (uid, username, hash_password(password)))
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Username already taken'}), 409

    session['user'] = {'id': uid, 'username': username, 'role': 'user'}
    return jsonify({'ok': True, 'username': username}), 201

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    session.pop('user', None)
    return jsonify({'ok': True})

@app.route('/api/auth/me', methods=['GET'])
def me():
    user = session.get('user')
    if not user:
        return jsonify({'loggedIn': False})
    return jsonify({'loggedIn': True, 'username': user['username'], 'role': user['role']})

@app.route('/api/admin/users', methods=['GET'])
def get_all_users():
    if not is_admin():
        return jsonify({'error': 'Forbidden'}), 403
    with get_db() as conn:
        rows = conn.execute("SELECT id, username FROM users ORDER BY username").fetchall()
    return jsonify([dict(r) for r in rows])

@app.route('/api/admin/users/<uid>', methods=['DELETE'])
def delete_user(uid):
    if not is_admin():
        return jsonify({'error': 'Forbidden'}), 403
    with get_db() as conn:
        # Delete all foods and dates belonging to the user (cascade via Python since no FK)
        date_ids = [r['id'] for r in conn.execute("SELECT id FROM dates WHERE user_id = ?", (uid,)).fetchall()]
        for did in date_ids:
            conn.execute("DELETE FROM date_foods WHERE date_id = ?", (did,))
        conn.execute("DELETE FROM dates WHERE user_id = ?", (uid,))
        conn.execute("DELETE FROM foods WHERE user_id = ?", (uid,))
        conn.execute("DELETE FROM users WHERE id = ?", (uid,))
    return jsonify({'ok': True})

@app.route('/api/admin/users/<uid>/dates', methods=['GET'])
def get_user_dates_admin(uid):
    if not is_admin():
        return jsonify({'error': 'Forbidden'}), 403
    with get_db() as conn:
        dates = conn.execute("SELECT * FROM dates WHERE user_id = ? ORDER BY date DESC", (uid,)).fetchall()
        result = []
        for d in dates:
            food_ids = conn.execute(
                "SELECT food_id FROM date_foods WHERE date_id = ?", (d['id'],)
            ).fetchall()
            result.append({'id': d['id'], 'date': d['date'], 'foodIds': [r['food_id'] for r in food_ids]})
    return jsonify(result)

@app.route('/api/admin/users/<uid>/foods', methods=['GET'])
def get_user_foods_admin(uid):
    if not is_admin():
        return jsonify({'error': 'Forbidden'}), 403
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM foods WHERE user_id = ? ORDER BY name", (uid,)).fetchall()
    return jsonify([dict(r) for r in rows])

@app.route('/')
def index():
    if is_admin():
        return redirect('/admin')
    return render_template('home.html')

@app.route('/add-food')
def add_food_page():
    if is_admin():
        return redirect('/admin')
    return render_template('add_food.html')

@app.route('/view-date')
def view_date_page():
    if is_admin():
        return redirect('/admin')
    date_id = request.args.get('id', '')
    return render_template('view_date.html', date_id=date_id)

@app.route('/admin')
def admin_page():
    return render_template('admin.html')

@app.route('/api/foods', methods=['GET'])
def get_foods():
    user_id = get_current_user_id()
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM foods WHERE user_id = ? ORDER BY name", (user_id,)).fetchall()
    return jsonify([dict(r) for r in rows])

@app.route('/api/foods', methods=['POST'])
def add_food():
    body = request.get_json()
    name = (body.get('name') or '').strip()
    if not name:
        return jsonify({'error': 'Name is required'}), 400
    user_id = get_current_user_id()
    food = {
        'id':      'fd_' + uuid.uuid4().hex[:10],
        'name':    name,
        'protein': float(body.get('protein', 0)),
        'carbs':   float(body.get('carbs', 0)),
        'fat':     float(body.get('fat', 0)),
        'user_id': user_id,
    }
    with get_db() as conn:
        conn.execute(
            "INSERT INTO foods (id, name, protein, carbs, fat, user_id) VALUES (?, ?, ?, ?, ?, ?)",
            (food['id'], food['name'], food['protein'], food['carbs'], food['fat'], food['user_id'])
        )
    return jsonify(food), 201

@app.route('/api/foods/<fid>', methods=['PUT'])
def update_food(fid):
    body = request.get_json()
    name = (body.get('name') or '').strip()
    if not name:
        return jsonify({'error': 'Name is required'}), 400
    with get_db() as conn:
        row = conn.execute("SELECT * FROM foods WHERE id = ?", (fid,)).fetchone()
        if not row:
            return jsonify({'error': 'Not found'}), 404
        conn.execute(
            "UPDATE foods SET name=?, protein=?, carbs=?, fat=? WHERE id=?",
            (name, float(body.get('protein', row['protein'])),
             float(body.get('carbs', row['carbs'])),
             float(body.get('fat', row['fat'])), fid)
        )
        updated = conn.execute("SELECT * FROM foods WHERE id = ?", (fid,)).fetchone()
    return jsonify(dict(updated))

@app.route('/api/foods/<fid>', methods=['DELETE'])
def delete_food(fid):
    with get_db() as conn:
        conn.execute("DELETE FROM foods WHERE id = ?", (fid,))
    return jsonify({'ok': True})

@app.route('/api/dates', methods=['GET'])
def get_dates():
    user_id = get_current_user_id()
    with get_db() as conn:
        dates = conn.execute("SELECT * FROM dates WHERE user_id = ? ORDER BY date DESC", (user_id,)).fetchall()
        result = []
        for d in dates:
            food_ids = conn.execute("SELECT food_id FROM date_foods WHERE date_id = ?", (d['id'],)).fetchall()
            result.append({'id': d['id'], 'date': d['date'], 'foodIds': [r['food_id'] for r in food_ids]})
    return jsonify(result)

@app.route('/api/dates', methods=['POST'])
def add_date():
    body = request.get_json()
    date_str = (body.get('date') or '').strip()
    if not date_str:
        return jsonify({'error': 'Date is required'}), 400
    user_id = get_current_user_id()
    entry = {'id': 'dt_' + uuid.uuid4().hex[:10], 'date': date_str, 'foodIds': []}
    try:
        with get_db() as conn:
            conn.execute("INSERT INTO dates (id, date, user_id) VALUES (?, ?, ?)",
                         (entry['id'], entry['date'], user_id))
    except sqlite3.IntegrityError:
        return jsonify({'error': 'That date already exists'}), 409
    return jsonify(entry), 201

@app.route('/api/dates/<did>', methods=['DELETE'])
def delete_date(did):
    with get_db() as conn:
        conn.execute("DELETE FROM dates WHERE id = ?", (did,))
    return jsonify({'ok': True})

@app.route('/api/dates/<did>/foods', methods=['POST'])
def add_food_to_date(did):
    body = request.get_json()
    fid  = body.get('foodId')
    with get_db() as conn:
        if not conn.execute("SELECT 1 FROM dates WHERE id = ?", (did,)).fetchone():
            return jsonify({'error': 'Date not found'}), 404
        if not fid or not conn.execute("SELECT 1 FROM foods WHERE id = ?", (fid,)).fetchone():
            return jsonify({'error': 'Invalid food id'}), 400
        conn.execute("INSERT INTO date_foods (date_id, food_id) VALUES (?, ?)", (did, fid))
        food_ids = conn.execute("SELECT food_id FROM date_foods WHERE date_id = ?", (did,)).fetchall()
    return jsonify({'id': did, 'foodIds': [r['food_id'] for r in food_ids]})

@app.route('/api/dates/<did>/foods/<fid>', methods=['DELETE'])
def remove_food_from_date(did, fid):
    with get_db() as conn:
        if not conn.execute("SELECT 1 FROM dates WHERE id = ?", (did,)).fetchone():
            return jsonify({'error': 'Date not found'}), 404
        row = conn.execute(
            "SELECT id FROM date_foods WHERE date_id = ? AND food_id = ? LIMIT 1", (did, fid)
        ).fetchone()
        if row:
            conn.execute("DELETE FROM date_foods WHERE id = ?", (row['id'],))
        food_ids = conn.execute("SELECT food_id FROM date_foods WHERE date_id = ?", (did,)).fetchall()
    return jsonify({'id': did, 'foodIds': [r['food_id'] for r in food_ids]})

if __name__ == '__main__':
    init_db()
    import webbrowser, threading
    def open_browser():
        import time; time.sleep(1)
        webbrowser.open('http://localhost:5000')
    threading.Thread(target=open_browser, daemon=True).start()
    print("\n🥗  Food Tracker is running!")
    print("   Open: http://localhost:5000")
    print("   Admin login: admin / admin123")
    print("   Press Ctrl+C to stop.\n")
    app.run(debug=False, port=5000)
