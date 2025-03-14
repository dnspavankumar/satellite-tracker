from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from skyfield.api import load
import os

app = Flask(__name__, static_folder='static')
CORS(app)  # Enable cross-origin requests

# Cache TLE data to avoid frequent downloads
satellites_cache = None

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/api/satellites')
def get_satellites():
    global satellites_cache
    
    try:
        # Load TLE data (using cache if available)
        if satellites_cache is None:
            stations_url = 'https://celestrak.org/NORAD/elements/stations.txt'
            satellites_cache = load.tle_file(stations_url)
        
        # Return list of satellite names
        return jsonify([sat.name for sat in satellites_cache])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/position/<satellite_name>')
def get_position(satellite_name):
    global satellites_cache
    
    try:
        # Load TLE data if not already cached
        if satellites_cache is None:
            stations_url = 'https://celestrak.org/NORAD/elements/stations.txt'
            satellites_cache = load.tle_file(stations_url)
        
        # Find the specified satellite
        satellite = None
        for sat in satellites_cache:
            if sat.name == satellite_name:
                satellite = sat
                break
        
        if not satellite:
            return jsonify({"error": "Satellite not found"}), 404
        
        # Get the current time
        ts = load.timescale()
        current_time = ts.now()
        
        # Compute the satellite's position
        geocentric = satellite.at(current_time)
        subpoint = geocentric.subpoint()
        
        # Return position data
        return jsonify({
            "satellite": satellite.name,
            "latitude": subpoint.latitude.degrees,
            "longitude": subpoint.longitude.degrees,
            "altitude": subpoint.elevation.km
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Create static folder if it doesn't exist
    os.makedirs('static', exist_ok=True)
    
    # Save the HTML file to static/index.html
    with open('static/index.html', 'w') as f:
        f.write('''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Satellite Tracker</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            border-radius: 5px;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
        }
        h1 {
            text-align: center;
            color: #333;
        }
        select {
            width: 100%;
            padding: 10px;
            margin-bottom: 20px;
            border: 1px solid #ddd;
            border-radius: 4px;
        }
        button {
            background-color: #4CAF50;
            color: white;
            padding: 10px 15px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 16px;
            display: block;
            margin: 0 auto;
        }
        button:hover {
            background-color: #45a049;
        }
        #map {
            height: 400px;
            margin: 20px 0;
            border: 1px solid #ddd;
            border-radius: 4px;
        }
        .position-data {
            background-color: #f9f9f9;
            padding: 15px;
            border: 1px solid #ddd;
            border-radius: 4px;
            margin-top: 20px;
        }
        .position-data h2 {
            margin-top: 0;
            color: #333;
            border-bottom: 1px solid #ddd;
            padding-bottom: 10px;
        }
        .data-row {
            display: flex;
            padding: 8px 0;
        }
        .data-label {
            font-weight: bold;
            width: 120px;
        }
        .loading {
            text-align: center;
            margin: 20px 0;
            font-style: italic;
            color: #666;
        }
        #status-message {
            text-align: center;
            margin: 10px 0;
            padding: 10px;
            border-radius: 4px;
        }
        .success {
            background-color: #dff0d8;
            color: #3c763d;
        }
        .error {
            background-color: #f2dede;
            color: #a94442;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Satellite Tracker</h1>
        
        <div id="satellite-selection">
            <h2>Select Satellite</h2>
            <select id="satellite-select">
                <option value="">Loading satellites...</option>
            </select>
            <button id="track-button">Track Satellite</button>
        </div>
        
        <div id="status-message"></div>
        
        <div id="map"></div>
        
        <div id="position-data" class="position-data" style="display: none;">
            <h2>Satellite Position (Real-Time)</h2>
            <div class="data-row">
                <div class="data-label">Satellite:</div>
                <div id="satellite-name"></div>
            </div>
            <div class="data-row">
                <div class="data-label">Latitude:</div>
                <div id="latitude"></div>
            </div>
            <div class="data-row">
                <div class="data-label">Longitude:</div>
                <div id="longitude"></div>
            </div>
            <div class="data-row">
                <div class="data-label">Altitude:</div>
                <div id="altitude"></div>
            </div>
            <div class="data-row">
                <div class="data-label">Updated:</div>
                <div id="updated-time"></div>
            </div>
        </div>
    </div>

    <!-- Load Leaflet for map display -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.css" />
    
    <script>
        // Initialize map
        const map = L.map('map').setView([0, 0], 2);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        }).addTo(map);
        
        let satelliteMarker = null;
        let updateInterval = null;
        const statusMessage = document.getElementById('status-message');
        
        // Load available satellites
        async function loadSatellites() {
            try {
                statusMessage.className = '';
                statusMessage.textContent = 'Loading satellite data...';
                
                const response = await fetch('/api/satellites');
                const data = await response.json();
                
                const select = document.getElementById('satellite-select');
                select.innerHTML = '';
                
                // Add default option
                const defaultOption = document.createElement('option');
                defaultOption.value = '';
                defaultOption.textContent = 'Select a satellite...';
                select.appendChild(defaultOption);
                
                // Add all available satellites
                data.forEach(sat => {
                    const option = document.createElement('option');
                    option.value = sat;
                    option.textContent = sat;
                    select.appendChild(option);
                });
                
                statusMessage.className = 'success';
                statusMessage.textContent = 'Satellite data loaded successfully!';
            } catch (error) {
                statusMessage.className = 'error';
                statusMessage.textContent = `Error loading satellites: ${error.message}`;
                console.error('Error loading satellites:', error);
            }
        }
        
        // Track the selected satellite
        async function trackSatellite() {
            const satelliteName = document.getElementById('satellite-select').value;
            
            if (!satelliteName) {
                statusMessage.className = 'error';
                statusMessage.textContent = 'Please select a satellite to track';
                return;
            }
            
            // Clear any previous interval
            if (updateInterval) {
                clearInterval(updateInterval);
            }
            
            statusMessage.className = '';
            statusMessage.textContent = `Tracking ${satelliteName}...`;
            
            // Get initial position
            await updatePosition(satelliteName);
            
            // Update every 10 seconds
            updateInterval = setInterval(() => {
                updatePosition(satelliteName);
            }, 10000);
        }
        
        // Update the satellite position
        async function updatePosition(satelliteName) {
            try {
                const response = await fetch(`/api/position/${encodeURIComponent(satelliteName)}`);
                
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                
                const data = await response.json();
                
                // Update position display
                document.getElementById('satellite-name').textContent = data.satellite;
                document.getElementById('latitude').textContent = `${data.latitude.toFixed(6)}°`;
                document.getElementById('longitude').textContent = `${data.longitude.toFixed(6)}°`;
                document.getElementById('altitude').textContent = `${data.altitude.toFixed(2)} km`;
                document.getElementById('updated-time').textContent = new Date().toLocaleTimeString();
                
                // Show the position data section
                document.getElementById('position-data').style.display = 'block';
                
                // Update map
                updateMapMarker(data.latitude, data.longitude, data.satellite, data.altitude);
                
                // Update status
                statusMessage.className = 'success';
                statusMessage.textContent = `Successfully tracking ${data.satellite}`;
            } catch (error) {
                statusMessage.className = 'error';
                statusMessage.textContent = `Error tracking satellite: ${error.message}`;
                console.error('Error getting position:', error);
            }
        }
        
        // Update the map marker
        function updateMapMarker(lat, lon, name, altitude) {
            // Remove existing marker
            if (satelliteMarker) {
                map.removeLayer(satelliteMarker);
            }
            
            // Create new marker and add to map
            satelliteMarker = L.marker([lat, lon]).addTo(map);
            
            // Add popup with info
            satelliteMarker.bindPopup(`
                <b>${name}</b><br>
                Latitude: ${lat.toFixed(6)}°<br>
                Longitude: ${lon.toFixed(6)}°<br>
                Altitude: ${altitude.toFixed(2)} km
            `).openPopup();
            
            // Center map on satellite
            map.setView([lat, lon], 3);
        }
        
        // Event listeners
        document.addEventListener('DOMContentLoaded', function() {
            // Load satellites when page loads
            loadSatellites();
            
            // Set up track button
            document.getElementById('track-button').addEventListener('click', trackSatellite);
        });
    </script>
</body>
</html>''')
    
    print("Starting server. Access the app at http://localhost:5000")
    app.run(debug=True,host='0.0.0.0', port=5000)
