# IntelliWheels - Comprehensive Technical Report

**Project:** IntelliWheels - AI-Powered Car Catalog Management System  
**Date:** 2024  
**Version:** 1.0.0

---

## Table of Contents
1. [Executive Summary](#executive-summary)
2. [Frontend Technologies](#frontend-technologies)
3. [Backend Technologies](#backend-technologies)
4. [Database Schema](#database-schema)
5. [API Endpoints](#api-endpoints)
6. [Features and Functionality](#features-and-functionality)
7. [Architecture Overview](#architecture-overview)
8. [Dependencies](#dependencies)

---

## Executive Summary

IntelliWheels is a full-stack web application for managing a car catalog with AI-powered features. The system includes user authentication, car listing management, AI chatbot assistance, personalized analytics, and an interactive user interface. The application is built using modern web technologies with a Flask backend, vanilla JavaScript frontend, and SQLite database.

---

## Frontend Technologies

### Core Technologies
- **HTML5**: Semantic markup for application structure
- **CSS3**: Advanced styling with custom properties, animations, and glassmorphism effects
- **JavaScript (ES6+)**: Modern JavaScript with modules, async/await, and ES6+ features
- **Tailwind CSS (CDN)**: Utility-first CSS framework for rapid UI development

### External Libraries & Services
- **Google Fonts**:
  - Inter (weights: 300-900)
  - Space Grotesk (weights: 400-700)
- **Tailwind CSS CDN**: v3.x for utility classes
- **SVG Icons**: Custom SVG icons embedded in HTML

### Frontend Architecture

#### File Structure
```
frontend/
├── index.html          # Main HTML structure
├── css/
│   └── style.css       # Custom styles and theme
└── js/
    ├── main.js         # Application logic and state management
    ├── api.js          # API communication layer
    └── ui.js           # UI rendering and DOM manipulation
```

#### Key Frontend Features

**1. User Interface Components:**
- Responsive navigation bar with horizontal scrolling
- Glassmorphism design with backdrop blur effects
- Dark theme with neon blue/purple accents
- Mobile-responsive hamburger menu
- Interactive cards and modals
- Loading states and error handling
- Smooth animations and transitions

**2. State Management:**
- Local storage for authentication tokens
- Session management for chat histories
- Client-side state for filters and UI state
- Real-time UI updates

**3. User Pages:**
- **Login/Signup**: Authentication pages with form validation
- **Listings**: Car catalog with search, filter, and sort
- **Top Reviews**: Highest-rated cars display
- **Favorites**: User's saved cars
- **My Listings**: User's own car listings with edit/delete
- **Profile Settings**: Account management (username, email, password)
- **Chatbot**: AI-powered car assistance
- **AI Listing Assistant**: Natural language listing creation
- **Analytics**: Interactive data visualization with filters

**4. Interactive Features:**
- Real-time search and filtering
- Dynamic car list rendering
- Modal dialogs for car details and editing
- Form validation with visual feedback
- Password strength validation
- Chat history management
- Analytics filtering (All/My Listings/Favorites)

---

## Backend Technologies

### Core Framework
- **Flask 3.0.0**: Python web framework
- **Python 3.x**: Programming language

### Backend Libraries

**1. Core Dependencies:**
- **flask-cors (4.0.0)**: Cross-Origin Resource Sharing support
- **requests (2.31.0)**: HTTP library for external API calls (Gemini AI)
- **flask-swagger-ui (5.21.0)**: API documentation interface

**2. Data Processing:**
- **pandas (2.1.3)**: Data manipulation and analysis
- **openpyxl (3.1.2)**: Excel file reading/writing

**3. Security:**
- **hashlib**: Password hashing (SHA-256)
- **secrets**: Secure token generation
- **functools.wraps**: Authentication decorators

### Backend Architecture

#### File Structure
```
backend/
└── app.py              # Main Flask application (2583 lines)
```

#### Key Backend Features

**1. Authentication System:**
- User registration with email/username validation
- Secure password hashing (SHA-256)
- Session-based authentication with tokens
- Token expiration (30 days)
- Session verification endpoint

**2. API Architecture:**
- RESTful API design
- JSON request/response format
- CORS enabled for frontend communication
- Error handling with appropriate HTTP status codes
- Request validation

**3. AI Integration:**
- **Google Gemini API**: 
  - Chatbot for car queries
  - AI Listing Assistant for natural language listing creation
  - Personalized analytics insights
- Intent detection for user queries
- Context-aware responses

**4. Data Management:**
- SQLite database operations
- Database migrations
- Transaction management
- Data validation and sanitization

---

## Database Schema

### Database: SQLite (intelliwheels.db)

#### Tables

**1. `cars` - Main Car Listings Table**
```sql
- id (INTEGER, PRIMARY KEY, AUTOINCREMENT)
- make (TEXT, NOT NULL)
- model (TEXT, NOT NULL)
- year (INTEGER)
- price (REAL)
- currency (TEXT, DEFAULT 'AED')
- image_url (TEXT)
- image_urls (TEXT) - JSON array
- rating (REAL, DEFAULT 0.0)
- reviews (INTEGER, DEFAULT 0)
- specs (TEXT) - JSON object
- engines (TEXT) - JSON array
- statistics (TEXT) - JSON object
- source_sheets (TEXT) - JSON array
- latitude (REAL)
- longitude (REAL)
- user_id (INTEGER) - Foreign key to users(id)
- created_at (TIMESTAMP, DEFAULT CURRENT_TIMESTAMP)
- updated_at (TIMESTAMP, DEFAULT CURRENT_TIMESTAMP)
```

**Indexes:**
- `idx_cars_user_id` on `user_id`

**2. `users` - User Accounts Table**
```sql
- id (INTEGER, PRIMARY KEY, AUTOINCREMENT)
- username (TEXT, NOT NULL, UNIQUE)
- email (TEXT, NOT NULL, UNIQUE)
- password_hash (TEXT, NOT NULL)
- created_at (TIMESTAMP, DEFAULT CURRENT_TIMESTAMP)
- last_login (TIMESTAMP)
```

**3. `user_sessions` - Authentication Sessions Table**
```sql
- id (INTEGER, PRIMARY KEY, AUTOINCREMENT)
- user_id (INTEGER, NOT NULL) - Foreign key to users(id)
- token (TEXT, NOT NULL, UNIQUE)
- created_at (TIMESTAMP, DEFAULT CURRENT_TIMESTAMP)
- expires_at (TIMESTAMP)
```

**Indexes:**
- `idx_user_sessions_token` on `token`
- `idx_user_sessions_user` on `user_id`

**4. `favorites` - User Favorites Table**
```sql
- id (INTEGER, PRIMARY KEY, AUTOINCREMENT)
- car_id (INTEGER, NOT NULL) - Foreign key to cars(id)
- user_id (INTEGER, NOT NULL) - Foreign key to users(id)
- created_at (TIMESTAMP, DEFAULT CURRENT_TIMESTAMP)
- UNIQUE(car_id, user_id)
```

**5. `statistics` - Car Statistics Table**
```sql
- id (INTEGER, PRIMARY KEY, AUTOINCREMENT)
- car_id (INTEGER) - Foreign key to cars(id)
- stat_name (TEXT)
- stat_value (TEXT)
```

**6. `chatbot_ratings` - Chatbot Feedback Table**
```sql
- id (INTEGER, PRIMARY KEY, AUTOINCREMENT)
- user_id (INTEGER, NOT NULL) - Foreign key to users(id)
- message_id (TEXT)
- rating (INTEGER, NOT NULL, CHECK: 1-5)
- feedback (TEXT)
- created_at (TIMESTAMP, DEFAULT CURRENT_TIMESTAMP)
```

**7. `analytics_cache` - Analytics Cache Table**
```sql
- id (INTEGER, PRIMARY KEY, AUTOINCREMENT)
- analysis_type (TEXT, NOT NULL)
- data (TEXT, NOT NULL) - JSON
- created_at (TIMESTAMP, DEFAULT CURRENT_TIMESTAMP)
- expires_at (TIMESTAMP)
```

### Database Relationships
- `cars.user_id` → `users.id` (Many-to-One)
- `user_sessions.user_id` → `users.id` (Many-to-One)
- `favorites.car_id` → `cars.id` (Many-to-One)
- `favorites.user_id` → `users.id` (Many-to-One)
- `statistics.car_id` → `cars.id` (Many-to-One)
- `chatbot_ratings.user_id` → `users.id` (Many-to-One)

---

## API Endpoints

### Base URL: `http://localhost:5000`

### Authentication Endpoints

**1. POST `/api/auth/signup`**
- **Description**: User registration
- **Request Body**: `{username, email, password}`
- **Response**: `{success, token, user}`
- **Status Codes**: 201 (Created), 400 (Bad Request)

**2. POST `/api/auth/login`**
- **Description**: User authentication
- **Request Body**: `{email, password}`
- **Response**: `{success, token, user}`
- **Status Codes**: 200 (OK), 401 (Unauthorized)

**3. POST `/api/auth/logout`**
- **Description**: User logout
- **Headers**: `Authorization: Bearer <token>`
- **Response**: `{success, message}`
- **Status Codes**: 200 (OK)

**4. GET `/api/auth/verify`**
- **Description**: Verify session validity
- **Headers**: `Authorization: Bearer <token>` or query param `?token=`
- **Response**: `{success, authenticated, user}`
- **Status Codes**: 200 (OK)

### Car Management Endpoints

**5. GET `/api/cars`**
- **Description**: Get all cars with optional filtering
- **Query Parameters**: 
  - `make` (string): Filter by car make
  - `sort` (string): Sort order (price-asc, price-desc, rating-desc)
  - `limit` (integer): Limit results
- **Headers**: `Authorization: Bearer <token>`
- **Response**: `{success, cars, total}`
- **Status Codes**: 200 (OK)

**6. GET `/api/cars/{car_id}`**
- **Description**: Get specific car details
- **Path Parameters**: `car_id` (integer)
- **Headers**: `Authorization: Bearer <token>`
- **Response**: `{success, car}`
- **Status Codes**: 200 (OK), 404 (Not Found)

**7. POST `/api/cars`**
- **Description**: Create new car listing
- **Headers**: `Authorization: Bearer <token>`
- **Request Body**: `{make, model, year, price, currency, image_url, specs, ...}`
- **Response**: `{success, message, car_id}`
- **Status Codes**: 201 (Created), 400 (Bad Request)

**8. PATCH `/api/cars/{car_id}`**
- **Description**: Update car listing
- **Path Parameters**: `car_id` (integer)
- **Headers**: `Authorization: Bearer <token>`
- **Request Body**: `{make, model, price, ...}` (partial update)
- **Response**: `{success, message}`
- **Status Codes**: 200 (OK), 403 (Forbidden), 404 (Not Found)

**9. DELETE `/api/cars/{car_id}`**
- **Description**: Delete car listing
- **Path Parameters**: `car_id` (integer)
- **Headers**: `Authorization: Bearer <token>`
- **Response**: `{success, message}`
- **Status Codes**: 200 (OK), 403 (Forbidden), 404 (Not Found)

**10. GET `/api/my-listings`**
- **Description**: Get user's own listings
- **Headers**: `Authorization: Bearer <token>`
- **Response**: `{success, cars, total}`
- **Status Codes**: 200 (OK)

**11. GET `/api/makes`**
- **Description**: Get all unique car makes
- **Headers**: `Authorization: Bearer <token>`
- **Response**: `{success, makes}`
- **Status Codes**: 200 (OK)

### Favorites Endpoints

**12. GET `/api/favorites`**
- **Description**: Get user's favorite cars
- **Headers**: `Authorization: Bearer <token>`
- **Response**: `{success, cars}`
- **Status Codes**: 200 (OK)

**13. POST `/api/favorites`**
- **Description**: Add car to favorites
- **Headers**: `Authorization: Bearer <token>`
- **Request Body**: `{car_id}`
- **Response**: `{success, message}`
- **Status Codes**: 200 (OK), 400 (Bad Request)

**14. DELETE `/api/favorites/{car_id}`**
- **Description**: Remove car from favorites
- **Path Parameters**: `car_id` (integer)
- **Headers**: `Authorization: Bearer <token>`
- **Response**: `{success, message}`
- **Status Codes**: 200 (OK)

### Profile Management Endpoints

**15. GET `/api/profile`**
- **Description**: Get user profile information
- **Headers**: `Authorization: Bearer <token>`
- **Response**: `{success, profile: {id, username, email, created_at, last_login}}`
- **Status Codes**: 200 (OK), 404 (Not Found)

**16. PATCH `/api/profile`**
- **Description**: Update user profile
- **Headers**: `Authorization: Bearer <token>`
- **Request Body**: `{username?, email?, password?, current_password?}`
- **Response**: `{success, message}`
- **Status Codes**: 200 (OK), 400 (Bad Request)

### AI Features Endpoints

**17. POST `/api/chatbot`**
- **Description**: Chat with AI assistant
- **Headers**: `Authorization: Bearer <token>`
- **Request Body**: `{query, session_id?}`
- **Response**: `{success, response, intent, relevant_car_ids, message_id}`
- **Status Codes**: 200 (OK), 500 (Server Error)

**18. POST `/api/chatbot/rate`**
- **Description**: Rate chatbot response
- **Headers**: `Authorization: Bearer <token>`
- **Request Body**: `{message_id, rating (1-5), feedback?}`
- **Response**: `{success, message}`
- **Status Codes**: 200 (OK), 400 (Bad Request)

**19. POST `/api/listing-assistant`**
- **Description**: AI-powered listing assistant
- **Headers**: `Authorization: Bearer <token>`
- **Request Body**: `{query, session_id?}`
- **Response**: `{success, response, action_type, listing_data, message_id}`
- **Status Codes**: 200 (OK), 500 (Server Error)

**20. GET `/api/analytics/insights`**
- **Description**: Get AI-powered analytics
- **Headers**: `Authorization: Bearer <token>`
- **Query Parameters**: `filter` (all|my|favorites, default: all)
- **Response**: `{success, filter, user_stats, insights: {summary, top_makes, top_rated_cars, price_distribution, ai_insights}}`
- **Status Codes**: 200 (OK), 404 (Not Found)

### Utility Endpoints

**21. GET `/api/health`**
- **Description**: Health check endpoint
- **Response**: `{success, status, timestamp}`
- **Status Codes**: 200 (OK)

**22. GET `/api/swagger.json`**
- **Description**: OpenAPI/Swagger specification
- **Response**: OpenAPI 3.0 JSON specification
- **Status Codes**: 200 (OK)

**23. GET `/api-docs`**
- **Description**: Swagger UI interface
- **Response**: HTML page with interactive API documentation
- **Status Codes**: 200 (OK)

---

## Features and Functionality

### 1. User Authentication & Authorization
- User registration with validation
- Secure login with password hashing
- Session management with token-based authentication
- Token expiration (30 days)
- Session verification
- Logout functionality

### 2. Car Catalog Management
- Browse all car listings
- Search by make, model, or keywords
- Filter by car make
- Sort by price (ascending/descending) or rating
- View detailed car information
- Pagination support

### 3. User Listings Management
- Create new car listings
- Edit own listings (full CRUD)
- Delete own listings
- View all personal listings
- Ownership verification

### 4. Favorites System
- Add cars to favorites
- Remove from favorites
- View all favorite cars
- User-specific favorites

### 5. AI Chatbot
- Natural language car queries
- Intent detection (search, compare, general questions)
- Context-aware responses
- Integration with car database
- Response rating system
- Chat history management
- Multiple chat sessions

### 6. AI Listing Assistant
- Natural language listing creation
- Automatic data extraction from text
- Price suggestions based on market data
- Listing editing assistance
- Structured data generation
- Chat history with sessions

### 7. Analytics Dashboard
- Interactive data visualization
- Personalized analytics (All/My Listings/Favorites)
- AI-powered insights
- Summary statistics (total cars, makes, average price, rating)
- Top makes distribution with visual bars
- Price distribution charts
- Top rated cars list
- User-specific statistics

### 8. Profile Management
- View account information
- Update username
- Update email address
- Change password with verification
- View account creation date
- View last login timestamp
- Form validation and error handling

### 9. User Interface Features
- Responsive design (mobile, tablet, desktop)
- Dark theme with neon accents
- Glassmorphism effects
- Smooth animations and transitions
- Loading states
- Error handling with user-friendly messages
- Success notifications
- Modal dialogs
- Interactive cards
- Horizontal scrolling navigation

### 10. API Documentation
- Swagger UI integration
- Interactive API testing
- OpenAPI 3.0 specification
- Endpoint documentation
- Request/response schemas
- Authentication support in Swagger

---

## Architecture Overview

### System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (Browser)                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │  HTML    │  │   CSS    │  │    JS    │             │
│  │ (index)  │  │ (style)  │  │ (modules)│             │
│  └──────────┘  └──────────┘  └──────────┘             │
│       │             │             │                    │
│       └─────────────┴─────────────┘                    │
│                    │                                     │
│              HTTP/REST API                              │
└────────────────────┼─────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              Backend (Flask Server)                      │
│  ┌──────────────────────────────────────────┐           │
│  │         Flask Application (app.py)        │           │
│  │  - REST API Endpoints                    │           │
│  │  - Authentication Middleware             │           │
│  │  - Request Validation                   │           │
│  │  - Error Handling                       │           │
│  └──────────────────────────────────────────┘           │
│                    │                                     │
│       ┌────────────┴────────────┐                        │
│       │                        │                         │
│       ▼                        ▼                         │
│  ┌──────────┐          ┌──────────────┐                 │
│  │ SQLite   │          │  Gemini API  │                 │
│  │ Database │          │  (External)  │                 │
│  └──────────┘          └──────────────┘                 │
└─────────────────────────────────────────────────────────┘
```

### Data Flow

1. **User Request** → Frontend JavaScript
2. **API Call** → `api.js` makes HTTP request
3. **Backend Processing** → Flask route handler
4. **Authentication Check** → `@require_auth` decorator
5. **Database Query** → SQLite operations
6. **AI Processing** (if needed) → Gemini API call
7. **Response** → JSON data back to frontend
8. **UI Update** → JavaScript renders response

### Security Features

- Password hashing (SHA-256)
- Token-based authentication
- Session expiration
- CORS configuration
- Input validation
- SQL injection prevention (parameterized queries)
- Ownership verification for edits/deletes
- Secure token generation

---

## Dependencies

### Backend Dependencies (requirements.txt)
```
Flask==3.0.0
flask-cors==4.0.0
pandas==2.1.3
openpyxl==3.1.2
requests==2.31.0
flask-swagger-ui==5.21.0
```

### Frontend Dependencies
- **Tailwind CSS**: Via CDN (https://cdn.tailwindcss.com)
- **Google Fonts**: Inter, Space Grotesk
- **No npm/node_modules**: Pure vanilla JavaScript

### External Services
- **Google Gemini API**: 
  - Model: `gemini-2.0-flash`
  - Endpoint: `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent`
  - Used for: Chatbot, Listing Assistant, Analytics Insights

---

## Technical Specifications

### Frontend
- **Language**: JavaScript (ES6+)
- **Framework**: Vanilla JavaScript (no framework)
- **Styling**: Tailwind CSS + Custom CSS
- **State Management**: LocalStorage + In-memory state
- **Module System**: ES6 Modules
- **Browser Support**: Modern browsers (Chrome, Firefox, Safari, Edge)

### Backend
- **Language**: Python 3.x
- **Framework**: Flask 3.0.0
- **Database**: SQLite 3
- **API Style**: RESTful
- **Authentication**: Token-based (Bearer tokens)
- **Server**: Flask development server (can be deployed with Gunicorn/uWSGI)

### Database
- **Type**: SQLite (file-based)
- **File**: `intelliwheels.db`
- **Tables**: 7 tables
- **Relationships**: Foreign key constraints
- **Indexes**: Optimized for user_id and token lookups

---

## File Structure

```
IntelliWheels/
├── app.py                      # Flask backend (2583 lines)
├── requirements.txt            # Python dependencies
├── intelliwheels.db            # SQLite database
├── index.html                  # Main HTML file
├── css/
│   └── style.css              # Custom styles (1900+ lines)
├── js/
│   ├── main.js                # Main application logic (2300+ lines)
│   ├── api.js                 # API communication (400+ lines)
│   └── ui.js                  # UI rendering (800+ lines)
├── data/                      # Data files
├── components/                 # React components (separate)
└── [other files]
```

---

## API Summary Statistics

- **Total Endpoints**: 23
- **Authentication Endpoints**: 4
- **Car Management Endpoints**: 7
- **Favorites Endpoints**: 3
- **Profile Endpoints**: 2
- **AI Feature Endpoints**: 4
- **Utility Endpoints**: 3

---

## Security Measures

1. **Password Security**:
   - SHA-256 hashing
   - Minimum 6 characters
   - Current password verification for changes

2. **Authentication**:
   - Token-based sessions
   - 30-day expiration
   - Secure token generation

3. **Authorization**:
   - Ownership verification
   - Protected routes with decorators
   - User-specific data access

4. **Input Validation**:
   - Email format validation
   - Username uniqueness
   - Data type validation
   - SQL injection prevention

---

## Performance Optimizations

1. **Database**:
   - Indexes on frequently queried columns
   - Foreign key constraints
   - Efficient query patterns

2. **Frontend**:
   - Lazy loading images
   - Debounced search inputs
   - Batch DOM updates
   - GPU-accelerated animations

3. **API**:
   - Efficient database queries
   - Response caching (analytics)
   - Connection pooling

---

## Future Enhancements (Potential)

- User roles and permissions
- Image upload functionality
- Advanced search filters
- Email notifications
- Social sharing features
- Export functionality (PDF, Excel)
- Real-time notifications
- Multi-language support
- Advanced analytics charts
- API rate limiting

---

## Conclusion

IntelliWheels is a comprehensive, modern web application built with Flask and vanilla JavaScript. It provides a complete car catalog management system with AI-powered features, user authentication, and an intuitive interface. The system is well-structured, secure, and scalable, with proper separation of concerns between frontend, backend, and database layers.

**Total Lines of Code**: ~6,500+ lines
**Technologies Used**: 10+ major technologies
**API Endpoints**: 23 endpoints
**Database Tables**: 7 tables
**Features**: 10+ major features

---

**Report Generated**: 2024  
**System Status**: Production Ready

