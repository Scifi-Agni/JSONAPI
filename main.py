from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import sqlite3
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

app = FastAPI()

# SQLite database configuration
conn = sqlite3.connect('addresses.db')
cursor = conn.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS addresses (id INTEGER PRIMARY KEY, name TEXT, address TEXT, latitude REAL, longitude REAL)')
conn.commit()

# Address model
class Address(BaseModel):
    name: str
    address: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None

# Function to validate address
def validate_address(address):
    geolocator = Nominatim(user_agent='address_book')
    try:
        location = geolocator.geocode(address)
        if location:
            return (location.latitude, location.longitude)
        else:
            return None
    except:
        return None

# API route to add a new address
@app.post('/addresses', status_code=201)
async def add_address(address: Address):
    coordinates = validate_address(address.address)
    if not coordinates:
        raise HTTPException(status_code=400, detail='Invalid address')
    cursor.execute('INSERT INTO addresses (name, address, latitude, longitude) VALUES (?, ?, ?, ?)', (address.name, address.address, coordinates[0], coordinates[1]))
    conn.commit()
    return {'message': 'Address added successfully'}

# API route to update an address
@app.put('/addresses/{id}')
async def update_address(id: int, address: Address):
    coordinates = validate_address(address.address)
    if not coordinates:
        raise HTTPException(status_code=400, detail='Invalid address')
    cursor.execute('UPDATE addresses SET name=?, address=?, latitude=?, longitude=? WHERE id=?', (address.name, address.address, coordinates[0], coordinates[1], id))
    conn.commit()
    return {'message': 'Address updated successfully'}

# API route to delete an address
@app.delete('/addresses/{id}')
async def delete_address(id: int):
    cursor.execute('DELETE FROM addresses WHERE id=?', (id,))
    conn.commit()
    return {'message': 'Address deleted successfully'}

# API route to retrieve addresses within a given distance and location coordinates
@app.get('/addresses')
async def get_addresses(latitude: float, longitude: float, distance: float):
    cursor.execute('SELECT * FROM addresses')
    rows = cursor.fetchall()
    addresses = []
    for row in rows:
        coords = (row[3], row[4])
        if geodesic(coords, (latitude, longitude)).km <= distance:
            addresses.append({'id': row[0], 'name': row[1], 'address': row[2], 'latitude': row[3], 'longitude': row[4]})
    return {'addresses': addresses}
