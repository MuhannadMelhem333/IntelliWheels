/**
 * Script to add latitude/longitude to existing cars in the database
 * Run this once to populate location data for existing cars
 */

import sqlite3
import random

# Major cities with their coordinates
MAJOR_CITIES = [
    (40.7128, -74.0060),   # New York
    (51.5074, -0.1278),     # London
    (35.6762, 139.6503),   # Tokyo
    (48.8566, 2.3522),     # Paris
    (52.5200, 13.4050),    # Berlin
    (25.2048, 55.2708),    # Dubai
    (-33.8688, 151.2093),  # Sydney
    (37.7749, -122.4194),  # San Francisco
    (34.0522, -118.2437),  # Los Angeles
    (41.9028, 12.4964),    # Rome
    (55.7558, 37.6173),    # Moscow
    (19.4326, -99.1332),   # Mexico City
    (-23.5505, -46.6333),  # São Paulo
    (39.9042, 116.4074),    # Beijing
    (22.3193, 114.1694),   # Hong Kong
]

# Car make to city mapping (optional, for more realistic distribution)
MAKE_LOCATIONS = {
    'BMW': (48.1351, 11.5820),  # Munich
    'Mercedes-Benz': (48.7758, 9.1829),  # Stuttgart
    'Audi': (48.7758, 9.1829),  # Ingolstadt
    'Toyota': (35.6762, 139.6503),  # Tokyo
    'Honda': (35.6762, 139.6503),  # Tokyo
    'Nissan': (35.6762, 139.6503),  # Tokyo
    'Ford': (42.3314, -83.0458),  # Detroit
    'Chevrolet': (42.3314, -83.0458),  # Detroit
    'Tesla': (37.7749, -122.4194),  # San Francisco
    'Porsche': (48.7758, 9.1829),  # Stuttgart
    'Ferrari': (44.6471, 10.9252),  # Maranello
    'Lamborghini': (44.6471, 10.9252),  # Sant'Agata
    'McLaren': (51.5074, -0.1278),  # London
    'Jaguar': (52.4862, -1.8904),  # Coventry
    'Land Rover': (52.4862, -1.8904),  # Solihull
}

def add_locations_to_cars():
    """Add latitude/longitude to cars that don't have them"""
    conn = sqlite3.connect('intelliwheels.db')
    cursor = conn.cursor()
    
    # Check if columns exist, if not add them
    try:
        cursor.execute('ALTER TABLE cars ADD COLUMN latitude REAL')
        cursor.execute('ALTER TABLE cars ADD COLUMN longitude REAL')
        print("Added latitude/longitude columns to cars table")
    except sqlite3.OperationalError as e:
        if 'duplicate column' in str(e).lower():
            print("Columns already exist")
        else:
            raise
    
    # Get all cars without locations
    cursor.execute('SELECT id, make FROM cars WHERE latitude IS NULL OR longitude IS NULL')
    cars = cursor.fetchall()
    
    print(f"Found {len(cars)} cars without locations")
    
    # Assign locations
    for car_id, make in cars:
        # Try to get location from make
        if make and make.upper() in MAKE_LOCATIONS:
            lat, lon = MAKE_LOCATIONS[make.upper()]
        else:
            # Use deterministic assignment based on car ID
            city_index = car_id % len(MAJOR_CITIES)
            lat, lon = MAJOR_CITIES[city_index]
        
        cursor.execute(
            'UPDATE cars SET latitude = ?, longitude = ? WHERE id = ?',
            (lat, lon, car_id)
        )
    
    conn.commit()
    conn.close()
    
    print(f"Successfully added locations to {len(cars)} cars")

if __name__ == '__main__':
    add_locations_to_cars()
    print("Done! Cars now have location data.")

