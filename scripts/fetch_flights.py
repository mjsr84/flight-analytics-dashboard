import pandas as pd
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from math import radians, cos, sin, sqrt, atan2
from pathlib import Path
from pyopensky.rest import REST

LOCAL_LAT = 42.347
LOCAL_LON = -123.438
RADIUS_MILES = 100

# Approximate degrees
lat_delta = RADIUS_MILES / 69
lon_delta = RADIUS_MILES / (69 *cos(radians(LOCAL_LAT)))

# Bounds
min_lat, max_lat = LOCAL_LAT - lat_delta, LOCAL_LAT + lat_delta
min_lon, max_lon = LOCAL_LON - lon_delta, LOCAL_LON + lon_delta

def haversine(lat1, lon1, lat2, lon2):
    # Calculates distance between two points when given lat/lon for each.
    R = 3958.8 # Earth's radius (miles)
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1))*cos(radians(lat2))*sin(dlon/2)**2
    c = 2*atan2(sqrt(a), sqrt(1 - a))
    return R * c 

# Initialize OpenSky API
api = REST()

# Fetch all live states
flights_df = api.states()

# Drop rows with missing coordinates
flights_df = flights_df.dropna(subset=['latitude', 'longitude'])

# Calculate distance from set location
flights_df['distance_miles'] = flights_df.apply(
    lambda row: haversine(LOCAL_LAT, LOCAL_LON, row ['latitude'], row['longitude']), axis=1
).round()
flights_df['groundspeed_mph'] = (flights_df['groundspeed'] * 2.237).round()
flights_df['geoaltitude_ft'] = (flights_df['geoaltitude'] * 3.281).round()

# Filter for flights within set radius
local_flights = flights_df[flights_df['distance_miles'] <= RADIUS_MILES]

# Keep select columns
columns_to_keep = [
    'icao24', 'callsign', 'origin_country', 'longitude', 'latitude',
    'geoaltitude_ft', 'groundspeed_mph', 'distance_miles', 'timestamp'
]
local_flights = local_flights[columns_to_keep]

# Save to CSV for Tableau
local_flights.to_csv('../data/processed/flights_local.csv', index=False)

print(f"Total flights overhead withing (~{RADIUS_MILES} miles): {len(local_flights)}")
print(local_flights.sort_values('distance_miles'))
print(local_flights.describe())
print(local_flights.shape)
print(flights_df.dtypes)
