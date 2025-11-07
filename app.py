"""
IntelliWheels Backend API
Modern REST API for car catalog management with AI chatbot integration
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import json
import os
from datetime import datetime
from functools import wraps
import re

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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
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
            user_session TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(car_id, user_session)
        )
    ''')
    
    # Chat sessions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL UNIQUE,
            user_session TEXT,
            title TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Chat messages table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES chat_sessions(session_id)
        )
    ''')
    
    # Create index for faster queries
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_chat_messages_session 
        ON chat_messages(session_id, created_at)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_chat_sessions_user 
        ON chat_sessions(user_session, updated_at)
    ''')
    
    conn.commit()
    conn.close()

# Database helper functions
def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def car_row_to_dict(row):
    """Convert database row to dictionary"""
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
        'source_sheets': json.loads(row['source_sheets']) if row['source_sheets'] else []
    }

# API Routes

@app.route('/api/cars', methods=['GET'])
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
def create_car():
    """Create a new car listing"""
    try:
        data = request.json
        conn = get_db()
        cursor = conn.cursor()
        
        # Validate required fields
        required_fields = ['make', 'model']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400
        
        # Insert car
        cursor.execute('''
            INSERT INTO cars (make, model, year, price, currency, image_url, image_urls, 
                           rating, reviews, specs, engines, statistics, source_sheets)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            json.dumps(['Manual Entry'])
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
def update_car(car_id):
    """Update an existing car"""
    try:
        data = request.json
        conn = get_db()
        cursor = conn.cursor()
        
        # Check if car exists
        cursor.execute("SELECT id FROM cars WHERE id = ?", (car_id,))
        if not cursor.fetchone():
            conn.close()
            return jsonify({'success': False, 'error': 'Car not found'}), 404
        
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
def delete_car(car_id):
    """Delete a car"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Check if car exists
        cursor.execute("SELECT id FROM cars WHERE id = ?", (car_id,))
        if not cursor.fetchone():
            conn.close()
            return jsonify({'success': False, 'error': 'Car not found'}), 404
        
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

@app.route('/api/favorites', methods=['GET'])
def get_favorites():
    """Get user's favorite cars"""
    try:
        user_session = request.args.get('session', 'default')
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT c.* FROM cars c
            INNER JOIN favorites f ON c.id = f.car_id
            WHERE f.user_session = ?
            ORDER BY f.created_at DESC
        ''', (user_session,))
        
        rows = cursor.fetchall()
        cars = [car_row_to_dict(row) for row in rows]
        conn.close()
        
        return jsonify({'success': True, 'cars': cars})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/favorites', methods=['POST'])
def add_favorite():
    """Add a car to favorites"""
    try:
        data = request.json
        car_id = data.get('car_id')
        user_session = data.get('session', 'default')
        
        if not car_id:
            return jsonify({'success': False, 'error': 'car_id is required'}), 400
        
        conn = get_db()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO favorites (car_id, user_session)
                VALUES (?, ?)
            ''', (car_id, user_session))
            conn.commit()
            conn.close()
            return jsonify({'success': True, 'message': 'Added to favorites'})
        except sqlite3.IntegrityError:
            conn.close()
            return jsonify({'success': False, 'error': 'Already in favorites'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/favorites/<int:car_id>', methods=['DELETE'])
def remove_favorite(car_id):
    """Remove a car from favorites"""
    try:
        user_session = request.args.get('session', 'default')
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM favorites
            WHERE car_id = ? AND user_session = ?
        ''', (car_id, user_session))
        
        conn.commit()
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
def chatbot():
    """Enhanced AI Chatbot endpoint with negotiation capabilities and intelligent database querying"""
    if not REQUESTS_AVAILABLE:
        return jsonify({
            'success': False,
            'error': 'Requests library not installed. Please install it with: pip install requests'
        }), 500
    
    try:
        data = request.json
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

            # Persist conversation to server-side store
            session_messages = CHAT_SESSIONS.get(session_id, [])
            session_messages.append({ 'role': 'user', 'text': query })
            session_messages.append({ 'role': 'bot', 'text': response_text })
            # Keep last 15 messages
            if len(session_messages) > 15:
                session_messages = session_messages[-15:]
            CHAT_SESSIONS[session_id] = session_messages
            
            # Extract car IDs mentioned in response for frontend linking
            car_ids_mentioned = []
            for car in relevant_cars:
                if car['make'].lower() in response_text.lower() and car['model'].lower() in response_text.lower():
                    car_ids_mentioned.append(car['id'])
            
            return jsonify({
                'success': True,
                'response': response_text,
                'session': session_id,
                'intent': intent,
                'relevant_car_ids': car_ids_mentioned[:5]  # Return up to 5 relevant car IDs
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

