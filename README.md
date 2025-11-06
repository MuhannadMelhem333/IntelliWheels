# IntelliWheels - Professional Car Catalog Platform

A modern, professional car catalog application with AI chatbot integration, built with Flask backend and modern JavaScript frontend.

## Features

- 🚗 **Complete Car Catalog** - View, search, filter, and manage car listings
- 🤖 **AI Chatbot** - Integrated Google Gemini AI for car-related questions
- ⭐ **Favorites System** - Save and manage favorite cars
- 📊 **Excel Data Integration** - Reads from 5 Excel sheets (Make-Model-Year, Make-Model, Basic Specs, Engine Specs, Statistics)
- 🎨 **Modern UI** - Professional, responsive design with smooth animations
- 🔄 **Full CRUD Operations** - Create, Read, Update, Delete car listings via REST API
- 💾 **SQLite Database** - Free, lightweight database solution

## Tech Stack

### Backend
- Flask (Python web framework)
- SQLite (Database)
- Pandas (Excel processing)
- Google Generative AI (Gemini)

### Frontend
- Vanilla JavaScript (ES6 Modules)
- Tailwind CSS
- Modern CSS with animations

## Setup Instructions

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. Ingest SQL Data to Database

Make sure your SQL file (`data/Middle-East-GCC-Car-Database-by-Teoalida-SAMPLE.sql`) is in the `data/` directory.

Then run the SQL ingestion script:

```bash
python ingest_sql_to_db.py
```

This will create `intelliwheels.db` and populate it with data from the SQL file.

**Alternative: Excel Ingestion**

If you prefer to use Excel files instead, place your `cars.xlsx` file in the project root with the following sheets:
- Make-Model-Year
- Make-Model
- Basic Specs
- Engine Specs
- Statistics

Then run:
```bash
python ingest_excel_to_db.py
```

### 3. Configure Gemini API Key

Edit `js/main.js` and replace `YOUR_GEMINI_API_KEY_HERE` with your actual Gemini API key:

```javascript
const GEMINI_API_KEY = "your-actual-api-key-here";
```

Alternatively, you can set it as an environment variable:

```bash
export GEMINI_API_KEY="your-actual-api-key-here"
```

### 4. Start the Backend Server

```bash
python app.py
```

The server will start on `http://localhost:5000`

### 5. Open the Frontend

Simply open `index.html` in your web browser, or use a local server:

```bash
# Using Python
python -m http.server 8000

# Using Node.js
npx serve

# Using PHP
php -S localhost:8000
```

Then navigate to `http://localhost:8000` (or your chosen port)

## API Endpoints

### Cars
- `GET /api/cars` - Get all cars (supports query params: make, search, sort, limit, offset)
- `GET /api/cars/<id>` - Get a single car
- `POST /api/cars` - Create a new car
- `PATCH /api/cars/<id>` - Update a car
- `DELETE /api/cars/<id>` - Delete a car

### Makes
- `GET /api/makes` - Get all unique car makes

### Favorites
- `GET /api/favorites` - Get user's favorite cars
- `POST /api/favorites` - Add a car to favorites
- `DELETE /api/favorites/<car_id>` - Remove a car from favorites

### Chatbot
- `POST /api/chatbot` - Send a message to the AI chatbot

### Health
- `GET /api/health` - Health check endpoint

## Project Structure

```
IntelliWheels/
├── app.py                 # Flask backend server
├── ingest_excel_to_db.py  # Excel data ingestion script
├── requirements.txt       # Python dependencies
├── intelliwheels.db       # SQLite database (created after ingestion)
├── cars.xlsx              # Excel data file
├── index.html             # Main HTML file
├── css/
│   └── style.css          # Enhanced modern styling
└── js/
    ├── main.js            # Main application logic
    ├── api.js             # API client
    └── ui.js              # UI rendering functions
```

## Features in Detail

### Car Management
- Browse all cars with beautiful card layouts
- Search by make or model
- Filter by make
- Sort by price (low to high, high to low) or rating
- View detailed car information in modal
- Add new car listings
- Edit existing listings (via API)
- Delete car listings

### AI Chatbot
- Ask questions about cars, maintenance, specifications
- Get recommendations and comparisons
- Powered by Google Gemini AI

### Favorites
- Save cars to favorites
- Persistent storage (database + localStorage)
- View all favorites in dedicated page

### Data Management
- Automatic ingestion from Excel
- Support for multiple data sources
- Statistics tracking
- Engine specifications
- Comprehensive car specifications

## Development

### Adding New Features

1. **Backend**: Add new routes in `app.py`
2. **Frontend**: Add API calls in `js/api.js`
3. **UI**: Add rendering logic in `js/ui.js`
4. **Styling**: Add styles in `css/style.css`

### Database Schema

The main `cars` table includes:
- Basic info (make, model, year, price, currency)
- Images (image_url, image_urls)
- Ratings (rating, reviews)
- Specifications (specs as JSON)
- Engines (engines as JSON)
- Statistics (statistics as JSON)
- Source tracking (source_sheets)

## Troubleshooting

### Backend not starting
- Make sure port 5000 is not in use
- Check that all dependencies are installed
- Verify Python version (3.7+)

### Database errors
- Run `ingest_excel_to_db.py` to initialize database
- Check that `cars.xlsx` exists and has all 5 sheets

### Chatbot not working
- Verify Gemini API key is set correctly
- Check browser console for API errors
- Ensure backend server is running

### CORS errors
- Make sure Flask-CORS is installed
- Check that backend is running on correct port
- Verify API base URL in `js/api.js`

## License

This project is open source and available for use.

## Contributing

Feel free to submit issues and enhancement requests!

---

Built with ❤️ for car enthusiasts

