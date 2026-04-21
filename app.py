"""
GasBook Backend  |  Flask + MySQL
File: app.py  (self-contained — config.py merged in)

Config is loaded from config.env via python-dotenv.
Falls back to safe defaults so the app starts without .env.
"""

from flask import Flask, request, jsonify, session, render_template_string, send_from_directory
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error, IntegrityError
from datetime import datetime
import logging
import os
from dotenv import load_dotenv

# ── Load config.env ───────────────────────────────────────────────────────────
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(_BASE_DIR, 'config.env'))

# ── Inline Config (merged from config.py) ────────────────────────────────────
def _bool(val: str, default: bool = False) -> bool:
    return val.lower() in ('1', 'true', 'yes') if val else default

_cors_raw = os.environ.get(
    'CORS_ORIGINS',
    'http://localhost:5002,http://127.0.0.1:5002,http://localhost:3000,'
    'http://127.0.0.1:3000,http://localhost:5500,null'
)

class Config:
    """Application Configuration — sourced from config.env"""
    # Flask
    SECRET_KEY     = os.environ.get('SECRET_KEY', 'gasbook-secret-key-2024')
    DEBUG          = _bool(os.environ.get('DEBUG', 'false'))
    FLASK_ENV      = os.environ.get('FLASK_ENV', 'production')
    FLASK_PORT     = int(os.environ.get('FLASK_PORT', 5002))
    JSON_SORT_KEYS = False
    # MySQL
    MYSQL_HOST     = os.environ.get('MYSQL_HOST',     'db')
    MYSQL_USER     = os.environ.get('MYSQL_USER',     'gasbook_user')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', 'gasbook_pass')
    MYSQL_DATABASE = os.environ.get('MYSQL_DATABASE', 'gasbook')
    MYSQL_PORT     = int(os.environ.get('MYSQL_PORT', 3306))
    # CORS
    CORS_ORIGINS   = [o.strip() for o in _cors_raw.split(',') if o.strip()]

# ── App & Config ──────────────────────────────────────────────────────────────
app = Flask(__name__)
app.config.from_object(Config)          # ← uses inline class, no import needed

# ── CORS ──────────────────────────────────────────────────────────────────────
CORS(app,
     origins=app.config.get('CORS_ORIGINS', ['null', 'http://localhost:5002']),
     supports_credentials=True,
     allow_headers=['Content-Type', 'Authorization'],
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# ── Web Status Page ───────────────────────────────────────────────────────────
STATUS_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>GasBook API — Status</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet"/>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    :root {
      --bg:      #0f1117;
      --card:    #1a1d27;
      --accent:  #6c63ff;
      --accent2: #ff6584;
      --green:   #00d084;
      --red:     #ff4d4f;
      --text:    #e0e0ef;
      --sub:     #8888aa;
    }
    body {
      font-family: 'Inter', sans-serif;
      background: var(--bg);
      color: var(--text);
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 2rem;
    }
    .card {
      background: var(--card);
      border-radius: 20px;
      padding: 2.5rem 3rem;
      max-width: 680px;
      width: 100%;
      box-shadow: 0 8px 40px rgba(108,99,255,.25);
      border: 1px solid rgba(108,99,255,.2);
    }
    .logo {
      font-size: 2.2rem;
      font-weight: 700;
      background: linear-gradient(135deg, var(--accent), var(--accent2));
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      margin-bottom: .4rem;
    }
    .subtitle { color: var(--sub); font-size: .95rem; margin-bottom: 2rem; }
    .badge {
      display: inline-flex;
      align-items: center;
      gap: .45rem;
      padding: .35rem .85rem;
      border-radius: 999px;
      font-size: .82rem;
      font-weight: 600;
      margin-bottom: 1.8rem;
    }
    .badge.ok  { background: rgba(0,208,132,.12); color: var(--green); border: 1px solid rgba(0,208,132,.3); }
    .badge.err { background: rgba(255,77,79,.12);  color: var(--red);   border: 1px solid rgba(255,77,79,.3); }
    .dot { width: 8px; height: 8px; border-radius: 50%; }
    .dot.ok  { background: var(--green); box-shadow: 0 0 8px var(--green); animation: pulse 1.5s infinite; }
    .dot.err { background: var(--red); }
    @keyframes pulse {
      0%,100% { opacity: 1; } 50% { opacity: .4; }
    }
    table { width: 100%; border-collapse: collapse; }
    th, td { padding: .65rem .8rem; text-align: left; font-size: .88rem; }
    th { color: var(--sub); font-weight: 600; border-bottom: 1px solid rgba(255,255,255,.06); }
    tr:not(:last-child) td { border-bottom: 1px solid rgba(255,255,255,.04); }
    td:first-child { color: var(--accent); font-family: monospace; font-size: .84rem; }
    .method {
      display: inline-block;
      padding: .1rem .5rem;
      border-radius: 4px;
      font-size: .75rem;
      font-weight: 700;
    }
    .get    { background: rgba(0,208,132,.15); color: var(--green); }
    .post   { background: rgba(108,99,255,.2); color: #a89dff; }
    .put    { background: rgba(255,165,0,.15); color: #ffb347; }
    .delete { background: rgba(255,77,79,.15); color: var(--red); }
    footer { margin-top: 1.8rem; color: var(--sub); font-size: .78rem; text-align: center; }
  </style>
</head>
<body>
  <div class="card">
    <div class="logo">⛽ GasBook API</div>
    <div class="subtitle">LPG Booking Management System — Backend</div>

    <div class="badge {{ 'ok' if db_ok else 'err' }}">
      <span class="dot {{ 'ok' if db_ok else 'err' }}"></span>
      {{ 'MySQL Connected' if db_ok else 'MySQL Disconnected' }}
    </div>

    <table>
      <thead>
        <tr><th>Endpoint</th><th>Method</th><th>Description</th></tr>
      </thead>
      <tbody>
        <tr><td>/api/health</td><td><span class="method get">GET</span></td><td>Health check</td></tr>
        <tr><td>/api/login</td><td><span class="method post">POST</span></td><td>User login</td></tr>
        <tr><td>/api/logout</td><td><span class="method post">POST</span></td><td>User logout</td></tr>
        <tr><td>/api/customers</td><td><span class="method get">GET</span></td><td>List customers</td></tr>
        <tr><td>/api/customers</td><td><span class="method post">POST</span></td><td>Create customer</td></tr>
        <tr><td>/api/customers/&lt;id&gt;</td><td><span class="method put">PUT</span></td><td>Update customer</td></tr>
        <tr><td>/api/customers/&lt;id&gt;</td><td><span class="method delete">DELETE</span></td><td>Delete customer</td></tr>
        <tr><td>/api/bookings</td><td><span class="method get">GET</span></td><td>List bookings</td></tr>
        <tr><td>/api/bookings</td><td><span class="method post">POST</span></td><td>Create booking</td></tr>
        <tr><td>/api/bookings/&lt;id&gt;/status</td><td><span class="method put">PUT</span></td><td>Update status</td></tr>
        <tr><td>/api/bookings/&lt;id&gt;</td><td><span class="method delete">DELETE</span></td><td>Delete booking</td></tr>
        <tr><td>/api/inventory</td><td><span class="method get">GET</span></td><td>Inventory list</td></tr>
        <tr><td>/api/inventory/restock</td><td><span class="method post">POST</span></td><td>Restock inventory</td></tr>
        <tr><td>/api/warehouses</td><td><span class="method get">GET</span></td><td>List warehouses</td></tr>
        <tr><td>/api/deliveryboys</td><td><span class="method get">GET</span></td><td>List delivery boys</td></tr>
        <tr><td>/api/analytics/dashboard</td><td><span class="method get">GET</span></td><td>Dashboard metrics</td></tr>
        <tr><td>/api/cylinder-types</td><td><span class="method get">GET</span></td><td>Cylinder types</td></tr>
      </tbody>
    </table>

    <footer>GasBook v2 &bull; Running on port {{ port }} &bull; {{ now }}</footer>
  </div>
</body>
</html>"""


# ── Serve HTML Pages ──────────────────────────────────────────────────────────
_HTML_DIR = os.path.dirname(os.path.abspath(__file__))

@app.route('/', methods=['GET'])
def index():
    """Serve the GasBook login page"""
    return send_from_directory(_HTML_DIR, 'src/index.html')

@app.route('/dashboard', methods=['GET'])
def dashboard_page():
    """Serve the GasBook dashboard page"""
    return send_from_directory(_HTML_DIR, 'src/dashboard.html')

@app.route('/status', methods=['GET'])
def status_page():
    """API status overview page (moved from /)"""
    conn = get_db()
    db_ok = conn is not None
    if conn:
        conn.close()
    return render_template_string(
        STATUS_PAGE,
        db_ok=db_ok,
        port=app.config.get('FLASK_PORT', 5002),
        now=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    )



# ── DB connection ─────────────────────────────────────────────────────────────
def get_db():
    try:
        conn = mysql.connector.connect(
            host=app.config['MYSQL_HOST'],
            user=app.config['MYSQL_USER'],
            password=app.config['MYSQL_PASSWORD'],
            database=app.config['MYSQL_DATABASE'],
            port=app.config['MYSQL_PORT'],
            autocommit=False,
            connection_timeout=10,
            auth_plugin='caching_sha2_password'
        )
        return conn
    except Error as e:
        logger.error(f"DB connection failed: {e}")
        return None

def db_error(msg='Database connection failed'):
    return jsonify({'success': False, 'message': msg}), 500


def ensure_member_role():
    """Patch live DB: add 'member' to users.role ENUM and customer_id if missing."""
    conn = get_db()
    if not conn:
        return
    try:
        cur = conn.cursor()
        cur.execute("""
            ALTER TABLE users
            MODIFY COLUMN role ENUM('admin','staff','member') NOT NULL DEFAULT 'staff'
        """)
        conn.commit()
    except Exception:
        pass  # already has the value — safe to ignore
        
    try:
        cur.execute("ALTER TABLE users ADD COLUMN customer_id VARCHAR(20) DEFAULT NULL")
        cur.execute("UPDATE users u JOIN customers c ON c.email = u.username SET u.customer_id = c.customer_id WHERE u.customer_id IS NULL")
        conn.commit()
    except Exception:
        pass
        
    finally:
        if 'cur' in locals(): cur.close()
        conn.close()

# ── Health ────────────────────────────────────────────────────────────────────
@app.route('/api/health', methods=['GET'])
def health():
    conn = get_db()
    if conn:
        conn.close()
        return jsonify({'success': True, 'status': 'healthy', 'db': 'connected'})
    return jsonify({'success': False, 'status': 'unhealthy', 'db': 'disconnected'}), 500

# ── AUTH ──────────────────────────────────────────────────────────────────────
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json(force=True, silent=True) or {}
    username = (data.get('username') or '').strip()
    password = (data.get('password') or '').strip()

    if not username or not password:
        return jsonify({'success': False, 'message': 'Username and password are required'}), 400

    conn = get_db()
    if not conn:
        return db_error()

    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(
            'SELECT users.user_id, users.username, users.role, customers.email AS c_email, COALESCE(users.customer_id, customers.customer_id) AS c_id FROM users '
            'LEFT JOIN customers ON customers.customer_id = users.customer_id OR customers.email = %s OR customers.email = users.username '
            'WHERE (users.username=%s OR customers.email=%s) AND users.password=%s AND users.status="active" LIMIT 1',
            (username, username, username, password)
        )
        user = cur.fetchone()
        cur.close()
        conn.close()

        if user:
            session['user_id']  = user['user_id']
            session['username'] = user['username']
            session['role']     = user['role']
            session['c_email']  = user['c_email']
            session['c_id']     = user['c_id']
            return jsonify({
                'success':  True,
                'user_id':  user['user_id'],
                'username': user['username'],
                'c_id':     user['c_id'],
                'role':     user['role'],
                'message':  'Login successful'
            })

        return jsonify({'success': False, 'message': 'Invalid username or password'}), 401

    except Error as e:
        conn.close()
        logger.error(f"Login error: {e}")
        return db_error(str(e))

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out'})

@app.route('/api/register', methods=['POST'])
def register():
    data      = request.get_json(force=True, silent=True) or {}
    username  = (data.get('username') or '').strip()
    password  = (data.get('password') or '').strip()
    email     = (data.get('email')    or '').strip()
    full_name = (data.get('full_name') or email.split('@')[0]).strip()

    # ── Validate ──────────────────────────────────────────────────
    if not email or not password:
        return jsonify({'success': False, 'message': 'Email and password are required'}), 400
    if len(password) < 8:
        return jsonify({'success': False, 'message': 'Password must be at least 8 characters'}), 400
    if not username:
        username = email   # use email as username if not supplied

    conn = get_db()
    if not conn: return db_error()
    try:
        cur = conn.cursor(dictionary=True)

        # ── Check for duplicate username / email ──────────────────
        cur.execute('SELECT user_id FROM users WHERE username=%s', (username,))
        if cur.fetchone():
            cur.close(); conn.close()
            return jsonify({'success': False, 'message': 'An account with this email already exists'}), 409

        # ── Create user (role = member) ───────────────────────────
        cur.execute(
            'INSERT INTO users (username, password, role, status) VALUES (%s, %s, %s, %s)',
            (username, password, 'member', 'active')
        )
        user_id = cur.lastrowid

        # ── Generate unique customer_id (CUST0001 format) ─────────
        cur.execute('SELECT COUNT(*) AS c FROM customers')
        count = cur.fetchone()['c'] + 1
        cid   = f'CUST{count:04d}'
        cur.execute('SELECT customer_id FROM customers WHERE customer_id=%s', (cid,))
        while cur.fetchone():
            count += 1
            cid = f'CUST{count:04d}'
            cur.execute('SELECT customer_id FROM customers WHERE customer_id=%s', (cid,))

        import uuid
        dummy_phone = f"00{uuid.uuid4().hex[:8]}"

        # ── Create linked customer record ─────────────────────────
        cur.execute(
            'INSERT INTO customers (customer_id, name, phone, email, status) VALUES (%s, %s, %s, %s, %s)',
            (cid, full_name, dummy_phone, email, 'active')
        )
        
        # ── Update user's customer_id ─────────────────────────────
        cur.execute('UPDATE users SET customer_id=%s WHERE user_id=%s', (cid, user_id))

        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'success': True, 'message': 'Account created! You can now sign in.', 'user_id': user_id}), 201

    except IntegrityError as e:
        conn.rollback(); conn.close()
        logger.error(f'Register conflict: {e}')
        return jsonify({'success': False, 'message': f'Account constraint issue: {e}'}), 409
    except Error as e:
        conn.rollback(); conn.close()
        logger.error(f'Register error: {e}')
        return db_error(str(e))

# ── CUSTOMERS ─────────────────────────────────────────────────────────────────
@app.route('/api/customers', methods=['GET'])
def get_customers():
    conn = get_db()
    if not conn: return db_error()
    try:
        cur   = conn.cursor(dictionary=True)
        page  = request.args.get('page',  1,   type=int)
        limit = request.args.get('limit', 10,  type=int)
        q     = request.args.get('q',     '',  type=str).strip()
        offset = (page - 1) * limit

        role  = session.get('role', 'member')
        c_id  = session.get('c_id')
        c_em  = session.get('c_email')
        
        # Base query logic: if Member, restrict to ONLY their customer_id or email
        where_clause = ""
        params = []
        
        if role == 'member':
            where_clause = "WHERE customer_id = %s OR email = %s "
            params.extend([c_id, c_em])
        elif q:
            like = f'%{q}%'
            where_clause = "WHERE name LIKE %s OR phone LIKE %s OR customer_id LIKE %s "
            params.extend([like, like, like])

        count_sql = "SELECT COUNT(*) as c FROM customers " + where_clause
        cur.execute(count_sql, tuple(params))
        total = cur.fetchone()['c']

        data_sql = "SELECT * FROM customers " + where_clause + "ORDER BY member_since DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        cur.execute(data_sql, tuple(params))
        rows = cur.fetchall()

        cur.close(); conn.close()
        return jsonify({'success': True, 'data': rows, 'total': total, 'page': page, 'limit': limit})
    except Error as e:
        conn.close(); return db_error(str(e))

@app.route('/api/customers', methods=['POST'])
def create_customer():
    data = request.get_json(force=True, silent=True) or {}
    if not data.get('name') or not data.get('phone'):
        return jsonify({'success': False, 'message': 'Name and phone are required'}), 400

    conn = get_db()
    if not conn: return db_error()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute('SELECT COUNT(*) as c FROM customers')
        count = cur.fetchone()['c'] + 1
        cid   = f'CUST{count:04d}'
        cur.execute('SELECT customer_id FROM customers WHERE customer_id=%s', (cid,))
        while cur.fetchone():
            count += 1
            cid = f'CUST{count:04d}'

        cur.execute(
            'INSERT INTO customers (customer_id,name,phone,email,address,aadhar_no) VALUES (%s,%s,%s,%s,%s,%s)',
            (cid, data['name'], data['phone'], data.get('email',''), data.get('address',''), data.get('aadhar_no',''))
        )
        conn.commit(); cur.close(); conn.close()
        return jsonify({'success': True, 'message': 'Customer registered', 'customer_id': cid}), 201
    except IntegrityError:
        conn.close()
        return jsonify({'success': False, 'message': 'Phone number already registered'}), 409
    except Error as e:
        conn.close(); return db_error(str(e))

@app.route('/api/customers/<customer_id>', methods=['GET'])
def get_customer(customer_id):
    conn = get_db()
    if not conn: return db_error()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute('SELECT * FROM customers WHERE customer_id=%s', (customer_id,))
        row = cur.fetchone()
        cur.close(); conn.close()
        if not row:
            return jsonify({'success': False, 'message': 'Customer not found'}), 404
        return jsonify({'success': True, 'data': row})
    except Error as e:
        conn.close(); return db_error(str(e))

@app.route('/api/customers/<customer_id>', methods=['PUT'])
def update_customer(customer_id):
    if session.get('role') == 'member' and session.get('c_id') != customer_id:
        return jsonify({'success': False, 'message': 'Forbidden'}), 403
        
    data = request.get_json(force=True, silent=True) or {}
    conn = get_db()
    if not conn: return db_error()
    try:
        cur = conn.cursor()
        cur.execute(
            'UPDATE customers SET name=%s, phone=%s, email=%s, address=%s, aadhar_no=%s WHERE customer_id=%s',
            (data.get('name'), data.get('phone'), data.get('email'), data.get('address'), data.get('aadhar_no'), customer_id)
        )
        conn.commit(); cur.close(); conn.close()
        return jsonify({'success': True, 'message': 'Customer updated'})
    except Error as e:
        conn.close(); return db_error(str(e))

@app.route('/api/customers/<customer_id>', methods=['DELETE'])
def delete_customer(customer_id):
    conn = get_db()
    if not conn: return db_error()
    try:
        cur = conn.cursor()
        cur.execute('DELETE FROM customers WHERE customer_id=%s', (customer_id,))
        conn.commit(); cur.close(); conn.close()
        return jsonify({'success': True, 'message': 'Customer deleted'})
    except Error as e:
        conn.close(); return db_error(str(e))

# ── CYLINDER TYPES ────────────────────────────────────────────────────────────
@app.route('/api/cylinder-types', methods=['GET'])
def get_cylinder_types():
    conn = get_db()
    if not conn: return db_error()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute('SELECT * FROM cylindertypes WHERE is_active=1 ORDER BY type_id')
        rows = cur.fetchall()
        cur.close(); conn.close()
        return jsonify({'success': True, 'data': rows})
    except Error as e:
        conn.close(); return db_error(str(e))

# ── BOOKINGS ──────────────────────────────────────────────────────────────────
@app.route('/api/bookings', methods=['GET'])
def get_bookings():
    conn = get_db()
    if not conn: return db_error()
    try:
        cur    = conn.cursor(dictionary=True)
        page   = request.args.get('page',   1,  type=int)
        limit  = request.args.get('limit',  10, type=int)
        status = request.args.get('status', '', type=str).strip()
        offset = (page - 1) * limit

        role = session.get('role', 'member')
        c_id = session.get('c_id')

        base_sql = '''
            SELECT b.*, c.name AS customer_name, c.phone AS customer_phone,
                   c.address AS customer_address,
                   ct.type_name, ct.price AS unit_price, ct.weight,
                   db.name AS delivery_boy_name
            FROM   bookings b
            JOIN   customers    c  ON b.customer_id = c.customer_id
            JOIN   cylindertypes ct ON b.type_id     = ct.type_id
            LEFT JOIN deliveryboys db ON b.delivery_boy_id = db.boy_id
        '''
        
        conds = []
        params = []
        if status:
            conds.append("b.status=%s")
            params.append(status)
        if role == 'member':
            conds.append("b.customer_id=%s")
            params.append(c_id)
            
        where_clause = " WHERE " + " AND ".join(conds) if conds else ""
        
        cur.execute(base_sql + where_clause + ' ORDER BY b.booking_date DESC LIMIT %s OFFSET %s', tuple(params + [limit, offset]))
        rows = cur.fetchall()

        for r in rows:
            for k, v in r.items():
                if isinstance(v, datetime):
                    r[k] = v.strftime('%Y-%m-%d %H:%M:%S')

        count_sql = 'SELECT COUNT(*) as c FROM bookings b' + where_clause
        cur.execute(count_sql, tuple(params))
        total = cur.fetchone()['c']
        cur.close(); conn.close()
        return jsonify({'success': True, 'data': rows, 'total': total, 'page': page, 'limit': limit})
    except Error as e:
        conn.close(); return db_error(str(e))

@app.route('/api/bookings', methods=['POST'])
def create_booking():
    data = request.get_json(force=True, silent=True) or {}
    
    if session.get('role') == 'member':
        c_id = session.get('c_id')
        if not c_id:
            # Self-heal if active session lacks c_id due to old cookie
            conn = get_db()
            if conn:
                try:
                    cur = conn.cursor(dictionary=True)
                    cur.execute(
                        "SELECT customer_id FROM customers WHERE email = %s OR customer_id = (SELECT customer_id FROM users WHERE username = %s) LIMIT 1", 
                        (session.get('c_email') or session.get('username'), session.get('username'))
                    )
                    row = cur.fetchone()
                    if row:
                        c_id = row['customer_id']
                        session['c_id'] = c_id
                    cur.close()
                except Exception as e:
                    logger.error(f"Failed to auto-recover c_id: {e}")
                finally:
                    conn.close()
        
        if c_id:
            data['customer_id'] = c_id
        elif not data.get('customer_id'):
            data['customer_id'] = None # Fallback

    if not data.get('customer_id') or not data.get('type_id'):
        return jsonify({'success': False, 'message': 'customer_id and type_id are required (Profile might be unlinked)'}), 400

    conn = get_db()
    if not conn: return db_error()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute('SELECT price FROM cylindertypes WHERE type_id=%s AND is_active=1', (data['type_id'],))
        ct = cur.fetchone()
        if not ct:
            cur.close(); conn.close()
            return jsonify({'success': False, 'message': 'Invalid cylinder type'}), 400

        qty    = int(data.get('quantity', 1))
        amount = float(ct['price']) * qty

        cur.execute('SELECT COUNT(*) as c FROM bookings')
        count = cur.fetchone()['c'] + 1
        bid   = f"BK{datetime.now().strftime('%Y%m')}{count:04d}"

        cur.execute('''
            INSERT INTO bookings (booking_id,customer_id,type_id,quantity,booking_date,delivery_date,amount,delivery_boy_id)
            VALUES (%s,%s,%s,%s,NOW(),%s,%s,%s)
        ''', (bid, data['customer_id'], data['type_id'], qty,
              data.get('delivery_date') or None,
              amount,
              data.get('delivery_boy_id') or None))

        cur.execute(
            'UPDATE customers SET total_bookings=total_bookings+1, total_spent=total_spent+%s WHERE customer_id=%s',
            (amount, data['customer_id'])
        )
        conn.commit(); cur.close(); conn.close()
        return jsonify({'success': True, 'message': 'Booking created', 'booking_id': bid, 'amount': amount}), 201

    except Error as e:
        conn.rollback(); conn.close(); return db_error(str(e))

@app.route('/api/bookings/<booking_id>/status', methods=['PUT'])
def update_booking_status(booking_id):
    data   = request.get_json(force=True, silent=True) or {}
    status = data.get('status')
    valid  = ('pending','confirmed','out_for_delivery','delivered','cancelled')
    
    role = session.get('role', 'member')
    if role == 'member' and status != 'cancelled':
        return jsonify({'success': False, 'message': 'Members can only cancel bookings.'}), 403
        
    if status not in valid:
        return jsonify({'success': False, 'message': f'status must be one of {valid}'}), 400

    conn = get_db()
    if not conn: return db_error()
    try:
        cur = conn.cursor()
        if status == 'delivered':
            cur.execute(
                'UPDATE bookings SET status=%s, delivery_date=CURDATE() WHERE booking_id=%s',
                (status, booking_id)
            )
        else:
            cur.execute('UPDATE bookings SET status=%s WHERE booking_id=%s', (status, booking_id))
        conn.commit(); cur.close(); conn.close()
        return jsonify({'success': True, 'message': 'Status updated'})
    except Error as e:
        conn.close(); return db_error(str(e))

@app.route('/api/bookings/<booking_id>', methods=['DELETE'])
def delete_booking(booking_id):
    if session.get('role') == 'member':
        return jsonify({'success': False, 'message': 'Members cannot delete bookings'}), 403

    conn = get_db()
    if not conn: return db_error()
    try:
        cur = conn.cursor()
        cur.execute('DELETE FROM bookings WHERE booking_id=%s', (booking_id,))
        conn.commit(); cur.close(); conn.close()
        return jsonify({'success': True, 'message': 'Booking deleted'})
    except Error as e:
        conn.close(); return db_error(str(e))

# ── INVENTORY ─────────────────────────────────────────────────────────────────
@app.route('/api/inventory', methods=['GET'])
def get_inventory():
    conn = get_db()
    if not conn: return db_error()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute('''
            SELECT i.*, ct.type_name, ct.weight, ct.price,
                   w.name AS warehouse_name, w.location
            FROM   inventory i
            JOIN   cylindertypes ct ON i.type_id      = ct.type_id
            JOIN   warehouses    w  ON i.warehouse_id = w.warehouse_id
            ORDER  BY w.name, ct.type_name
        ''')
        rows = cur.fetchall()
        cur.close(); conn.close()
        return jsonify({'success': True, 'data': rows})
    except Error as e:
        conn.close(); return db_error(str(e))

@app.route('/api/inventory/restock', methods=['POST'])
def restock():
    data = request.get_json(force=True, silent=True) or {}
    if not data.get('type_id') or not data.get('warehouse_id') or not data.get('quantity'):
        return jsonify({'success': False, 'message': 'type_id, warehouse_id and quantity required'}), 400

    conn = get_db()
    if not conn: return db_error()
    try:
        cur = conn.cursor()
        cur.execute('''
            UPDATE inventory
            SET    quantity_on_hand = quantity_on_hand + %s,
                   last_restocked   = NOW()
            WHERE  type_id=%s AND warehouse_id=%s
        ''', (int(data['quantity']), data['type_id'], data['warehouse_id']))
        conn.commit(); cur.close(); conn.close()
        return jsonify({'success': True, 'message': 'Inventory restocked'})
    except Error as e:
        conn.close(); return db_error(str(e))

# ── WAREHOUSES ────────────────────────────────────────────────────────────────
@app.route('/api/warehouses', methods=['GET'])
def get_warehouses():
    conn = get_db()
    if not conn: return db_error()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute('SELECT * FROM warehouses ORDER BY name')
        rows = cur.fetchall()
        cur.close(); conn.close()
        return jsonify({'success': True, 'data': rows})
    except Error as e:
        conn.close(); return db_error(str(e))

# ── DELIVERY BOYS ─────────────────────────────────────────────────────────────
@app.route('/api/deliveryboys', methods=['GET'])
def get_delivery_boys():
    conn = get_db()
    if not conn: return db_error()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM deliveryboys WHERE status='active' ORDER BY name")
        rows = cur.fetchall()
        cur.close(); conn.close()
        return jsonify({'success': True, 'data': rows})
    except Error as e:
        conn.close(); return db_error(str(e))

# ── ANALYTICS / DASHBOARD ─────────────────────────────────────────────────────
@app.route('/api/analytics/dashboard', methods=['GET'])
def dashboard_metrics():
    conn = get_db()
    if not conn: return db_error()
    try:
        cur = conn.cursor(dictionary=True)

        cur.execute('SELECT COUNT(*) as c FROM bookings')
        total_bookings = cur.fetchone()['c']

        cur.execute('SELECT COUNT(*) as c FROM customers WHERE status="active"')
        total_customers = cur.fetchone()['c']

        cur.execute('SELECT COALESCE(SUM(amount),0) as s FROM bookings WHERE status="delivered"')
        total_revenue = float(cur.fetchone()['s'])

        cur.execute('SELECT COUNT(*) as c FROM bookings WHERE status="pending"')
        pending = cur.fetchone()['c']

        cur.execute('SELECT COUNT(*) as c FROM bookings WHERE status="confirmed" OR status="out_for_delivery"')
        confirmed = cur.fetchone()['c']

        cur.execute('''
            SELECT b.booking_id, c.name as customer_name, ct.type_name,
                   b.amount, b.status, b.booking_date
            FROM   bookings b
            JOIN   customers c ON b.customer_id=c.customer_id
            JOIN   cylindertypes ct ON b.type_id=ct.type_id
            ORDER  BY b.booking_date DESC LIMIT 5
        ''')
        recent = cur.fetchall()
        for r in recent:
            if isinstance(r.get('booking_date'), datetime):
                r['booking_date'] = r['booking_date'].strftime('%Y-%m-%d')

        cur.execute('''
            SELECT DATE_FORMAT(booking_date,'%Y-%m') as month,
                   COUNT(*) as bookings,
                   COALESCE(SUM(amount),0) as revenue
            FROM   bookings
            WHERE  booking_date >= DATE_SUB(NOW(), INTERVAL 6 MONTH)
            GROUP  BY DATE_FORMAT(booking_date,'%Y-%m')
            ORDER  BY month ASC
        ''')
        monthly = cur.fetchall()

        cur.close(); conn.close()
        return jsonify({
            'success':         True,
            'total_bookings':  total_bookings,
            'total_customers': total_customers,
            'total_revenue':   round(total_revenue, 2),
            'pending':         pending,
            'confirmed':       confirmed,
            'recent_bookings': recent,
            'monthly':         monthly,
        })
    except Error as e:
        conn.close(); return db_error(str(e))


# ── Automatic Table Creation ──────────────────────────────────────────────────
def initialize_database():
    conn = get_db()
    if not conn:
        logger.error("Could not connect to DB for initialization.")
        return
    try:
        cur = conn.cursor()
        cur.execute("SHOW TABLES LIKE 'users'")
        if not cur.fetchone():
            logger.info("Tables are missing! Running init.sql automatically...")
            init_file = os.path.join(_BASE_DIR, 'src', 'init.sql')
            if os.path.exists(init_file):
                with open(init_file, 'r', encoding='utf-8') as f:
                    sql_script = f.read()
                
                # Simple parser for SQL script (avoids breaking on semi-colons inside strings)
                statements = [s.strip() + ';' for s in sql_script.split(';') if s.strip()]
                for statement in statements:
                    try:
                        cur.execute(statement)
                    except Error as e:
                        if 'already exists' not in str(e).lower() and 'duplicate entry' not in str(e).lower():
                            logger.error(f"Failed to execute init query: {e}")
                conn.commit()
                logger.info("Database initialized successfully from src/init.sql")
            else:
                logger.error(f"init.sql not found at {init_file}")
        cur.close()
        conn.close()
    except Exception as e:
        logger.error(f"Initialization error: {e}")

# ── Entry Point ───────────────────────────────────────────────────────────────
if __name__ == '__main__':
    port = app.config.get('FLASK_PORT', 5002)
    logger.info("=" * 55)
    logger.info(f"  GasBook Backend  |  http://localhost:{port}")
    logger.info(f"  DB: {app.config['MYSQL_HOST']}:{app.config['MYSQL_PORT']}/{app.config['MYSQL_DATABASE']}")
    logger.info("  Login: admin / admin123  OR  staff / staff123")
    logger.info("=" * 55)
    
    # Run automatic setup
    initialize_database()
    ensure_member_role()   # patch ENUM to include 'member'
    
    app.run(debug=app.config.get('DEBUG', False), host='0.0.0.0', port=port)
