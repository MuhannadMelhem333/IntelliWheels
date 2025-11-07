"""
IntelliWheels Backend API
Modern REST API for car catalog management with AI chatbot integration
"""
import sqlite3
import json
import os
import re
import hashlib
import secrets
import time
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("⚠️ Warning: requests not installed. Install with: pip install requests")

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

# Database configuration
DB_PATH = 'intelliwheels.db'

# In-memory conversation store per session
CHAT_SESSIONS = {}

# In-memory session store for authentication
AUTH_SESSIONS = {}  # {token: {user_id, username, created_at}}

# Initialize database
def init_db():
    """Initialize SQLite database with schema"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Main cars table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cars (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            make TEXT NOT NULL,
            model TEXT NOT NULL,
            year INTEGER,
            price REAL,
            currency TEXT DEFAULT 'AED',
            image_url TEXT,
            image_urls TEXT,
            rating REAL DEFAULT 0.0,
            reviews INTEGER DEFAULT 0,
            specs TEXT,
            engines TEXT,
            statistics TEXT,
            source_sheets TEXT,
            latitude REAL,
            longitude REAL,
            user_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Add user_id column if it doesn't exist (migration)
    cursor.execute("PRAGMA table_info(cars)")
    columns = [column[1] for column in cursor.fetchall()]
    if 'user_id' not in columns:
        cursor.execute('ALTER TABLE cars ADD COLUMN user_id INTEGER')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_cars_user_id ON cars(user_id)')
        print("✅ Added user_id column to cars table")
    
    # Statistics table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS statistics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            car_id INTEGER,
            stat_name TEXT,
            stat_value TEXT,
            FOREIGN KEY (car_id) REFERENCES cars(id)
        )
    ''')
    
    # Favorites table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS favorites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            car_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(car_id, user_id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Users table for authentication
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
    ''')
    
    # User sessions table for persistent sessions
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token TEXT NOT NULL UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Chatbot ratings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chatbot_ratings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            message_id TEXT,
            rating INTEGER NOT NULL CHECK(rating >= 1 AND rating <= 5),
            feedback TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Analytics cache table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS analytics_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            analysis_type TEXT NOT NULL,
            data TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_user_sessions_token 
        ON user_sessions(token)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_user_sessions_user 
        ON user_sessions(user_id)
    ''')
    
    conn.commit()
    conn.close()
    
    # Migrate favorites table if needed (add user_id column if missing)
    migrate_favorites_table()

def migrate_favorites_table():
    """Migrate favorites table to add user_id column if it doesn't exist"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if favorites table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='favorites'")
        if not cursor.fetchone():
            print("✅ Favorites table doesn't exist, will be created by init_db()")
            conn.close()
            return
        
        # Check if user_id column exists
        cursor.execute("PRAGMA table_info(favorites)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'user_id' not in columns:
            print("⚠️ Favorites table missing user_id column, migrating...")
            
            # Get existing data (if any)
            cursor.execute("SELECT car_id FROM favorites")
            existing_favorites = cursor.fetchall()
            
            # Drop old table
            cursor.execute("DROP TABLE IF EXISTS favorites")
            
            # Create new table with user_id
            cursor.execute('''
                CREATE TABLE favorites (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    car_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(car_id, user_id),
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')
            
            # Note: We can't restore old favorites without user_id, so they're lost
            # This is expected behavior for a migration
            if existing_favorites:
                print(f"⚠️ Note: {len(existing_favorites)} old favorites without user_id were removed during migration")
            
            conn.commit()
            print("✅ Favorites table migrated successfully")
        else:
            print("✅ Favorites table already has user_id column")
            
    except Exception as e:
        print(f"❌ Error migrating favorites table: {e}")
        conn.rollback()
    finally:
        conn.close()

# Database helper functions
def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def car_row_to_dict(row):
    """Convert database row to dictionary"""
    # Handle sqlite3.Row which doesn't have .get() method
    def get_value(key, default=None):
        try:
            return row[key] if key in row.keys() else default
        except (KeyError, TypeError):
            return default
    
    return {
        'id': row['id'],
        'make': row['make'],
        'model': row['model'],
        'year': row['year'],
        'price': row['price'],
        'currency': row['currency'],
        'image': row['image_url'],
        'imageUrls': json.loads(row['image_urls']) if row['image_urls'] else [],
        'rating': row['rating'] or 0.0,
        'reviews': row['reviews'] or 0,
        'specs': json.loads(row['specs']) if row['specs'] else {
            'bodyStyle': 'Unknown',
            'horsepower': 0,
            'engine': 'N/A',
            'fuelEconomy': 'N/A'
        },
        'engines': json.loads(row['engines']) if row['engines'] else [],
        'statistics': json.loads(row['statistics']) if row['statistics'] else {},
        'source_sheets': json.loads(row['source_sheets']) if row['source_sheets'] else [],
        'latitude': get_value('latitude'),
        'longitude': get_value('longitude')
    }

# Authentication helper functions
def hash_password(password):
    """Hash a password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, password_hash):
    """Verify a password against its hash"""
    return hash_password(password) == password_hash

def generate_token():
    """Generate a secure random token"""
    return secrets.token_urlsafe(32)

def get_user_from_token(token):
    """Get user info from token"""
    if not token:
        return None
    
    # Check in-memory sessions first
    if token in AUTH_SESSIONS:
        return AUTH_SESSIONS[token]
    
    # Check database sessions
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT u.id, u.username, u.email, us.token
        FROM users u
        INNER JOIN user_sessions us ON u.id = us.user_id
        WHERE us.token = ? AND (us.expires_at IS NULL OR us.expires_at > datetime('now'))
    ''', (token,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        user_info = {
            'user_id': row[0],
            'username': row[1],
            'email': row[2]
        }
        AUTH_SESSIONS[token] = user_info
        return user_info
    
    return None

def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None
        
        # Try Authorization header first
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header[7:]
        
        # Try query parameter
        if not token:
            token = request.args.get('token')
        
        # Try JSON body (but don't fail if it's empty)
        if not token:
            if request.is_json:
                data = request.get_json(silent=True)
                if data:
                    token = data.get('token')
        
        user = get_user_from_token(token)
        if not user:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        
        # Add user info to request context
        request.current_user = user
        return f(*args, **kwargs)
    return decorated_function

# Authentication API Routes

@app.route('/api/auth/signup', methods=['POST'])
def signup():
    """User registration endpoint"""
    try:
        # Check if request has JSON data
        if not request.is_json:
            return jsonify({'success': False, 'error': 'Request must be JSON'}), 400
        
        data = request.get_json(silent=True)
        if not data:
            return jsonify({'success': False, 'error': 'Invalid JSON data'}), 400
        
        username = data.get('username', '').strip()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        # Validation
        if not username or len(username) < 3:
            return jsonify({'success': False, 'error': 'Username must be at least 3 characters'}), 400
        
        if not email or '@' not in email:
            return jsonify({'success': False, 'error': 'Valid email is required'}), 400
        
        if not password or len(password) < 6:
            return jsonify({'success': False, 'error': 'Password must be at least 6 characters'}), 400
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Check if username or email already exists
        cursor.execute('SELECT id FROM users WHERE username = ? OR email = ?', (username, email))
        if cursor.fetchone():
            conn.close()
            return jsonify({'success': False, 'error': 'Username or email already exists'}), 400
        
        # Create user
        password_hash = hash_password(password)
        cursor.execute('''
            INSERT INTO users (username, email, password_hash)
            VALUES (?, ?, ?)
        ''', (username, email, password_hash))
        
        user_id = cursor.lastrowid
        
        # Create session token
        token = generate_token()
        cursor.execute('''
            INSERT INTO user_sessions (user_id, token, expires_at)
            VALUES (?, ?, datetime('now', '+30 days'))
        ''', (user_id, token))
        
        conn.commit()
        conn.close()
        
        # Store in memory
        AUTH_SESSIONS[token] = {
            'user_id': user_id,
            'username': username,
            'email': email
        }
        
        return jsonify({
            'success': True,
            'message': 'Account created successfully',
            'token': token,
            'user': {
                'id': user_id,
                'username': username,
                'email': email
            }
        }), 201
        
    except sqlite3.IntegrityError:
        return jsonify({'success': False, 'error': 'Username or email already exists'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    """User login endpoint"""
    try:
        # Check if request has JSON data
        if not request.is_json:
            return jsonify({'success': False, 'error': 'Request must be JSON'}), 400
        
        data = request.get_json(silent=True)
        if not data:
            return jsonify({'success': False, 'error': 'Invalid JSON data'}), 400
        
        username_or_email = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username_or_email or not password:
            return jsonify({'success': False, 'error': 'Username/email and password are required'}), 400
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Find user by username or email
        cursor.execute('''
            SELECT id, username, email, password_hash
            FROM users
            WHERE username = ? OR email = ?
        ''', (username_or_email, username_or_email.lower()))
        
        row = cursor.fetchone()
        if not row:
            conn.close()
            return jsonify({'success': False, 'error': 'Invalid credentials'}), 401
        
        user_id, username, email, password_hash = row
        
        # Verify password
        if not verify_password(password, password_hash):
            conn.close()
            return jsonify({'success': False, 'error': 'Invalid credentials'}), 401
        
        # Update last login
        cursor.execute('''
            UPDATE users SET last_login = datetime('now') WHERE id = ?
        ''', (user_id,))
        
        # Create new session token
        token = generate_token()
        cursor.execute('''
            INSERT INTO user_sessions (user_id, token, expires_at)
            VALUES (?, ?, datetime('now', '+30 days'))
        ''', (user_id, token))
        
        conn.commit()
        conn.close()
        
        # Store in memory
        AUTH_SESSIONS[token] = {
            'user_id': user_id,
            'username': username,
            'email': email
        }
        
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'token': token,
            'user': {
                'id': user_id,
                'username': username,
                'email': email
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    """User logout endpoint"""
    try:
        # Token can come from header, query param, or body
        token = None
        
        # Try Authorization header first
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header[7:]
        
        # Try query parameter
        if not token:
            token = request.args.get('token')
        
        # Try JSON body (but don't fail if it's empty)
        if not token:
            if request.is_json:
                data = request.get_json(silent=True)
                if data:
                    token = data.get('token')
        
        if token:
            # Remove from memory
            AUTH_SESSIONS.pop(token, None)
            
            # Remove from database
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('DELETE FROM user_sessions WHERE token = ?', (token,))
            conn.commit()
            conn.close()
        
        return jsonify({'success': True, 'message': 'Logged out successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/auth/verify', methods=['GET'])
def verify_session():
    """Verify if user session is valid"""
    try:
        token = request.headers.get('Authorization') or request.args.get('token')
        if token and token.startswith('Bearer '):
            token = token[7:]
        
        user = get_user_from_token(token)
        if user:
            return jsonify({
                'success': True,
                'authenticated': True,
                'user': {
                    'id': user['user_id'],
                    'username': user['username'],
                    'email': user['email']
                }
            })
        else:
            return jsonify({
                'success': True,
                'authenticated': False
            })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/profile', methods=['GET'])
@require_auth
def get_profile():
    """Get current user profile"""
    try:
        user_id = request.current_user['user_id']
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, username, email, created_at, last_login
            FROM users WHERE id = ?
        ''', (user_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        return jsonify({
            'success': True,
            'profile': {
                'id': row[0],
                'username': row[1],
                'email': row[2],
                'created_at': row[3],
                'last_login': row[4]
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/profile', methods=['PATCH'])
@require_auth
def update_profile():
    """Update user profile"""
    try:
        if not request.is_json:
            return jsonify({'success': False, 'error': 'Request must be JSON'}), 400
        
        data = request.get_json(silent=True)
        if not data:
            return jsonify({'success': False, 'error': 'Invalid JSON data'}), 400
        
        user_id = request.current_user['user_id']
        conn = get_db()
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute('SELECT id, username, email FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        if not user:
            conn.close()
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        updates = []
        params = []
        
        # Update username
        if 'username' in data:
            new_username = data['username'].strip()
            if new_username and new_username != user[1]:
                # Check if username already exists
                cursor.execute('SELECT id FROM users WHERE username = ? AND id != ?', (new_username, user_id))
                if cursor.fetchone():
                    conn.close()
                    return jsonify({'success': False, 'error': 'Username already taken'}), 400
                updates.append('username = ?')
                params.append(new_username)
        
        # Update email
        if 'email' in data:
            new_email = data['email'].strip().lower()
            if new_email and new_email != user[2]:
                # Check if email already exists
                cursor.execute('SELECT id FROM users WHERE email = ? AND id != ?', (new_email, user_id))
                if cursor.fetchone():
                    conn.close()
                    return jsonify({'success': False, 'error': 'Email already taken'}), 400
                updates.append('email = ?')
                params.append(new_email)
        
        # Update password
        if 'password' in data and 'current_password' in data:
            current_password = data['current_password']
            new_password = data['password']
            
            # Verify current password
            cursor.execute('SELECT password_hash FROM users WHERE id = ?', (user_id,))
            row = cursor.fetchone()
            if not row or not verify_password(current_password, row[0]):
                conn.close()
                return jsonify({'success': False, 'error': 'Current password is incorrect'}), 400
            
            # Validate new password
            if len(new_password) < 6:
                conn.close()
                return jsonify({'success': False, 'error': 'Password must be at least 6 characters'}), 400
            
            password_hash = hash_password(new_password)
            updates.append('password_hash = ?')
            params.append(password_hash)
        
        if not updates:
            conn.close()
            return jsonify({'success': False, 'error': 'No valid fields to update'}), 400
        
        params.append(user_id)
        query = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, params)
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Profile updated successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# API Routes

@app.route('/api/cars', methods=['GET'])
@require_auth
def get_cars():
    """Get all cars with optional filtering and sorting"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Query parameters
        make = request.args.get('make')
        search = request.args.get('search')
        sort_by = request.args.get('sort', 'default')
        limit = request.args.get('limit', type=int)
        offset = request.args.get('offset', type=int, default=0)
        
        # Build query
        query = "SELECT * FROM cars WHERE 1=1"
        params = []
        
        if make and make != 'all':
            query += " AND make = ?"
            params.append(make)
        
        if search:
            query += " AND (make LIKE ? OR model LIKE ?)"
            params.extend([f'%{search}%', f'%{search}%'])
        
        # Sorting
        if sort_by == 'price-asc':
            query += " ORDER BY price ASC"
        elif sort_by == 'price-desc':
            query += " ORDER BY price DESC"
        elif sort_by == 'rating-desc':
            query += " ORDER BY rating DESC"
        else:
            query += " ORDER BY id DESC"
        
        if limit:
            query += " LIMIT ?"
            params.append(limit)
        
        if offset:
            query += " OFFSET ?"
            params.append(offset)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        cars = [car_row_to_dict(row) for row in rows]
        
        # Get total count
        count_query = "SELECT COUNT(*) FROM cars WHERE 1=1"
        count_params = []
        if make and make != 'all':
            count_query += " AND make = ?"
            count_params.append(make)
        if search:
            count_query += " AND (make LIKE ? OR model LIKE ?)"
            count_params.extend([f'%{search}%', f'%{search}%'])
        
        cursor.execute(count_query, count_params)
        total = cursor.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'success': True,
            'cars': cars,
            'total': total,
            'offset': offset
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/cars/<int:car_id>', methods=['GET'])
@require_auth
def get_car(car_id):
    """Get a single car by ID"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM cars WHERE id = ?", (car_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return jsonify({'success': True, 'car': car_row_to_dict(row)})
        else:
            return jsonify({'success': False, 'error': 'Car not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/cars', methods=['POST'])
@require_auth
def create_car():
    """Create a new car listing"""
    try:
        # Check if request has JSON data
        if not request.is_json:
            return jsonify({'success': False, 'error': 'Request must be JSON'}), 400
        
        data = request.get_json(silent=True)
        if not data:
            return jsonify({'success': False, 'error': 'Invalid JSON data'}), 400
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Validate required fields
        required_fields = ['make', 'model']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400
        
        # Get user_id from authenticated user
        user_id = request.current_user['user_id']
        
        # Insert car
        cursor.execute('''
            INSERT INTO cars (make, model, year, price, currency, image_url, image_urls, 
                           rating, reviews, specs, engines, statistics, source_sheets, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('make'),
            data.get('model'),
            data.get('year'),
            data.get('price'),
            data.get('currency', 'AED'),
            data.get('image') or data.get('image_url'),
            json.dumps(data.get('imageUrls', [])),
            data.get('rating', 0.0),
            data.get('reviews', 0),
            json.dumps(data.get('specs', {})),
            json.dumps(data.get('engines', [])),
            json.dumps(data.get('statistics', {})),
            json.dumps(['Manual Entry']),
            user_id
        ))
        
        car_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Car created successfully',
            'car_id': car_id
        }), 201
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/cars/<int:car_id>', methods=['PATCH'])
@require_auth
def update_car(car_id):
    """Update an existing car"""
    try:
        # Check if request has JSON data
        if not request.is_json:
            return jsonify({'success': False, 'error': 'Request must be JSON'}), 400
        
        data = request.get_json(silent=True)
        if not data:
            return jsonify({'success': False, 'error': 'Invalid JSON data'}), 400
        
        conn = get_db()
        cursor = conn.cursor()
        user_id = request.current_user['user_id']
        
        # Check if car exists and belongs to user
        cursor.execute("SELECT id, user_id FROM cars WHERE id = ?", (car_id,))
        car = cursor.fetchone()
        if not car:
            conn.close()
            return jsonify({'success': False, 'error': 'Car not found'}), 404
        
        # Check ownership (allow if user_id is None for backward compatibility or if it matches)
        if car[1] is not None and car[1] != user_id:
            conn.close()
            return jsonify({'success': False, 'error': 'You do not have permission to edit this listing'}), 403
        
        # Build update query dynamically
        updates = []
        params = []
        
        allowed_fields = ['make', 'model', 'year', 'price', 'currency', 'image_url', 
                         'image_urls', 'rating', 'reviews', 'specs', 'engines', 'statistics']
        
        for field in allowed_fields:
            if field in data:
                if field == 'image_urls':
                    updates.append('image_urls = ?')
                    params.append(json.dumps(data[field]))
                elif field in ['specs', 'engines', 'statistics']:
                    updates.append(f'{field} = ?')
                    params.append(json.dumps(data[field]))
                else:
                    updates.append(f'{field} = ?')
                    params.append(data[field])
        
        if not updates:
            conn.close()
            return jsonify({'success': False, 'error': 'No valid fields to update'}), 400
        
        updates.append('updated_at = ?')
        params.append(datetime.now().isoformat())
        params.append(car_id)
        
        query = f"UPDATE cars SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, params)
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Car updated successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/cars/<int:car_id>', methods=['DELETE'])
@require_auth
def delete_car(car_id):
    """Delete a car"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        user_id = request.current_user['user_id']
        
        # Check if car exists and belongs to user
        cursor.execute("SELECT id, user_id FROM cars WHERE id = ?", (car_id,))
        car = cursor.fetchone()
        if not car:
            conn.close()
            return jsonify({'success': False, 'error': 'Car not found'}), 404
        
        # Check ownership (allow if user_id is None for backward compatibility or if it matches)
        if car[1] is not None and car[1] != user_id:
            conn.close()
            return jsonify({'success': False, 'error': 'You do not have permission to delete this listing'}), 403
        
        # Delete related data
        cursor.execute("DELETE FROM favorites WHERE car_id = ?", (car_id,))
        cursor.execute("DELETE FROM statistics WHERE car_id = ?", (car_id,))
        
        # Delete car
        cursor.execute("DELETE FROM cars WHERE id = ?", (car_id,))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Car deleted successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/makes', methods=['GET'])
@require_auth
def get_makes():
    """Get all unique car makes"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT make FROM cars ORDER BY make")
        makes = [row[0] for row in cursor.fetchall()]
        conn.close()
        return jsonify({'success': True, 'makes': makes})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/my-listings', methods=['GET'])
@require_auth
def get_my_listings():
    """Get all listings created by the current user"""
    try:
        user_id = request.current_user['user_id']
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM cars 
            WHERE user_id = ?
            ORDER BY created_at DESC
        ''', (user_id,))
        
        rows = cursor.fetchall()
        cars = [car_row_to_dict(row) for row in rows]
        conn.close()
        
        return jsonify({
            'success': True,
            'cars': cars,
            'total': len(cars)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/favorites', methods=['GET'])
@require_auth
def get_favorites():
    """Get user's favorite cars"""
    try:
        user_id = request.current_user['user_id']
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT c.* FROM cars c
            INNER JOIN favorites f ON c.id = f.car_id
            WHERE f.user_id = ?
            ORDER BY f.created_at DESC
        ''', (user_id,))
        
        rows = cursor.fetchall()
        cars = [car_row_to_dict(row) for row in rows]
        conn.close()
        
        print(f"📋 Retrieved {len(cars)} favorites for user_id={user_id}")
        return jsonify({'success': True, 'cars': cars})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/favorites', methods=['POST'])
@require_auth
def add_favorite():
    """Add a car to favorites"""
    try:
        # Check if request has JSON data
        if not request.is_json:
            return jsonify({'success': False, 'error': 'Request must be JSON'}), 400
        
        data = request.get_json(silent=True)
        if not data:
            return jsonify({'success': False, 'error': 'Invalid JSON data'}), 400
        
        car_id = data.get('car_id')
        user_id = request.current_user['user_id']
        
        if not car_id:
            return jsonify({'success': False, 'error': 'car_id is required'}), 400
        
        conn = get_db()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO favorites (car_id, user_id)
                VALUES (?, ?)
            ''', (car_id, user_id))
            conn.commit()
            print(f"✅ Added favorite: user_id={user_id}, car_id={car_id}")
            conn.close()
            return jsonify({'success': True, 'message': 'Added to favorites'})
        except sqlite3.IntegrityError as e:
            conn.close()
            print(f"⚠️ Favorite already exists: user_id={user_id}, car_id={car_id}")
            return jsonify({'success': False, 'error': 'Already in favorites'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/favorites/<int:car_id>', methods=['DELETE'])
@require_auth
def remove_favorite(car_id):
    """Remove a car from favorites"""
    try:
        user_id = request.current_user['user_id']
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM favorites
            WHERE car_id = ? AND user_id = ?
        ''', (car_id, user_id))
        
        rows_deleted = cursor.rowcount
        conn.commit()
        print(f"✅ Removed favorite: user_id={user_id}, car_id={car_id}, rows_deleted={rows_deleted}")
        conn.close()
        
        return jsonify({'success': True, 'message': 'Removed from favorites'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def detect_user_intent(query):
    """Detect user intent from query"""
    query_lower = query.lower()
    
    # Buying intent
    buying_keywords = ['buy', 'purchase', 'looking for', 'want', 'need', 'interested in', 'shopping for', 'considering']
    if any(kw in query_lower for kw in buying_keywords):
        return 'buying'
    
    # Comparing intent
    comparing_keywords = ['compare', 'vs', 'versus', 'difference', 'better', 'which is', 'between']
    if any(kw in query_lower for kw in comparing_keywords):
        return 'comparing'
    
    # Negotiating intent
    negotiating_keywords = ['discount', 'deal', 'negotiate', 'best price', 'lower price', 'cheaper', 'offer', 'bargain']
    if any(kw in query_lower for kw in negotiating_keywords):
        return 'negotiating'
    
    # Price inquiry
    price_keywords = ['price', 'cost', 'how much', 'expensive', 'affordable', 'budget']
    if any(kw in query_lower for kw in price_keywords):
        return 'price_inquiry'
    
    # Feature inquiry
    feature_keywords = ['spec', 'feature', 'engine', 'horsepower', 'fuel', 'mileage', 'safety', 'rating']
    if any(kw in query_lower for kw in feature_keywords):
        return 'feature_inquiry'
    
    # Recommendation
    recommendation_keywords = ['recommend', 'suggest', 'best', 'good', 'top', 'popular']
    if any(kw in query_lower for kw in recommendation_keywords):
        return 'recommendation'
    
    return 'general'

def query_cars_intelligently(query, intent, detected_currency=None):
    """Intelligently query cars from database based on query and intent"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Extract tokens for search (filter out common words)
    common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'should', 'could', 'can', 'may', 'might', 'must', 'what', 'which', 'where', 'when', 'why', 'how', 'about', 'show', 'me', 'i', 'want', 'need', 'looking', 'for', 'find', 'get', 'buy', 'price', 'cost', 'compare', 'best', 'good', 'car', 'cars', 'vehicle', 'vehicles'}
    tokens = [t for t in re.findall(r"[A-Za-z\u0600-\u06FF0-9]+", query) if len(t) >= 2 and t.lower() not in common_words]
    
    # Extract price range if mentioned
    price_pattern = re.search(r'(\d+)\s*(?:k|thousand|million)?', query.lower())
    max_price = None
    if price_pattern:
        price_val = int(price_pattern.group(1))
        if 'k' in query.lower() or 'thousand' in query.lower():
            max_price = price_val * 1000
        elif 'million' in query.lower():
            max_price = price_val * 1000000
        else:
            max_price = price_val
    
    # Extract year if mentioned
    year_pattern = re.search(r'\b(19|20)\d{2}\b', query)
    year_filter = int(year_pattern.group(0)) if year_pattern else None
    
    # Build SQL query
    where_clauses = []
    params = []
    
    # Make/Model search
    if tokens:
        make_model_clauses = []
        for token in tokens[:8]:  # Limit tokens
            pattern = f"%{token}%"
            make_model_clauses.append("(make LIKE ? OR model LIKE ?)")
            params.extend([pattern, pattern])
        if make_model_clauses:
            where_clauses.append(f"({' OR '.join(make_model_clauses)})")
    
    # Year filter
    if year_filter:
        where_clauses.append("year = ?")
        params.append(year_filter)
    
    # Price filter
    if max_price:
        where_clauses.append("price <= ?")
        params.append(max_price)
    
    # Currency filter
    if detected_currency:
        where_clauses.append("currency = ?")
        params.append(detected_currency)
    
    # Build final query - if no specific filters, get diverse sample
    if where_clauses:
        where_sql = " AND ".join(where_clauses)
    else:
        # No specific filters, get diverse sample
        where_sql = "1=1"
    
    # Order by relevance
    if intent == 'price_inquiry' or intent == 'negotiating':
        order_by = "ORDER BY price ASC"
    elif intent == 'recommendation':
        order_by = "ORDER BY rating DESC, reviews DESC"
    else:
        order_by = "ORDER BY year DESC, rating DESC"
    
    sql = f"""
        SELECT id, make, model, year, price, currency, rating, reviews, specs, engines, statistics
        FROM cars 
        WHERE {where_sql}
        {order_by}
        LIMIT 30
    """
    
    try:
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        cars = []
        for row in rows:
            try:
                car = {
                    'id': row[0],
                    'make': row[1],
                    'model': row[2],
                    'year': row[3],
                    'price': row[4],
                    'currency': row[5],
                    'rating': row[6] or 0.0,
                    'reviews': row[7] or 0,
                    'specs': json.loads(row[8]) if row[8] else {},
                    'engines': json.loads(row[9]) if row[9] else [],
                    'statistics': json.loads(row[10]) if row[10] else {}
                }
                cars.append(car)
            except Exception as e:
                print(f"Error parsing car row: {e}")
                continue
        conn.close()
        return cars
    except Exception as e:
        print(f"Error querying cars: {e}")
        import traceback
        traceback.print_exc()
        conn.close()
        return []

@app.route('/api/chatbot', methods=['POST'])
@require_auth
def chatbot():
    """Enhanced AI Chatbot endpoint with negotiation capabilities and intelligent database querying"""
    if not REQUESTS_AVAILABLE:
        return jsonify({
            'success': False,
            'error': 'Requests library not installed. Please install it with: pip install requests'
        }), 500
    
    try:
        # Check if request has JSON data
        if not request.is_json:
            return jsonify({'success': False, 'error': 'Request must be JSON'}), 400
        
        data = request.get_json(silent=True)
        if not data:
            return jsonify({'success': False, 'error': 'Invalid JSON data'}), 400
        
        query = data.get('query', '')
        api_key = data.get('api_key') or os.getenv('GEMINI_API_KEY')
        history = data.get('history', [])  # Client-provided conversation history
        session_id = data.get('session') or request.args.get('session') or 'default'
        
        if not query:
            return jsonify({'success': False, 'error': 'Query is required'}), 400
        
        if not api_key or api_key.strip() == '':
            return jsonify({
                'success': False,
                'error': 'API key is missing. Please add your Gemini API key.'
            }), 400
        
        # Merge with server-side session history
        server_history = CHAT_SESSIONS.get(session_id, [])
        combined_history = server_history + history if history else server_history

        # Limit combined history to last 15 messages to maintain context
        if len(combined_history) > 15:
            combined_history = combined_history[-15:]
            print(f"⚠️ Conversation history truncated to last 15 messages for session {session_id}")
        
        # Detect Arabic to respond in user's language
        is_arabic = bool(re.search(r"[\u0600-\u06FF]", query))
        if not is_arabic and combined_history:
            for msg in combined_history[-3:]:
                if msg.get('text') and re.search(r"[\u0600-\u06FF]", msg.get('text', '')):
                    is_arabic = True
                    break

        # Detect region/country and currency
        region_currency_map = {
            'jordan': 'JOD', 'amman': 'JOD',
            'uae': 'AED', 'dubai': 'AED', 'abu dhabi': 'AED', 'united arab emirates': 'AED',
            'ksa': 'SAR', 'saudi': 'SAR', 'saudi arabia': 'SAR', 'riyadh': 'SAR', 'jeddah': 'SAR',
            'qatar': 'QAR', 'doha': 'QAR',
            'kuwait': 'KWD',
            'bahrain': 'BHD',
            'oman': 'OMR', 'muscat': 'OMR',
            'egypt': 'EGP', 'cairo': 'EGP',
            'morocco': 'MAD', 'casablanca': 'MAD', 'marrakesh': 'MAD',
            'lebanon': 'LBP', 'beirut': 'LBP',
            'iraq': 'IQD', 'baghdad': 'IQD',
            'palestine': 'ILS', 'west bank': 'ILS', 'gaza': 'ILS', 'jerusalem': 'ILS',
            'syria': 'SYP', 'damascus': 'SYP',
            'turkey': 'TRY', 'istanbul': 'TRY'
        }
        query_lower = query.lower()
        detected_region = None
        detected_currency = None
        for key, cur in region_currency_map.items():
            if key in query_lower:
                detected_region = key
                detected_currency = cur
                break

        # Detect user intent
        intent = detect_user_intent(query)
        print(f"🎯 Detected intent: {intent}")

        # Query cars intelligently based on intent and query
        relevant_cars = query_cars_intelligently(query, intent, detected_currency)
        print(f"🔍 Initial query returned {len(relevant_cars)} cars")
        
        # Always ensure we have cars to show - if no matches, get diverse sample
        conn = get_db()
        cursor = conn.cursor()

        # Check total cars in database
        cursor.execute("SELECT COUNT(*) FROM cars")
        total_cars = cursor.fetchone()[0]
        print(f"📊 Total cars in database: {total_cars}")
        
        if not relevant_cars or len(relevant_cars) < 10:
            # Get additional cars to ensure good coverage
            cursor.execute("""
                SELECT id, make, model, year, price, currency, rating, reviews, specs, engines, statistics
                FROM cars 
                ORDER BY RANDOM() 
                LIMIT 20
            """)
            rows = cursor.fetchall()
            existing_ids = {car['id'] for car in relevant_cars}
            for row in rows:
                car_id = row[0]
                if car_id not in existing_ids:
                    relevant_cars.append({
                        'id': car_id,
                        'make': row[1],
                        'model': row[2],
                        'year': row[3],
                        'price': row[4],
                        'currency': row[5],
                        'rating': row[6] or 0.0,
                        'reviews': row[7] or 0,
                        'specs': json.loads(row[8]) if row[8] else {},
                        'engines': json.loads(row[9]) if row[9] else [],
                        'statistics': json.loads(row[10]) if row[10] else {}
                    })
                    if len(relevant_cars) >= 30:
                        break
        
        # If still no cars, get any cars from database
        if not relevant_cars:
            cursor.execute("""
                SELECT id, make, model, year, price, currency, rating, reviews, specs, engines, statistics
                FROM cars 
                ORDER BY id DESC
                LIMIT 30
            """)
            rows = cursor.fetchall()
            for row in rows:
                relevant_cars.append({
                    'id': row[0],
                    'make': row[1],
                    'model': row[2],
                    'year': row[3],
                    'price': row[4],
                    'currency': row[5],
                    'rating': row[6] or 0.0,
                    'reviews': row[7] or 0,
                    'specs': json.loads(row[8]) if row[8] else {},
                    'engines': json.loads(row[9]) if row[9] else [],
                    'statistics': json.loads(row[10]) if row[10] else {}
                })

        conn.close()

        # Build comprehensive car context
        cars_context_parts = []
        for car in relevant_cars[:20]:  # Limit to 20 most relevant
            car_info = f"ID: {car['id']} | {car['make']} {car['model']} ({car['year']})"
            car_info += f" | Price: {car['price']} {car['currency']}"
            if car['rating'] > 0:
                car_info += f" | Rating: {car['rating']}/5.0 ({car['reviews']} reviews)"
            
            specs = car.get('specs', {})
            if specs:
                if specs.get('bodyStyle'):
                    car_info += f" | Body: {specs['bodyStyle']}"
                if specs.get('horsepower'):
                    car_info += f" | HP: {specs['horsepower']}"
                if specs.get('engine'):
                    car_info += f" | Engine: {specs['engine']}"
                if specs.get('fuelEconomy'):
                    car_info += f" | Fuel: {specs['fuelEconomy']}"
            
            cars_context_parts.append(car_info)
        
        cars_context = "\n".join(cars_context_parts) if cars_context_parts else "No cars found in database."
        print(f"📝 Sending {len(relevant_cars)} cars to AI (showing {len(cars_context_parts)} in context)")

        # Build enhanced system prompt with negotiation capabilities
        language_hint = "Arabic" if is_arabic else "English"
        region_hint = f"User's region: {detected_region} | Preferred currency: {detected_currency}\n" if detected_region else ""
        
        system_instruction = f"""You are IntelliWheels' premium AI automotive assistant and negotiation expert. Your role is to help users find the perfect car, negotiate deals, compare options, and answer all automotive questions.

CAPABILITIES:
1. CAR RECOMMENDATIONS: Suggest cars from the catalog based on user needs, budget, and preferences
2. PRICE NEGOTIATION: Help negotiate prices, suggest discounts, find best deals, and compare prices across similar models
3. COMPARISONS: Compare multiple cars side-by-side on specs, price, ratings, and features
4. DETAILED INFORMATION: Provide comprehensive information about any car including specs, engines, ratings, and statistics
5. DEAL MAKING: Help structure deals, suggest financing options, and find the best value propositions

NEGOTIATION STRATEGY:
- When users ask about prices or discounts, suggest reasonable negotiation ranges (typically 5-15% off listed price)
- Compare prices with similar models to show value
- Highlight features that justify the price
- Suggest alternative models if budget is a concern
- Be helpful and realistic about market prices

RESPONSE GUIDELINES:
- Always prioritize catalog data when available (use exact prices, specs, and ratings from the catalog)
- If catalog data doesn't match, use general automotive knowledge but clearly state it's an estimate
- When recommending cars, mention the car ID so users can view details (e.g., "Car ID: 123")
- Be conversational, friendly, and professional
- For negotiations, be helpful and suggest realistic deals
- Answer in {language_hint}
{region_hint}
- If user asks about a specific car, provide detailed information from the catalog
- When comparing, highlight key differences clearly
- Always be honest about limitations and uncertainties

CATALOG DATA (use this as your primary source):
{cars_context}

Remember: You have access to {len(relevant_cars)} cars in the catalog. Use this data to provide accurate, helpful responses. When users mention car IDs, reference those specific cars."""
        
        try:
            # Use Gemini REST API
            api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
            
            headers = {
                'Content-Type': 'application/json',
                'X-goog-api-key': api_key
            }
            
            # Build conversation contents with history
            contents = []
            
            # Convert history to Gemini format
            for msg in combined_history:
                role = "user" if msg.get('role') == 'user' else "model"
                contents.append({
                    "parts": [{"text": msg.get('text', '')}],
                    "role": role
                })
            
            # Add current user query
            contents.append({
                "parts": [{"text": query}],
                "role": "user"
            })
            
            # Build payload with enhanced configuration
            payload = {
                "contents": contents,
                "systemInstruction": {
                    "parts": [{"text": system_instruction}]
                },
                "generationConfig": {
                    "temperature": 0.7,  # Increased for more natural conversation
                    "topP": 0.9,
                    "topK": 40,
                    "maxOutputTokens": 2048  # Increased for detailed responses
                }
            }
            
            print(f"📝 Intent: {intent} | Found {len(relevant_cars)} relevant cars | History: {len(combined_history)} messages")
            print(f"📝 Query: {query[:80]}...")
            
            response = requests.post(api_url, headers=headers, json=payload, timeout=45)
            
            print(f"📥 Response status: {response.status_code}")
            
            if response.status_code != 200:
                error_data = response.json() if response.text else {}
                error_msg = error_data.get('error', {}).get('message', f'HTTP {response.status_code}: {response.text}')
                print(f"❌ Gemini API Error: {error_msg}")
                
                if response.status_code == 401 or response.status_code == 403:
                    error_msg = "Invalid API key. Please check your Gemini API key."
                elif response.status_code == 429:
                    error_msg = "API quota exceeded. Please try again later."
                elif 'safety' in error_msg.lower() or 'blocked' in error_msg.lower():
                    error_msg = "The query was blocked by safety filters. Please rephrase your question."
                
                return jsonify({
                    'success': False,
                    'error': f'Chatbot Error: {error_msg}'
                }), 500
            
            response_data = response.json()
            print(f"✅ Received response from Gemini")
            
            # Extract text from response
            response_text = None
            
            if 'candidates' in response_data and len(response_data['candidates']) > 0:
                candidate = response_data['candidates'][0]
                
                if 'finishReason' in candidate:
                    finish_reason = candidate['finishReason']
                    if finish_reason == 'SAFETY':
                        return jsonify({
                            'success': False,
                            'error': 'Chatbot Error: Response was blocked by safety filters. Please rephrase your question.'
                        }), 500
                    elif finish_reason == 'MAX_TOKENS':
                        print("⚠️ Response hit max tokens limit")
                
                if 'content' in candidate and 'parts' in candidate['content']:
                    for part in candidate['content']['parts']:
                        if 'text' in part:
                            response_text = part['text']
                            break
            
            if 'promptFeedback' in response_data:
                if 'blockReason' in response_data['promptFeedback']:
                    return jsonify({
                        'success': False,
                        'error': f"Chatbot Error: Query was blocked: {response_data['promptFeedback']['blockReason']}"
                    }), 500
            
            if not response_text or response_text.strip() == "":
                response_text = "I'm sorry, I received an empty response. Please try asking your question differently."
            
            print(f"📤 Response length: {len(response_text)} characters")

            # Extract car IDs mentioned in response for frontend linking
            car_ids_mentioned = []
            for car in relevant_cars:
                if car['make'].lower() in response_text.lower() and car['model'].lower() in response_text.lower():
                    car_ids_mentioned.append(car['id'])
            
            # Generate unique message ID for rating
            message_id = f"msg_{int(time.time())}_{hashlib.md5(response_text.encode()).hexdigest()[:8]}"
            
            # Store response in session history
            CHAT_SESSIONS[session_id] = combined_history + [{
                'role': 'user',
                'text': query
            }, {
                'role': 'bot',
                'text': response_text,
                'message_id': message_id
            }]
            
            # Limit session history size
            if len(CHAT_SESSIONS[session_id]) > 20:
                CHAT_SESSIONS[session_id] = CHAT_SESSIONS[session_id][-20:]
            
            return jsonify({
                'success': True,
                'response': response_text,
                'intent': intent,
                'relevant_car_ids': car_ids_mentioned[:5],  # Return up to 5 relevant car IDs
                'message_id': message_id
            })
            
        except requests.exceptions.Timeout:
            return jsonify({
                'success': False,
                'error': 'Chatbot Error: Request timed out. Please try again.'
            }), 500
        except requests.exceptions.RequestException as api_error:
            error_msg = str(api_error)
            print(f"❌ Request Error: {error_msg}")
            return jsonify({
                'success': False,
                'error': f'Chatbot Error: Network error - {error_msg}'
            }), 500
        except Exception as api_error:
            error_msg = str(api_error)
            print(f"❌ Gemini API Error: {error_msg}")
            print(f"Error type: {type(api_error)}")
            
            if 'API key' in error_msg or 'authentication' in error_msg.lower():
                error_msg = "Invalid API key. Please check your Gemini API key."
            elif 'quota' in error_msg.lower() or 'limit' in error_msg.lower():
                error_msg = "API quota exceeded. Please try again later."
            elif 'safety' in error_msg.lower() or 'blocked' in error_msg.lower():
                error_msg = "The query was blocked by safety filters. Please rephrase your question."
            
            return jsonify({
                'success': False,
                'error': f'Chatbot Error: {error_msg}'
            }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Chatbot error: {str(e)}'
        }), 500

@app.route('/api/chatbot/rate', methods=['POST'])
@require_auth
def rate_chatbot():
    """Rate a chatbot response"""
    try:
        if not request.is_json:
            return jsonify({'success': False, 'error': 'Request must be JSON'}), 400
        
        data = request.get_json(silent=True)
        if not data:
            return jsonify({'success': False, 'error': 'Invalid JSON data'}), 400
        
        rating = data.get('rating')
        feedback = data.get('feedback', '').strip()
        message_id = data.get('message_id', f"msg_{int(time.time())}")
        
        if not rating or rating < 1 or rating > 5:
            return jsonify({'success': False, 'error': 'Rating must be between 1 and 5'}), 400
        
        user_id = request.current_user['user_id']
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO chatbot_ratings (user_id, message_id, rating, feedback)
            VALUES (?, ?, ?, ?)
        ''', (user_id, message_id, rating, feedback))
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Thank you for your feedback!'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/analytics/insights', methods=['GET'])
@require_auth
def get_ai_insights():
    """Get AI-powered data analysis and insights (personalized)"""
    try:
        user_id = request.current_user['user_id']
        filter_type = request.args.get('filter', 'all')  # all, my, favorites
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Get cars based on filter
        if filter_type == 'my':
            cursor.execute('SELECT * FROM cars WHERE user_id = ?', (user_id,))
        elif filter_type == 'favorites':
            cursor.execute('''
                SELECT c.* FROM cars c
                INNER JOIN favorites f ON c.id = f.car_id
                WHERE f.user_id = ?
            ''', (user_id,))
        else:
            cursor.execute('SELECT * FROM cars')
        
        rows = cursor.fetchall()
        cars = [car_row_to_dict(row) for row in rows]
        
        # Get user-specific stats
        cursor.execute('SELECT COUNT(*) FROM cars WHERE user_id = ?', (user_id,))
        my_listings_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM favorites WHERE user_id = ?', (user_id,))
        favorites_count = cursor.fetchone()[0]
        
        if not cars:
            conn.close()
            return jsonify({
                'success': False,
                'error': 'No car data available for analysis'
            }), 404
        
        # Calculate statistics
        total_cars = len(cars)
        total_makes = len(set(car['make'] for car in cars if car.get('make')))
        total_models = len(set(f"{car['make']} {car['model']}" for car in cars if car.get('make') and car.get('model')))
        
        # Price analysis
        prices = [car['price'] for car in cars if car.get('price')]
        avg_price = sum(prices) / len(prices) if prices else 0
        min_price = min(prices) if prices else 0
        max_price = max(prices) if prices else 0
        
        # Rating analysis
        ratings = [car['rating'] for car in cars if car.get('rating')]
        avg_rating = sum(ratings) / len(ratings) if ratings else 0
        top_rated = sorted(cars, key=lambda x: x.get('rating', 0), reverse=True)[:5]
        
        # Make distribution
        make_counts = {}
        for car in cars:
            make = car.get('make', 'Unknown')
            make_counts[make] = make_counts.get(make, 0) + 1
        top_makes = sorted(make_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Year analysis
        years = [car['year'] for car in cars if car.get('year')]
        avg_year = sum(years) / len(years) if years else 0
        newest_year = max(years) if years else None
        oldest_year = min(years) if years else None
        
        # Price range distribution
        price_ranges = {
            'Budget (< 50K)': len([c for c in cars if c.get('price', 0) < 50000]),
            'Mid-Range (50K-100K)': len([c for c in cars if 50000 <= c.get('price', 0) < 100000]),
            'Premium (100K-200K)': len([c for c in cars if 100000 <= c.get('price', 0) < 200000]),
            'Luxury (200K+)': len([c for c in cars if c.get('price', 0) >= 200000])
        }
        
        # Currency distribution
        currency_counts = {}
        for car in cars:
            currency = car.get('currency', 'AED')
            currency_counts[currency] = currency_counts.get(currency, 0) + 1
        
        # Generate personalized AI insights using Gemini
        api_key = os.getenv('GEMINI_API_KEY')
        insights_text = ""
        
        if api_key and REQUESTS_AVAILABLE:
            try:
                personalization = ""
                if filter_type == 'my':
                    personalization = f"\n\nPersonal Context: This analysis is for YOUR listings ({my_listings_count} total). Focus on insights about your own inventory, pricing strategies, and recommendations for your listings."
                elif filter_type == 'favorites':
                    personalization = f"\n\nPersonal Context: This analysis is for YOUR favorite cars ({favorites_count} total). Focus on insights about your preferences, trends in your saved cars, and recommendations based on your interests."
                else:
                    personalization = f"\n\nPersonal Context: You have {my_listings_count} listings and {favorites_count} favorites. Consider these in your analysis."
                
                insights_prompt = f"""Analyze this car catalog data and provide 5-7 personalized, actionable insights:

Total Cars: {total_cars}
Total Makes: {total_makes}
Total Models: {total_models}
Average Price: {avg_price:.2f}
Price Range: {min_price:.2f} - {max_price:.2f}
Average Rating: {avg_rating:.2f}
Average Year: {avg_year:.0f}
Year Range: {oldest_year} - {newest_year}

Top Makes: {', '.join([f"{make} ({count})" for make, count in top_makes[:5]])}
Price Distribution: {price_ranges}
Currency Distribution: {currency_counts}
{personalization}

Provide concise, personalized, actionable insights about market trends, popular segments, pricing patterns, and specific recommendations. Format as a numbered list with emojis for visual appeal."""
                
                api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
                headers = {
                    'Content-Type': 'application/json',
                    'X-goog-api-key': api_key
                }
                
                payload = {
                    "contents": [{
                        "parts": [{"text": insights_prompt}],
                        "role": "user"
                    }],
                    "generationConfig": {
                        "temperature": 0.7,
                        "topP": 0.9,
                        "topK": 40,
                        "maxOutputTokens": 1024
                    }
                }
                
                response = requests.post(api_url, headers=headers, json=payload, timeout=30)
                if response.status_code == 200:
                    response_data = response.json()
                    if 'candidates' in response_data and len(response_data['candidates']) > 0:
                        insights_text = response_data['candidates'][0]['content']['parts'][0]['text']
            except Exception as e:
                print(f"AI insights generation failed: {e}")
                insights_text = "AI insights temporarily unavailable. Please check API key configuration."
        
        conn.close()
        
        return jsonify({
            'success': True,
            'filter': filter_type,
            'user_stats': {
                'my_listings': my_listings_count,
                'favorites': favorites_count
            },
            'insights': {
                'summary': {
                    'total_cars': total_cars,
                    'total_makes': total_makes,
                    'total_models': total_models,
                    'average_price': round(avg_price, 2),
                    'min_price': round(min_price, 2),
                    'max_price': round(max_price, 2),
                    'average_rating': round(avg_rating, 2),
                    'average_year': round(avg_year, 0) if avg_year else None,
                    'year_range': {'oldest': oldest_year, 'newest': newest_year}
                },
                'top_makes': [{'make': make, 'count': count} for make, count in top_makes],
                'top_rated_cars': [{
                    'id': car['id'],
                    'make': car.get('make'),
                    'model': car.get('model'),
                    'rating': car.get('rating', 0),
                    'price': car.get('price', 0)
                } for car in top_rated],
                'price_distribution': price_ranges,
                'currency_distribution': currency_counts,
                'ai_insights': insights_text
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/chatbot/stats', methods=['GET'])
@require_auth
def get_chatbot_stats():
    """Get chatbot statistics and ratings"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Get total ratings
        cursor.execute('SELECT COUNT(*) FROM chatbot_ratings')
        total_ratings = cursor.fetchone()[0]
        
        # Get average rating
        cursor.execute('SELECT AVG(rating) FROM chatbot_ratings')
        avg_rating = cursor.fetchone()[0] or 0
        
        # Get rating distribution
        cursor.execute('''
            SELECT rating, COUNT(*) as count
            FROM chatbot_ratings
            GROUP BY rating
            ORDER BY rating DESC
        ''')
        rating_distribution = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Get recent feedback
        cursor.execute('''
            SELECT rating, feedback, created_at
            FROM chatbot_ratings
            WHERE feedback IS NOT NULL AND feedback != ''
            ORDER BY created_at DESC
            LIMIT 10
        ''')
        recent_feedback = [
            {
                'rating': row[0],
                'feedback': row[1],
                'created_at': row[2]
            }
            for row in cursor.fetchall()
        ]
        
        conn.close()
        
        return jsonify({
            'success': True,
            'stats': {
                'total_ratings': total_ratings,
                'average_rating': round(avg_rating, 2) if avg_rating else 0,
                'rating_distribution': rating_distribution,
                'recent_feedback': recent_feedback
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/listing-assistant', methods=['POST'])
@require_auth
def listing_assistant():
    """AI Listing Assistant - helps users create and edit listings through natural conversation"""
    if not REQUESTS_AVAILABLE:
        return jsonify({
            'success': False,
            'error': 'Requests library not installed. Please install it with: pip install requests'
        }), 500
    
    try:
        if not request.is_json:
            return jsonify({'success': False, 'error': 'Request must be JSON'}), 400
        
        data = request.get_json(silent=True)
        if not data:
            return jsonify({'success': False, 'error': 'Invalid JSON data'}), 400
        
        query = data.get('query', '')
        api_key = data.get('api_key') or os.getenv('GEMINI_API_KEY')
        history = data.get('history', [])
        session_id = data.get('session') or request.args.get('session') or 'listing-assistant-default'
        
        if not query:
            return jsonify({'success': False, 'error': 'Query is required'}), 400
        
        if not api_key or api_key.strip() == '':
            return jsonify({
                'success': False,
                'error': 'API key is missing. Please add your Gemini API key.'
            }), 400
        
        # Get user's existing listings for context
        user_id = request.current_user['user_id']
        conn = get_db()
        cursor = conn.cursor()
        
        # Get market data for pricing suggestions
        cursor.execute('''
            SELECT make, model, year, price, currency, rating
            FROM cars
            ORDER BY created_at DESC
            LIMIT 50
        ''')
        market_cars = []
        for row in cursor.fetchall():
            market_cars.append({
                'make': row[0],
                'model': row[1],
                'year': row[2],
                'price': row[3],
                'currency': row[4],
                'rating': row[5] or 0.0
            })
        
        # Calculate average prices by make/model for pricing suggestions
        price_suggestions = {}
        for car in market_cars:
            key = f"{car['make']} {car['model']}"
            if key not in price_suggestions:
                price_suggestions[key] = []
            if car['price']:
                price_suggestions[key].append(car['price'])
        
        avg_prices = {}
        for key, prices in price_suggestions.items():
            if prices:
                avg_prices[key] = sum(prices) / len(prices)
        
        conn.close()
        
        # Build market context
        market_context = "Market Pricing Data:\n"
        for key, avg_price in list(avg_prices.items())[:20]:
            market_context += f"- {key}: Average price ~{avg_price:.0f}\n"
        
        # Detect Arabic
        is_arabic = bool(re.search(r"[\u0600-\u06FF]", query))
        
        # Build system prompt for listing assistant
        language_hint = "Arabic" if is_arabic else "English"
        
        system_instruction = f"""You are IntelliWheels' AI Listing Assistant. Your role is to help users create and edit car listings through natural conversation.

CAPABILITIES:
1. CREATE LISTINGS: Extract car information from user messages (make, model, year, price, specs, etc.) and help create listings
2. PRICING ASSISTANCE: Suggest appropriate prices based on market data, help negotiate fair pricing
3. EDIT LISTINGS: Help users update existing listings (price changes, spec updates, etc.)
4. INFORMATION GATHERING: Ask clarifying questions to gather all necessary listing details
5. VALIDATION: Ensure all required fields are provided before creating listings

MARKET DATA FOR PRICING:
{market_context}

RESPONSE GUIDELINES:
- Be conversational, helpful, and professional
- When user wants to create a listing, extract: make, model, year, price, currency, body style, engine, horsepower, fuel economy, image URL
- Suggest prices based on market data when user asks for pricing help
- Ask follow-up questions if information is missing
- When ready to create/update, provide a structured summary and ask for confirmation
- Answer in {language_hint}
- Format responses clearly with structured information when discussing listings

IMPORTANT:
- Always confirm details before creating/updating listings
- Suggest realistic prices based on market data
- Be helpful with pricing negotiations
- Extract all car details from natural language

When the user confirms they want to create or update a listing, provide a JSON-like structure with all the details so the system can process it."""

        try:
            api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
            
            headers = {
                'Content-Type': 'application/json',
                'X-goog-api-key': api_key
            }
            
            # Build conversation contents
            contents = []
            for msg in history:
                role = "user" if msg.get('role') == 'user' else "model"
                contents.append({
                    "parts": [{"text": msg.get('text', '')}],
                    "role": role
                })
            
            contents.append({
                "parts": [{"text": query}],
                "role": "user"
            })
            
            payload = {
                "contents": contents,
                "systemInstruction": {
                    "parts": [{"text": system_instruction}]
                },
                "generationConfig": {
                    "temperature": 0.7,
                    "topP": 0.9,
                    "topK": 40,
                    "maxOutputTokens": 2048
                }
            }
            
            response = requests.post(api_url, headers=headers, json=payload, timeout=45)
            
            if response.status_code != 200:
                error_data = response.json() if response.text else {}
                error_msg = error_data.get('error', {}).get('message', f'HTTP {response.status_code}: {response.text}')
                
                if response.status_code == 401 or response.status_code == 403:
                    error_msg = "Invalid API key. Please check your Gemini API key."
                elif response.status_code == 429:
                    error_msg = "API quota exceeded. Please try again later."
                
                return jsonify({
                    'success': False,
                    'error': f'Listing Assistant Error: {error_msg}'
                }), 500
            
            response_data = response.json()
            response_text = None
            
            if 'candidates' in response_data and len(response_data['candidates']) > 0:
                candidate = response_data['candidates'][0]
                
                if 'content' in candidate and 'parts' in candidate['content']:
                    for part in candidate['content']['parts']:
                        if 'text' in part:
                            response_text = part['text']
                            break
            
            if not response_text or response_text.strip() == "":
                response_text = "I'm sorry, I received an empty response. Please try asking your question differently."
            
            # Try to extract structured data from response (for listing creation/update)
            listing_data = None
            action_type = None
            
            # Look for JSON-like structures in response
            json_match = re.search(r'\{[^{}]*"make"[^{}]*\}', response_text, re.IGNORECASE)
            if json_match:
                try:
                    listing_data = json.loads(json_match.group(0))
                    if 'make' in listing_data and 'model' in listing_data:
                        action_type = 'create_listing'
                except:
                    pass
            
            # Check if user wants to create or update
            query_lower = query.lower()
            if any(word in query_lower for word in ['create', 'add', 'new listing', 'list my car']):
                action_type = 'create_listing'
            elif any(word in query_lower for word in ['edit', 'update', 'change', 'modify']):
                action_type = 'update_listing'
            
            return jsonify({
                'success': True,
                'response': response_text,
                'action_type': action_type,
                'listing_data': listing_data,
                'message_id': f"listing_msg_{int(time.time())}_{hashlib.md5(response_text.encode()).hexdigest()[:8]}"
            })
            
        except requests.exceptions.Timeout:
            return jsonify({
                'success': False,
                'error': 'Listing Assistant Error: Request timed out. Please try again.'
            }), 500
        except Exception as api_error:
            error_msg = str(api_error)
            return jsonify({
                'success': False,
                'error': f'Listing Assistant Error: {error_msg}'
            }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Listing Assistant error: {str(e)}'
        }), 500

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'success': True,
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    init_db()
    print("🚀 IntelliWheels API Server Starting...")
    print("📊 Database initialized")
    print("🌐 API available at http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)

