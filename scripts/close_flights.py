import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
from pyopensky.rest import REST
from math import radians, cos, sin, sqrt, atan2

# Location for filtering
try:
    LOCAL_LAT = float(input("Enter latitude (e.g., 42.347 for Glide, OR): "))
    LOCAL_LON = float(input("Enter longitude (e.g., -123.438 for Glide, OR): "))
except ValueError:
    print("Invalid input. Using default location: Glide, OR")
    LOCAL_LAT = 42.347
    LOCAL_LON = -123.438

try:
    RADIUS_MILES = float(input("Enter radius in miles to filter flights: "))
except ValueError:
    RADIUS_MILES = 100

# Haversine distance function
def haversine(lat1, lon1, lat2, lon2):
    R = 3958.8 # Earth radius in miles
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1))*cos(radians(lat2))*sin(dlon/2)**2
    c = 2*atan2(sqrt(a)), sqrt(1-a)
    return R * c

# Fetch and process flights
def fetch_local_flights():
    api = REST()
    df = api.states()

    # Drop flights without position information
    df = df.dropna(subset=['latitude', 'longitude'])

    # Distance from specified location
    df['distance_miles'] = df.apply(
        lambda row: haversine(LOCAL_LAT, LOCAL_LON, row['latitude'], row['longitude']),
        axis=1
    )

    # Filter by radius
    local = df[df['distance_miles'] <= RADIUS_MILES]

    # Convert units
    if 'groundspeed' in local.columns:
        local['groundspeed_mph'] = local['groundspeed'] * 2.237
        local['groundspeed_mph'] = local['groundspeed_mph'].round(1)
    if 'geoaltitude' in local.columns:
        local['geoaltitude_ft'] = local['geoaltitude'] * 3.28084
        local['geoaltitude_ft'] = local['geoaltitude_ft'].round(0)

    return local

# Initialize dash
app = dash.Dash(__name__)
app.title = "Local Flight Dashboard"

app.layout = html.Div([
    html.H1("Live Flights over Your Location"),
    html.Button("Refresh Data", id='refresh-button', n_clicks=0, style={'margin-bottom': '10px'}),
    dcc.Graph(id='flight-map'),
    html.Div(id='flight-summary', style={'margin-top': '10px', 'font-size': '16px'})
])

# Update callback
@app.callback(
    Output('flight-map', 'figure'),
    Output('flight-summary', 'children'),
    Input('refresh-button', 'n_clicks')
)
def update_dashboard(n_clicks):
    flights = fetch_local_flights()
    if flights.empty:
        summary = "No flights in the selected area at the moment."
        fig = px.scatter_mapbox(lat=[], lon=[], zoom=8, height=600)
        fig.update_layout(mapbox_style="open-street-map")
        return fig, summary
    
    # Map
    fig = px.scatter_mapbox(
        flights,
        lat='latitude',
        lon='longitude',
        color='geoaltitude_ft' if 'geoaltitude_ft' in flights.columns else None,
        size='groundspeed_mph'if 'groundspeed_mph' in flights.columns else None,
        hover_data=['callsign', 'origin_country', 'geoaltitude_ft', 'groundspeed_mph'],
        zoom=8,
        height=600
    )
    fig.update_layout(mapbox_style="open-street-map")

    # Summary
    avg_alt = flights['geoaltitude_ft'].mean() if 'geoaltitude_ft' in flights.columns else 0
    avg_mph = flights['groundspeed_mph'].mean() if 'groundspeed_mph' in flights.columns else 0
    summary = f"Flights overhead: {len(flights)} | Avg Altitude: {avg_alt:.0f} ft | Avg Speed: {avg_mph:.0f} mph"

    return fig, summary

# Run server
if __name__ == "__main__":
    app.run(debug=False)