# Integration Guide: Adding CarGlobe to IntelliWheels

This guide explains how to integrate the React CarGlobe component into your existing vanilla JavaScript IntelliWheels project.

## Option 1: Standalone React App (Recommended)

Create a separate React app for the globe feature and link to it from your main app.

### Steps:

1. **Create React app in a subdirectory:**
```bash
cd IntelliWheels
mkdir globe-viewer
cd globe-viewer
npm create vite@latest . -- --template react
npm install @react-three/fiber @react-three/drei three
```

2. **Copy component files:**
   - Copy `CarGlobe.jsx` to `globe-viewer/src/components/`
   - Copy `CarGlobeDemo.jsx` to `globe-viewer/src/`

3. **Update `globe-viewer/src/main.jsx`:**
```jsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import CarGlobeDemo from './CarGlobeDemo';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')).render(
    <React.StrictMode>
        <CarGlobeDemo />
    </React.StrictMode>
);
```

4. **Run the React app:**
```bash
cd globe-viewer
npm run dev
```

5. **Add link in your main app (`index.html`):**
```html
<button id="nav-globe" class="nav-button">Globe View</button>
```

6. **Add JavaScript to open globe:**
```javascript
document.getElementById('nav-globe').addEventListener('click', () => {
    window.open('http://localhost:3000', '_blank');
});
```

## Option 2: Fetch Car Data from API

Modify `CarGlobeDemo.jsx` to fetch cars from your Flask API:

```jsx
import { useState, useEffect } from 'react';

function CarGlobeDemo() {
    const [cars, setCars] = useState([]);
    const [loading, setLoading] = useState(true);
    
    useEffect(() => {
        // Fetch cars from your API
        fetch('http://localhost:5000/api/cars')
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    // Transform API data to CarGlobe format
                    const transformedCars = data.cars.map(car => ({
                        id: car.id,
                        name: `${car.make} ${car.model}`,
                        price: car.price,
                        currency: car.currency || 'USD',
                        image: car.image || car.image_url,
                        // You'll need to add lat/lon to your car data
                        latitude: car.latitude || getRandomLat(),
                        longitude: car.longitude || getRandomLon(),
                    }));
                    setCars(transformedCars);
                }
                setLoading(false);
            })
            .catch(err => {
                console.error('Error fetching cars:', err);
                setLoading(false);
            });
    }, []);
    
    if (loading) {
        return <div>Loading...</div>;
    }
    
    return (
        <div className="w-full h-screen">
            <div className="w-full h-[600px]">
                <CarGlobe cars={cars} />
            </div>
        </div>
    );
}
```

## Option 3: Add Latitude/Longitude to Database

To properly plot cars on the globe, you need latitude/longitude data:

### Update Database Schema

Add to `app.py`:

```python
# In init_db(), add columns to cars table:
cursor.execute('''
    ALTER TABLE cars ADD COLUMN latitude REAL;
    ALTER TABLE cars ADD COLUMN longitude REAL;
''')
```

### Add Location Data

Create a script to add locations based on car make/model or other criteria:

```python
# add_locations.py
import sqlite3
import random

conn = sqlite3.connect('intelliwheels.db')
cursor = conn.cursor()

# Example: Assign random locations (replace with real data)
cities = [
    (40.7128, -74.0060),   # New York
    (51.5074, -0.1278),    # London
    (35.6762, 139.6503),   # Tokyo
    # ... more cities
]

cursor.execute('SELECT id FROM cars WHERE latitude IS NULL')
cars = cursor.fetchall()

for car_id, in cars:
    lat, lon = random.choice(cities)
    cursor.execute('UPDATE cars SET latitude = ?, longitude = ? WHERE id = ?', 
                   (lat, lon, car_id))

conn.commit()
conn.close()
```

## Option 4: Use Vanilla JavaScript Version

If you prefer not to use React, you can create a vanilla JavaScript version using Three.js directly. This would require:

1. Include Three.js via CDN
2. Create a similar component structure in vanilla JS
3. Integrate directly into your existing `index.html`

Would you like me to create a vanilla JavaScript version instead?

## Testing

1. **Start Flask backend:**
```bash
python app.py
```

2. **Start React app:**
```bash
cd globe-viewer
npm run dev
```

3. **Open browser:**
Navigate to `http://localhost:3000` to see the globe

## Production Build

To build for production:

```bash
cd globe-viewer
npm run build
```

This creates a `dist` folder that can be served statically or integrated into your Flask app.

## Deploying

### Option A: Static Hosting
Upload the `dist` folder to any static hosting service (Netlify, Vercel, etc.)

### Option B: Flask Integration
Serve the React build from Flask:

```python
# In app.py
@app.route('/globe')
def globe():
    return send_from_directory('globe-viewer/dist', 'index.html')

@app.route('/globe/<path:path>')
def globe_static(path):
    return send_from_directory('globe-viewer/dist', path)
```

Then access at `http://localhost:5000/globe`

