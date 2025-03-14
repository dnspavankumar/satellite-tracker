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
        :root {
            --bg-primary: #121212;
            --bg-secondary: #1e1e1e;
            --bg-tertiary: #2d2d2d;
            --text-primary: #ffffff;
            --text-secondary: #b0b0b0;
            --accent: #00b4d8;
            --accent-hover: #48cae4;
            --danger: #e63946;
            --success: #2a9d8f;
            --transition: all 0.3s ease;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.6;
            min-height: 100vh;
            padding: 0;
            margin: 0;
        }
        
        .container {
            max-width: 1100px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 1px solid var(--bg-tertiary);
            position: relative;
        }
        
        .header h1 {
            font-size: 2.5rem;
            font-weight: 300;
            letter-spacing: 1px;
            margin: 0;
            color: var(--text-primary);
            display: inline-block;
        }
        
        .header h1 span {
            color: var(--accent);
            font-weight: 600;
        }
        
        .card {
            background-color: var(--bg-secondary);
            border-radius: 8px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
            margin-bottom: 25px;
            overflow: hidden;
            transition: var(--transition);
            animation: fadeIn 0.5s ease;
        }
        
        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 20px rgba(0, 0, 0, 0.3);
        }
        
        .card-header {
            padding: 18px 25px;
            display: flex;
            align-items: center;
            border-bottom: 1px solid var(--bg-tertiary);
        }
        
        .card-header h2 {
            font-size: 1.4rem;
            font-weight: 500;
            margin: 0;
            color: var(--text-primary);
        }
        
        .card-body {
            padding: 25px;
        }
        
        select {
            width: 100%;
            padding: 12px 15px;
            background-color: var(--bg-tertiary);
            color: var(--text-primary);
            border: none;
            border-radius: 6px;
            font-size: 1rem;
            margin-bottom: 20px;
            appearance: none;
            cursor: pointer;
            transition: var(--transition);
        }
        
        select:focus {
            outline: none;
            box-shadow: 0 0 0 2px var(--accent);
        }
        
        button {
            background-color: var(--accent);
            color: white;
            padding: 12px 24px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 1rem;
            transition: var(--transition);
            display: inline-flex;
            align-items: center;
            justify-content: center;
        }
        
        button:hover {
            background-color: var(--accent-hover);
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        }
        
        button:active {
            transform: translateY(0);
        }
        
        #map {
            height: 400px;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.15);
        }
        
        .map-container {
            position: relative;
        }
        
        .data-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
        }
        
        .data-item {
            padding: 15px;
            background-color: var(--bg-tertiary);
            border-radius: 6px;
            transition: var(--transition);
        }
        
        .data-item:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        }
        
        .data-label {
            font-size: 0.85rem;
            color: var(--text-secondary);
            margin-bottom: 5px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .data-value {
            font-size: 1.2rem;
            font-weight: 500;
            color: var(--text-primary);
        }
        
        #status-message {
            text-align: center;
            margin: 15px 0;
            padding: 10px 15px;
            border-radius: 6px;
            font-size: 0.95rem;
            transition: var(--transition);
            opacity: 0;
            height: 0;
            overflow: hidden;
        }
        
        #status-message.visible {
            opacity: 1;
            height: auto;
            margin: 15px 0;
            padding: 10px 15px;
        }
        
        .success {
            background-color: rgba(42, 157, 143, 0.15);
            color: var(--success);
            border-left: 4px solid var(--success);
        }
        
        .error {
            background-color: rgba(230, 57, 70, 0.15);
            color: var(--danger);
            border-left: 4px solid var(--danger);
        }
        
        .info {
            background-color: rgba(0, 180, 216, 0.15);
            color: var(--accent);
            border-left: 4px solid var(--accent);
        }
        
        .pulse {
            animation: pulse 2s infinite;
            position: absolute;
            bottom: 20px;
            right: 20px;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background-color: var(--success);
        }
        
        @keyframes pulse {
            0% {
                transform: scale(0.95);
                box-shadow: 0 0 0 0 rgba(42, 157, 143, 0.7);
            }
            
            70% {
                transform: scale(1);
                box-shadow: 0 0 0 10px rgba(42, 157, 143, 0);
            }
            
            100% {
                transform: scale(0.95);
                box-shadow: 0 0 0 0 rgba(42, 157, 143, 0);
            }
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .satellite-icon {
            display: inline-block;
            margin-right: 10px;
            width: 24px;
            height: 24px;
        }
        
        .loading {
            display: inline-block;
            width: 20px;
            height: 20px;
            margin-right: 10px;
            border: 3px solid rgba(255, 255, 255, 0.3);
            border-radius: 50%;
            border-top-color: #fff;
            animation: spin 1s ease-in-out infinite;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        /* Custom leaflet styling for dark theme */
        .leaflet-container {
            background-color: #1a1a1a !important;
        }
        
        .leaflet-popup-content-wrapper, .leaflet-popup-tip {
            background-color: var(--bg-secondary) !important;
            color: var(--text-primary) !important;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3) !important;
        }
        
        .troubleshoot-panel {
            background-color: var(--bg-tertiary);
            border-radius: 6px;
            padding: 15px;
            margin-top: 15px;
            border-left: 4px solid var(--accent);
            display: none;
        }
        
        .troubleshoot-panel h3 {
            color: var(--accent);
            margin-bottom: 10px;
        }
        
        .troubleshoot-panel ul {
            padding-left: 20px;
        }
        
        .troubleshoot-panel li {
            margin-bottom: 8px;
        }
        
        .troubleshoot-button {
            background-color: transparent;
            color: var(--accent);
            padding: 5px 10px;
            border: 1px solid var(--accent);
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.9rem;
            margin-top: 10px;
            transition: var(--transition);
        }
        
        .troubleshoot-button:hover {
            background-color: rgba(0, 180, 216, 0.1);
        }
        
        .settings-panel {
            margin-top: 15px;
            padding: 15px;
            background-color: var(--bg-tertiary);
            border-radius: 6px;
        }
        
        .settings-title {
            display: flex;
            align-items: center;
            margin-bottom: 15px;
            color: var(--text-primary);
            font-size: 1.1rem;
            font-weight: 500;
        }
        
        .settings-group {
            margin-bottom: 15px;
        }
        
        .settings-label {
            display: block;
            margin-bottom: 8px;
            color: var(--text-secondary);
            font-size: 0.9rem;
        }
        
        .settings-input {
            width: 100%;
            padding: 10px;
            background-color: var(--bg-primary);
            color: var(--text-primary);
            border: 1px solid var(--bg-tertiary);
            border-radius: 4px;
            font-size: 0.9rem;
        }
        
        .settings-input:focus {
            outline: none;
            border-color: var(--accent);
        }
        
        .settings-actions {
            display: flex;
            justify-content: flex-end;
            margin-top: 15px;
        }
        
        .settings-save {
            background-color: var(--accent);
            color: white;
            padding: 8px 15px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.9rem;
        }
        
        .tooltip {
            position: relative;
            display: inline-block;
            cursor: help;
            margin-left: 5px;
        }
        
        .tooltip .tooltip-text {
            visibility: hidden;
            width: 200px;
            background-color: var(--bg-primary);
            color: var(--text-primary);
            text-align: center;
            border-radius: 4px;
            padding: 5px;
            position: absolute;
            z-index: 1;
            bottom: 125%;
            left: 50%;
            margin-left: -100px;
            opacity: 0;
            transition: opacity 0.3s;
            font-size: 0.8rem;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
        }
        
        .tooltip:hover .tooltip-text {
            visibility: visible;
            opacity: 1;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1><span>Satellite</span> Tracker</h1>
            <div id="live-indicator" class="pulse" style="display: none;"></div>
        </div>
        
        <div class="card">
            <div class="card-header">
                <svg class="satellite-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M3.6 9l1.5 1.5M21 9l-1.5 1.5M9 3.6L10.5 5M14.2 3.6L12.7 5M12 14l1.5 1.5M10.5 15.5L12 17M18.4 12l-1.5 1.5M16.9 10.5L15.4 12M6 12l-1.5 1.5M7.5 10.5L6 12M12 6l-1.5 1.5M13.5 7.5L12 6"></path>
                    <circle cx="12" cy="12" r="3"></circle>
                </svg>
                <h2>Select Satellite</h2>
            </div>
            <div class="card-body">
                <select id="satellite-select">
                    <option value="">Loading satellites...</option>
                </select>
                <button id="track-button">
                    <span id="button-text">Track Satellite</span>
                </button>
                
                <div id="troubleshoot-panel" class="troubleshoot-panel">
                    <h3>Connection Troubleshooting</h3>
                    <ul>
                        <li>Ensure the Flask server is running at the API base URL</li>
                        <li>Check the console for detailed error messages</li>
                        <li>Verify there are no CORS issues with your API</li>
                    </ul>
                    <div class="settings-panel">
                        <div class="settings-title">
                            <svg class="satellite-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                <circle cx="12" cy="12" r="3"></circle>
<path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
</svg>
                            API Settings
                        </div>
                        <div class="settings-group">
                            <label class="settings-label">API Base URL
                                <span class="tooltip">?
                                    <span class="tooltip-text">The base URL of your Flask API server</span>
                                </span>
                            </label>
                            <input type="text" id="api-url" class="settings-input" value="http://localhost:5000">
                        </div>
                        <div class="settings-group">
                            <label class="settings-label">Update Interval (seconds)
                                <span class="tooltip">?
                                    <span class="tooltip-text">How often to update satellite positions</span>
                                </span>
                            </label>
                            <input type="number" id="update-interval" class="settings-input" value="10" min="1" max="60">
                        </div>
                        <div class="settings-actions">
                            <button class="settings-save" id="save-settings">Save Settings</button>
                        </div>
                    </div>
                </div>
                
                <button id="troubleshoot-button" class="troubleshoot-button">Show Connection Settings</button>
                
                <div id="status-message" class="info">
                    Loading satellite data...
                </div>
            </div>
        </div>
        
        <div class="card">
            <div class="card-header">
                <svg class="satellite-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="12" cy="10" r="3"></circle>
                    <path d="M12 1v2"></path>
                    <path d="M12 17v2"></path>
                    <path d="M5 10H3"></path>
                    <path d="m7.5 5 1.5 1.5"></path>
                    <path d="M16.5 5 15 6.5"></path>
                    <path d="M21 10h-2"></path>
                    <path d="M7.5 15 6 16.5"></path>
                    <path d="m16.5 15-1.5 1.5"></path>
                    <path d="M18 2h2v2"></path>
                    <path d="M4 2H2v2"></path>
                    <path d="M22 18h-2v2"></path>
                    <path d="M4 18H2v2"></path>
                </svg>
                <h2>Satellite Position</h2>
            </div>
            <div class="card-body">
                <div id="map"></div>
                <div class="data-grid" style="margin-top: 20px;">
                    <div class="data-item">
                        <div class="data-label">Latitude</div>
                        <div class="data-value" id="latitude">-</div>
                    </div>
                    <div class="data-item">
                        <div class="data-label">Longitude</div>
                        <div class="data-value" id="longitude">-</div>
                    </div>
                    <div class="data-item">
                        <div class="data-label">Altitude</div>
                        <div class="data-value" id="altitude">-</div>
                    </div>
                    <div class="data-item">
                        <div class="data-label">Last Update</div>
                        <div class="data-value" id="last-update">-</div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/leaflet.css" />
    <script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/leaflet.js"></script>
    
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            // DOM Elements
            const satelliteSelect = document.getElementById('satellite-select');
            const trackButton = document.getElementById('track-button');
            const buttonText = document.getElementById('button-text');
            const statusMessage = document.getElementById('status-message');
            const liveIndicator = document.getElementById('live-indicator');
            const troubleshootButton = document.getElementById('troubleshoot-button');
            const troubleshootPanel = document.getElementById('troubleshoot-panel');
            const saveSettingsButton = document.getElementById('save-settings');
            const apiUrlInput = document.getElementById('api-url');
            const updateIntervalInput = document.getElementById('update-interval');
            
            // Position data elements
            const latitudeElement = document.getElementById('latitude');
            const longitudeElement = document.getElementById('longitude');
            const altitudeElement = document.getElementById('altitude');
            const lastUpdateElement = document.getElementById('last-update');
            
            // Settings
            let apiBaseUrl = localStorage.getItem('apiBaseUrl') || 'http://localhost:5000';
            let updateInterval = parseInt(localStorage.getItem('updateInterval') || '10');
            
            // Initialize settings inputs
            apiUrlInput.value = apiBaseUrl;
            updateIntervalInput.value = updateInterval;
            
            // Map setup
            let map = L.map('map', {
                worldCopyJump: true,
                minZoom: 2
            }).setView([0, 0], 2);
            
            // Use a dark map tile layer
            L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
                attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
                subdomains: 'abcd',
                maxZoom: 19
            }).addTo(map);
            
            // Initialize satellite marker
            let satelliteMarker = null;
            let satelliteTrail = [];
            let trailPolyline = null;
            
            // Update interval ID
            let updateIntervalId = null;
            
            // Initialize Leaflet map
            function initMap() {
                map.invalidateSize();
            }
            
            // Show status message
            function showStatus(message, type = 'info') {
                statusMessage.textContent = message;
                statusMessage.className = type + ' visible';
                
                setTimeout(() => {
                    statusMessage.classList.remove('visible');
                }, 5000);
            }
            
            // Load satellite data
            async function loadSatellites() {
                try {
                    showStatus('Loading satellite data...', 'info');
                    
                    const response = await fetch(`${apiBaseUrl}/api/satellites`);
                    if (!response.ok) {
                        throw new Error(`Failed to load satellites: ${response.status} ${response.statusText}`);
                    }
                    
                    const satellites = await response.json();
                    
                    // Clear and populate the select
                    satelliteSelect.innerHTML = '';
                    
                    if (satellites.length === 0) {
                        const option = document.createElement('option');
                        option.value = '';
                        option.textContent = 'No satellites available';
                        satelliteSelect.appendChild(option);
                    } else {
                        const defaultOption = document.createElement('option');
                        defaultOption.value = '';
                        defaultOption.textContent = 'Select a satellite';
                        satelliteSelect.appendChild(defaultOption);
                        
                        satellites.forEach(satellite => {
                            const option = document.createElement('option');
                            option.value = satellite;
                            option.textContent = satellite;
                            satelliteSelect.appendChild(option);
                        });
                    }
                    
                    showStatus('Satellite data loaded successfully', 'success');
                } catch (error) {
                    console.error('Error loading satellites:', error);
                    showStatus(`Failed to load satellites: ${error.message}`, 'error');
                    
                    // Show troubleshooting panel
                    troubleshootPanel.style.display = 'block';
                    troubleshootButton.textContent = 'Hide Connection Settings';
                }
            }
            
            // Track satellite
            async function trackSatellite() {
                const selectedSatellite = satelliteSelect.value;
                
                if (!selectedSatellite) {
                    showStatus('Please select a satellite', 'error');
                    return;
                }
                
                try {
                    // Change button state
                    buttonText.innerHTML = '<span class="loading"></span> Tracking...';
                    trackButton.disabled = true;
                    
                    // Fetch satellite position
                    const response = await fetch(`${apiBaseUrl}/api/position/${encodeURIComponent(selectedSatellite)}`);
                    if (!response.ok) {
                        throw new Error(`Failed to get satellite position: ${response.status} ${response.statusText}`);
                    }
                    
                    const positionData = await response.json();
                    
                    // Update position display
                    updatePositionDisplay(positionData);
                    
                    // Setup interval for continuous updates
                    if (updateIntervalId) {
                        clearInterval(updateIntervalId);
                    }
                    
                    updateIntervalId = setInterval(() => {
                        updateSatellitePosition(selectedSatellite);
                    }, updateInterval * 1000);
                    
                    // Show live indicator
                    liveIndicator.style.display = 'block';
                    
                    // Reset button state
                    buttonText.textContent = 'Tracking Active';
                    trackButton.disabled = false;
                    
                    showStatus(`Now tracking ${selectedSatellite}`, 'success');
                } catch (error) {
                    console.error('Error tracking satellite:', error);
                    showStatus(`Failed to track satellite: ${error.message}`, 'error');
                    
                    // Reset button state
                    buttonText.textContent = 'Track Satellite';
                    trackButton.disabled = false;
                }
            }
            
            // Update satellite position
            async function updateSatellitePosition(satellite) {
                try {
                    const response = await fetch(`${apiBaseUrl}/api/position/${encodeURIComponent(satellite)}`);
                    if (!response.ok) {
                        throw new Error('Failed to update satellite position');
                    }
                    
                    const positionData = await response.json();
                    updatePositionDisplay(positionData);
                } catch (error) {
                    console.error('Error updating satellite position:', error);
                    showStatus('Failed to update satellite position', 'error');
                    
                    // Stop tracking if connection fails
                    clearInterval(updateIntervalId);
                    liveIndicator.style.display = 'none';
                    buttonText.textContent = 'Track Satellite';
                }
            }
            
            // Update position display
            function updatePositionDisplay(positionData) {
                const { latitude, longitude, altitude, satellite } = positionData;
                
                // Update text displays
                latitudeElement.textContent = latitude.toFixed(4) + '°';
                longitudeElement.textContent = longitude.toFixed(4) + '°';
                altitudeElement.textContent = altitude.toFixed(1) + ' km';
                lastUpdateElement.textContent = new Date().toLocaleTimeString();
                
                // Update marker on map
                const position = [latitude, longitude];
                
                if (!satelliteMarker) {
                    // Create marker if it doesn't exist
                    satelliteMarker = L.marker(position).addTo(map);
                    satelliteMarker.bindPopup(`<b>${satellite}</b><br>Alt: ${altitude.toFixed(1)} km`);
                    
                    // Center map on marker
                    map.setView(position, 3);
                } else {
                    // Update existing marker
                    satelliteMarker.setLatLng(position);
                    satelliteMarker.bindPopup(`<b>${satellite}</b><br>Alt: ${altitude.toFixed(1)} km`);
                }
                
                // Add position to trail
                satelliteTrail.push(position);
                
                // Limit trail length
                if (satelliteTrail.length > 20) {
                    satelliteTrail.shift();
                }
                
                // Update trail polyline
                if (trailPolyline) {
                    trailPolyline.removeFrom(map);
                }
                
                trailPolyline = L.polyline(satelliteTrail, {
                    color: '#00b4d8',
                    weight: 2,
                    opacity: 0.6
                }).addTo(map);
            }
            
            // Save settings
            function saveSettings() {
                const newApiBaseUrl = apiUrlInput.value.trim();
                const newUpdateInterval = parseInt(updateIntervalInput.value);
                
                if (!newApiBaseUrl) {
                    showStatus('API Base URL cannot be empty', 'error');
                    return;
                }
                
               if (isNaN(newUpdateInterval) || newUpdateInterval < 1 || newUpdateInterval > 60) {
                    showStatus('Update interval must be between 1 and 60 seconds', 'error');
                    return;
                }
                
                // Store new settings
                apiBaseUrl = newApiBaseUrl;
                updateInterval = newUpdateInterval;
                
                // Save to local storage
                localStorage.setItem('apiBaseUrl', apiBaseUrl);
                localStorage.setItem('updateInterval', updateInterval);
                
                // If tracking is active, restart with new interval
                if (updateIntervalId) {
                    clearInterval(updateIntervalId);
                    const selectedSatellite = satelliteSelect.value;
                    if (selectedSatellite) {
                        updateIntervalId = setInterval(() => {
                            updateSatellitePosition(selectedSatellite);
                        }, updateInterval * 1000);
                    }
                }
                
                showStatus('Settings saved successfully', 'success');
            }
            
            // Toggle troubleshoot panel
            function toggleTroubleshootPanel() {
                if (troubleshootPanel.style.display === 'none' || troubleshootPanel.style.display === '') {
                    troubleshootPanel.style.display = 'block';
                    troubleshootButton.textContent = 'Hide Connection Settings';
                } else {
                    troubleshootPanel.style.display = 'none';
                    troubleshootButton.textContent = 'Show Connection Settings';
                }
            }
            
            // Event listeners
            trackButton.addEventListener('click', trackSatellite);
            troubleshootButton.addEventListener('click', toggleTroubleshootPanel);
            saveSettingsButton.addEventListener('click', saveSettings);
            
            // Initialize map after DOM is fully loaded
            setTimeout(initMap, 100);
            
            // Load satellites on page load
            loadSatellites();
        });
    </script>
</body>
</html>''')
    
    print("Starting server. Access the app at http://localhost:5000")
    app.run(debug=True,host='0.0.0.0',port=5000)
