"""
Ingest SQL file data into SQLite database
Reads from Middle-East-GCC-Car-Database SQL file and populates the database
"""
import sqlite3
import json
import re
import os

DB_PATH = 'intelliwheels.db'
SQL_FILE_PATH = 'data/Middle-East-GCC-Car-Database-by-Teoalida-SAMPLE.sql'

def norm(s):
    """Normalize string values"""
    if s is None:
        return ""
    if isinstance(s, (int, float)):
        return str(s).strip()
    text = str(s).strip()
    if text.lower() in {"nan", "none", "null", "", "NULL"}:
        return ""
    return text

def extract_price_from_range(price_str):
    """Extract numeric price from price range string like 'AED 175,000 - 185,000'"""
    if not price_str:
        return None
    
    # Remove currency codes and extract first number
    price_str = re.sub(r'[A-Z]{3}\s*', '', price_str)  # Remove currency codes
    price_str = re.sub(r'\([^)]*\)', '', price_str)  # Remove parentheses content
    price_str = price_str.replace(',', '').strip()
    
    # Extract first number (could be range like "175000 - 185000")
    numbers = re.findall(r'\d+', price_str)
    if numbers:
        try:
            return float(numbers[0])
        except:
            pass
    return None

def determine_currency_from_price(price_uae, price_ksa):
    """Determine currency based on available prices"""
    if price_uae and price_uae.strip():
        return 'AED'
    elif price_ksa and price_ksa.strip():
        return 'SAR'
    return 'AED'  # Default

def parse_sql_inserts(sql_content):
    """Parse INSERT statements from SQL file"""
    # Find all INSERT statements
    insert_pattern = r"INSERT INTO[^;]+;"
    inserts = re.findall(insert_pattern, sql_content, re.IGNORECASE | re.DOTALL)
    
    rows = []
    for insert in inserts:
        # Extract VALUES part
        values_match = re.search(r'VALUES\s+(.+?);', insert, re.IGNORECASE | re.DOTALL)
        if not values_match:
            continue
        
        values_str = values_match.group(1)
        
        # Parse individual value rows
        # This is tricky because values can contain commas, quotes, etc.
        # We'll use a more robust parsing approach
        row_pattern = r'\(([^)]+(?:\([^)]*\)[^)]*)*)\)'
        value_rows = re.findall(row_pattern, values_str)
        
        for row_str in value_rows:
            # Split by comma, but respect quoted strings
            values = []
            current_value = ""
            in_quotes = False
            quote_char = None
            
            i = 0
            while i < len(row_str):
                char = row_str[i]
                
                if char in ('"', "'") and (i == 0 or row_str[i-1] != '\\'):
                    if not in_quotes:
                        in_quotes = True
                        quote_char = char
                    elif char == quote_char:
                        in_quotes = False
                        quote_char = None
                    current_value += char
                elif char == ',' and not in_quotes:
                    values.append(current_value.strip())
                    current_value = ""
                else:
                    current_value += char
                
                i += 1
            
            if current_value.strip():
                values.append(current_value.strip())
            
            # Clean up values (remove quotes, handle NULL)
            cleaned_values = []
            for val in values:
                val = val.strip()
                if val.upper() == 'NULL' or val == '':
                    cleaned_values.append(None)
                elif val.startswith("'") and val.endswith("'"):
                    cleaned_values.append(val[1:-1].replace("''", "'"))
                elif val.startswith('"') and val.endswith('"'):
                    cleaned_values.append(val[1:-1].replace('""', '"'))
                else:
                    cleaned_values.append(val)
            
            if len(cleaned_values) >= 4:  # At least Make, Model, Year, etc.
                rows.append(cleaned_values)
    
    return rows

def parse_sql_file_better(sql_file_path):
    """Better SQL file parser - handles INSERT statements more reliably"""
    print(f"Reading SQL file: {sql_file_path}")
    
    with open(sql_file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # Find the INSERT statement
    insert_match = re.search(
        r'INSERT INTO[^`]+`([^`]+)`[^(]+VALUES\s+(.+?);',
        content,
        re.IGNORECASE | re.DOTALL
    )
    
    if not insert_match:
        print("ERROR: Could not find INSERT statement in SQL file")
        return []
    
    values_part = insert_match.group(2)
    
    # Split by ), but handle nested quotes
    rows = []
    current_row = ""
    paren_depth = 0
    in_string = False
    string_char = None
    i = 0
    
    while i < len(values_part):
        char = values_part[i]
        next_char = values_part[i+1] if i+1 < len(values_part) else ''
        
        if char in ("'", '"') and (i == 0 or values_part[i-1] != '\\'):
            if not in_string:
                in_string = True
                string_char = char
            elif char == string_char:
                in_string = False
                string_char = None
            current_row += char
        elif char == '(' and not in_string:
            paren_depth += 1
            if paren_depth == 1:
                current_row = ""  # Start new row
            else:
                current_row += char
        elif char == ')' and not in_string:
            paren_depth -= 1
            if paren_depth == 0:
                # End of row
                rows.append(current_row)
                current_row = ""
            else:
                current_row += char
        else:
            current_row += char
        
        i += 1
    
    return rows

def parse_row_values(row_str):
    """Parse a single row string into individual values"""
    values = []
    current = ""
    in_quotes = False
    quote_char = None
    i = 0
    
    while i < len(row_str):
        char = row_str[i]
        
        # Handle escaped characters
        if char == '\\' and i + 1 < len(row_str):
            current += char + row_str[i+1]
            i += 2
            continue
        
        # Handle quotes
        if char in ("'", '"'):
            if not in_quotes:
                in_quotes = True
                quote_char = char
            elif char == quote_char:
                in_quotes = False
                quote_char = None
            current += char
        elif char == ',' and not in_quotes:
            # Split here
            val = current.strip()
            if val.upper() == 'NULL' or val == '':
                values.append(None)
            elif val.startswith("'") and val.endswith("'"):
                values.append(val[1:-1].replace("''", "'").replace("\\'", "'"))
            elif val.startswith('"') and val.endswith('"'):
                values.append(val[1:-1].replace('""', '"').replace('\\"', '"'))
            else:
                values.append(val)
            current = ""
        else:
            current += char
        
        i += 1
    
    # Add last value
    if current.strip():
        val = current.strip()
        if val.upper() == 'NULL' or val == '':
            values.append(None)
        elif val.startswith("'") and val.endswith("'"):
            values.append(val[1:-1].replace("''", "'").replace("\\'", "'"))
        elif val.startswith('"') and val.endswith('"'):
            values.append(val[1:-1].replace('""', '"').replace('\\"', '"'))
        else:
            values.append(val)
    
    return values

def init_db():
    """Initialize database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
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
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS statistics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            car_id INTEGER,
            stat_name TEXT,
            stat_value TEXT,
            FOREIGN KEY (car_id) REFERENCES cars(id)
        )
    ''')
    
    conn.commit()
    conn.close()

def main():
    """Main ingestion function"""
    print("Starting SQL data ingestion...")
    
    if not os.path.exists(SQL_FILE_PATH):
        print(f"ERROR: {SQL_FILE_PATH} not found!")
        return
    
    init_db()
    
    # Read and parse SQL file
    print(f"Reading SQL file: {SQL_FILE_PATH}")
    
    with open(SQL_FILE_PATH, 'r', encoding='utf-8', errors='ignore') as f:
        sql_content = f.read()
    
    # Extract INSERT statements more carefully
    # Find the table structure first to understand column order
    table_match = re.search(
        r'CREATE TABLE[^`]+`([^`]+)`\s*\(([^)]+)\)',
        sql_content,
        re.IGNORECASE | re.DOTALL
    )
    
    # Extract column names from INSERT statement
    column_header_match = re.search(
        r'INSERT INTO[^`]+`([^`]+)`\s*\(([^)]+)\)',
        sql_content,
        re.IGNORECASE | re.DOTALL
    )
    
    if column_header_match:
        columns_part = column_header_match.group(2)
        # Extract column names from backticks
        column_matches = re.findall(r'`([^`]+)`', columns_part)
        print(f"Found columns: {len(column_matches)} columns")
        print(f"   First 5 columns: {', '.join(column_matches[:5])}")
    else:
        # Default column order based on the SQL structure
        column_matches = [
            'URL', 'Make', 'Model', 'Year', 'Image 1', 'Image 2',
            'Price UAE', 'Price KSA', 'Country of Origin', 'Class',
            'Body Styles', 'Weight', 'Good', 'Bad', 'Overview',
            'Reliability', 'Resale Value', 'Known Problems',
            'NHTSA Driver Frontal Rating', 'EuroNCAP Overall Adult Rating',
            'Engine', 'Gearbox', 'Power (hp)', 'Torque (Nm)',
            'Fuel Econ (L/100km)', 'Fuel Econ (km/L)',
            '0-100 kph (sec)', 'Top speed (kph)'
        ]
        print(f"Using default column order: {len(column_matches)} columns")
    
    # Parse INSERT statements
    print("Parsing INSERT statements...")
    
    # Use a simpler approach: execute SQL directly on a temporary database
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()
    
    # Create temporary table matching SQL structure
    create_table_sql = re.search(
        r'CREATE TABLE[^`]+`([^`]+)`\s*\([^)]+\)',
        sql_content,
        re.IGNORECASE | re.DOTALL
    )
    
    if create_table_sql:
        # Convert MySQL CREATE TABLE to SQLite-compatible
        create_stmt = create_table_sql.group(0)
        create_stmt = re.sub(r'`([^`]+)`', r'\1', create_stmt)  # Remove backticks
        create_stmt = re.sub(r'varchar\([^)]+\)', 'TEXT', create_stmt, flags=re.IGNORECASE)
        create_stmt = re.sub(r'ENGINE[^;]+', '', create_stmt, flags=re.IGNORECASE)
        create_stmt = re.sub(r'DEFAULT CHARSET[^;]+', '', create_stmt, flags=re.IGNORECASE)
        
        try:
            cursor.execute(create_stmt)
            print("Created temporary table")
        except Exception as e:
            print(f"WARNING: Could not create temp table: {e}")
            conn.close()
            # Fall back to manual parsing
            all_rows = parse_manually(sql_content)
            if all_rows:
                # Process manually parsed rows
                return process_rows(all_rows, column_matches)
            return
    
    # Extract and execute INSERT statements
    insert_statements = re.findall(
        r'INSERT INTO[^;]+;',
        sql_content,
        re.IGNORECASE | re.DOTALL
    )
    
    print(f"Found {len(insert_statements)} INSERT statement(s)")
    
    for insert_stmt in insert_statements:
        # Convert MySQL INSERT to SQLite-compatible
        insert_stmt = re.sub(r'`([^`]+)`', r'\1', insert_stmt)
        try:
            cursor.execute(insert_stmt)
        except Exception as e:
            print(f"WARNING: Error executing INSERT: {str(e)[:100]}")
            continue
    
    # Fetch all rows
    cursor.execute(f"SELECT * FROM {column_matches[0] if column_matches else 'middle_east_gcc_car_database_sample'}")
    all_rows = cursor.fetchall()
    conn.close()
    
    print(f"Found {len(all_rows)} rows in SQL file")
    
    if len(all_rows) == 0:
        print("WARNING: No data rows found. Trying alternative parsing method...")
        manual_rows = parse_manually(sql_content)
        if manual_rows:
            return process_rows(manual_rows, column_matches)
        return
    
    # Process rows and insert into main database
    return process_rows(all_rows, column_matches)

def process_rows(all_rows, column_matches):
    """Process and insert rows into database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    inserted = 0
    skipped = 0
    
    for row in all_rows:
        try:
            # Map SQL columns to our structure
            # row is a tuple, need to map by index
            if len(row) < 4:  # Need at least URL, Make, Model, Year
                skipped += 1
                continue
            
            # Create a dictionary for easier access
            # Handle both tuple (from DB) and list (from manual parsing)
            row_list = list(row) if isinstance(row, tuple) else row
            row_dict = {}
            for i, col_name in enumerate(column_matches):
                if i < len(row_list):
                    row_dict[col_name] = row_list[i]
            
            make = norm(row_dict.get('Make', ''))
            model = norm(row_dict.get('Model', ''))
            year_str = norm(row_dict.get('Year', ''))
            
            # Skip header/info rows
            if not make or not model or make.lower() in ['', 'none', 'null'] or model.lower() in ['', 'none', 'null']:
                skipped += 1
                continue
            
            # Parse year
            try:
                year = int(year_str) if year_str and year_str.isdigit() else None
            except:
                year = None
            
            # Get prices
            price_uae = norm(row_dict.get('Price UAE', ''))
            price_ksa = norm(row_dict.get('Price KSA', ''))
            
            price = None
            currency = 'AED'
            
            if price_uae:
                price = extract_price_from_range(price_uae)
                currency = 'AED'
            elif price_ksa:
                price = extract_price_from_range(price_ksa)
                currency = 'SAR'
            
            # Generate price if missing
            if not price:
                base_prices = {
                    "BMW": 200000, "Mercedes-Benz": 220000, "Audi": 200000,
                    "Toyota": 120000, "Honda": 100000, "Nissan": 110000,
                    "Ford": 130000, "Chevrolet": 120000, "Porsche": 400000
                }
                base_price = base_prices.get(make, 100000)
                if year:
                    year_factor = 1.0 + (2024 - year) * 0.05
                    year_factor = max(0.3, min(1.2, year_factor))
                    price = base_price * year_factor
                else:
                    price = base_price
            
            # Get images
            image1 = norm(row_dict.get('Image 1', ''))
            image2 = norm(row_dict.get('Image 2', ''))
            image_urls = []
            if image1:
                image_urls.append(image1)
            if image2:
                image_urls.append(image2)
            main_image = image_urls[0] if image_urls else ''
            
            # Build specs
            specs = {
                'bodyStyle': norm(row_dict.get('Body Styles', 'Unknown')),
                'class': norm(row_dict.get('Class', '')),
                'weight': norm(row_dict.get('Weight', '')),
                'countryOfOrigin': norm(row_dict.get('Country of Origin', ''))
            }
            
            # Add engine specs
            engine = norm(row_dict.get('Engine', ''))
            if engine:
                specs['engine'] = engine
            
            power = norm(row_dict.get('Power (hp)', ''))
            if power and power.isdigit():
                specs['horsepower'] = int(power)
            
            fuel_econ = norm(row_dict.get('Fuel Econ (L/100km)', ''))
            if fuel_econ:
                specs['fuelEconomy'] = fuel_econ
            
            # Build engines array
            engines = []
            if engine or power or fuel_econ:
                engine_obj = {}
                if engine:
                    engine_obj['type'] = engine
                if power:
                    engine_obj['power'] = power + ' hp'
                torque = norm(row_dict.get('Torque (Nm)', ''))
                if torque:
                    engine_obj['torque'] = torque + ' Nm'
                gearbox = norm(row_dict.get('Gearbox', ''))
                if gearbox:
                    engine_obj['gearbox'] = gearbox
                if fuel_econ:
                    engine_obj['fuelEconomy'] = fuel_econ + ' L/100km'
                
                if engine_obj:
                    engines.append(engine_obj)
            
            # Build statistics
            statistics = {}
            if norm(row_dict.get('Reliability', '')):
                statistics['Reliability'] = norm(row_dict.get('Reliability', ''))
            if norm(row_dict.get('Resale Value', '')):
                statistics['Resale Value'] = norm(row_dict.get('Resale Value', ''))
            if norm(row_dict.get('NHTSA Driver Frontal Rating', '')):
                statistics['NHTSA Rating'] = norm(row_dict.get('NHTSA Driver Frontal Rating', ''))
            if norm(row_dict.get('EuroNCAP Overall Adult Rating', '')):
                statistics['EuroNCAP Rating'] = norm(row_dict.get('EuroNCAP Overall Adult Rating', ''))
            
            # Generate rating and reviews
            rating = 4.0 + (hash(f"{make}{model}{year}") % 100) / 100  # 4.0-5.0
            reviews = (hash(f"{make}{model}") % 500) + 50  # 50-550
            
            # Insert into database
            cursor.execute('''
                INSERT OR REPLACE INTO cars 
                (make, model, year, price, currency, image_url, image_urls, 
                 rating, reviews, specs, engines, statistics, source_sheets)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                make,
                model,
                year,
                price,
                currency,
                main_image,
                json.dumps(image_urls),
                round(rating, 1),
                reviews,
                json.dumps(specs),
                json.dumps(engines) if engines else None,
                json.dumps(statistics) if statistics else None,
                json.dumps(['SQL Database'])
            ))
            inserted += 1
            
        except Exception as e:
            print(f"WARNING: Error processing row: {e}")
            skipped += 1
            continue
    
    conn.commit()
    conn.close()
    
    print(f"\nSUCCESS: Inserted {inserted} cars into database!")
    print(f"WARNING: Skipped {skipped} rows (headers/invalid data)")
    print(f"Database ready at: {DB_PATH}")

def parse_manually(sql_content):
    """Fallback manual parsing method - line-by-line approach"""
    print("Using manual parsing method...")
    
    rows = []
    # Find INSERT INTO ... VALUES section
    # Use greedy match to get all values until the final semicolon
    insert_match = re.search(r'VALUES\s+(.+);', sql_content, re.IGNORECASE | re.DOTALL)
    
    if not insert_match:
        print("ERROR: Could not find VALUES section")
        return rows
    
    values_text = insert_match.group(1).strip()
    
    # Remove trailing semicolon if present
    if values_text.endswith(';'):
        values_text = values_text[:-1].strip()
    
    # Parse row by row - each row starts with '(' and ends with '),'
    # We need to handle multi-line rows and escaped quotes
    current_row = ""
    in_row = False
    paren_depth = 0
    in_string = False
    string_char = None
    i = 0
    
    while i < len(values_text):
        char = values_text[i]
        next_char = values_text[i+1] if i+1 < len(values_text) else ''
        
        # Handle escaped characters
        if char == '\\' and next_char:
            current_row += char + next_char
            i += 2
            continue
        
        # Handle string quotes
        if char in ("'", '"'):
            if not in_string:
                in_string = True
                string_char = char
            elif char == string_char:
                # Check if it's escaped ('' for SQL)
                if next_char == char:
                    current_row += char + char
                    i += 2
                    continue
                in_string = False
                string_char = None
            current_row += char
        
        # Handle parentheses
        elif char == '(' and not in_string:
            paren_depth += 1
            if paren_depth == 1:
                current_row = ""  # Start new row
            else:
                current_row += char
        
        elif char == ')' and not in_string:
            paren_depth -= 1
            if paren_depth == 0:
                # End of row - parse it
                values = parse_row_values(current_row)
                if len(values) > 0:
                    rows.append(values)
                current_row = ""
            else:
                current_row += char
        
        # Handle commas
        elif char == ',' and not in_string and paren_depth == 0:
            # This comma separates rows, ignore it
            pass
        
        else:
            current_row += char
        
        i += 1
    
    print(f"Manually parsed {len(rows)} rows")
    return rows

if __name__ == "__main__":
    main()

