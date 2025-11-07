# How to Run IntelliWheels with CarMap Feature

## Quick Start Guide

### Prerequisites
- Python 3.7 or higher installed
- Web browser (Chrome, Firefox, Edge, Safari)

---

## Step-by-Step Instructions

### Step 1: Install Python Dependencies

Open a terminal/command prompt in the project directory and run:

```bash
pip install -r requirements.txt
```

This installs:
- Flask (web server)
- flask-cors (CORS support)
- pandas (data processing)
- openpyxl (Excel file handling)
- requests (HTTP requests)

---

### Step 2: Set Up Database

You need to populate the database with car data. Choose one option:

#### Option A: SQL Ingestion (Recommended)
```bash
python ingest_sql_to_db.py
```

**Note:** Make sure `data/Middle-East-GCC-Car-Database-by-Teoalida-SAMPLE.sql` exists in the `data/` folder.

#### Option B: Excel Ingestion
```bash
python ingest_excel_to_db.py
```

**Note:** Make sure `cars.xlsx` exists in the project root.

#### Option C: Add Location Data (Optional but Recommended for CarMap)
After ingesting data, add location coordinates to cars:
```bash
python add_car_locations.py
```

This assigns latitude/longitude to cars so they appear on the globe map.

---

### Step 3: Start the Backend Server

#### Windows:
```bash
python app.py
```

Or use the batch file:
```bash
start.bat
```

#### Linux/Mac:
```bash
python app.py
```

Or use the shell script:
```bash
chmod +x start.sh
./start.sh
```

**Expected Output:**
```
 * Running on http://127.0.0.1:5000
 * Debug mode: on
```

The backend server is now running on `http://localhost:5000`

---

### Step 4: Open the Frontend

You have two options:

#### Option A: Direct File Open (Simplest)
1. Navigate to your project folder
2. Double-click `index.html` to open it in your default browser
3. The app should load automatically

#### Option B: Local Server (Recommended for Development)
Open a **new terminal/command prompt** (keep the Flask server running) and run:

**Python:**
```bash
python -m http.server 8000
```

**Node.js (if installed):**
```bash
npx serve
```

**PHP (if installed):**
```bash
php -S localhost:8000
```

Then open your browser and go to:
- `http://localhost:8000` (if using local server)
- Or just open `index.html` directly

---

### Step 5: Use the Application

1. **Login/Signup:**
   - Create a new account or login with existing credentials
   - The system requires authentication to access features

2. **Navigate:**
   - **Listings** - Browse all cars
   - **Top Reviews** - See highest rated cars
   - **Favorites** - Your saved cars
   - **Chatbot** - AI assistant for car questions
   - **CarMap** - NEW! 3D globe view of car locations
   - **Add Listing** - Create new car entries

3. **Try CarMap:**
   - Click the "CarMap" tab in navigation
   - Wait for the globe to load
   - Hover over markers to see car names
   - Click markers to see car details
   - Drag to rotate, scroll to zoom

---

## Troubleshooting

### Backend won't start
- **Port 5000 already in use:**
  - Close other applications using port 5000
  - Or edit `app.py` and change the port:
    ```python
    app.run(host='0.0.0.0', port=5001, debug=True)  # Use port 5001 instead
    ```

### Database errors
- **"No such table: cars":**
  - Run the ingestion script: `python ingest_sql_to_db.py`
  
- **"No cars found":**
  - Make sure you've run the ingestion script
  - Check that `intelliwheels.db` exists in the project folder

### CarMap not loading
- **"Three.js not loaded":**
  - Check your internet connection (Three.js loads from CDN)
  - Open browser console (F12) to see errors
  
- **"Failed to load car map":**
  - Make sure backend server is running on port 5000
  - Check browser console for API errors
  - Verify you're logged in

### CORS Errors
- Make sure Flask-CORS is installed: `pip install flask-cors`
- Ensure backend is running before opening frontend

### Globe not showing markers
- Run `python add_car_locations.py` to add location data
- Check browser console for errors
- Verify cars have latitude/longitude in database

---

## Complete Example Workflow

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Ingest data
python ingest_sql_to_db.py

# 3. Add locations (optional but recommended)
python add_car_locations.py

# 4. Start backend (in one terminal)
python app.py

# 5. Open frontend (in another terminal or just open index.html)
python -m http.server 8000

# 6. Open browser
# Go to http://localhost:8000 or open index.html directly
```

---

## File Structure

```
IntelliWheels/
├── app.py                    # Flask backend server
├── index.html                # Frontend HTML
├── requirements.txt          # Python dependencies
├── intelliwheels.db          # SQLite database (created after ingestion)
├── add_car_locations.py      # Script to add location data
├── ingest_sql_to_db.py       # SQL data ingestion
├── ingest_excel_to_db.py     # Excel data ingestion
├── start.bat                 # Windows start script
├── start.sh                  # Linux/Mac start script
├── css/
│   └── style.css            # Styling
├── js/
│   ├── main.js              # Main application logic
│   ├── api.js               # API client
│   ├── ui.js                # UI rendering
│   └── globe.js             # 3D globe component (NEW!)
└── data/
    └── Middle-East-GCC-Car-Database-by-Teoalida-SAMPLE.sql
```

---

## Need Help?

1. Check browser console (F12) for JavaScript errors
2. Check terminal for Python/Flask errors
3. Verify all dependencies are installed
4. Ensure database is populated
5. Make sure backend is running before opening frontend

---

## Quick Commands Reference

```bash
# Install dependencies
pip install -r requirements.txt

# Ingest SQL data
python ingest_sql_to_db.py

# Add locations to cars
python add_car_locations.py

# Start backend
python app.py

# Start frontend server (optional)
python -m http.server 8000
```

---

**That's it! Your IntelliWheels application with CarMap is ready to use! 🚀**

