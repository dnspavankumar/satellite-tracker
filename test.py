import requests
import json

def test_api_endpoints(base_url="http://localhost:5000"):
    """Test the API endpoints of the satellite tracker app."""
    print(f"Testing API endpoints at {base_url}")
    
    # Test /api/satellites endpoint
    print("\nTesting /api/satellites endpoint...")
    try:
        response = requests.get(f"{base_url}/api/satellites")
        print(f"Status code: {response.status_code}")
        print(f"Content type: {response.headers.get('content-type', 'None')}")
        
        if response.status_code == 200:
            if 'application/json' in response.headers.get('content-type', ''):
                data = response.json()
                print(f"Received {len(data)} satellites")
                if data:
                    print(f"First few satellites: {data[:3]}")
            else:
                print("WARNING: Response is not JSON")
                print(f"First 100 characters of response: {response.text[:100]}...")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Exception occurred: {str(e)}")
    
    # Get a satellite name to test with (if available)
    satellite_name = None
    try:
        satellites = requests.get(f"{base_url}/api/satellites").json()
        if satellites:
            satellite_name = satellites[0]
    except:
        pass
    
    # Test /api/position endpoint if we have a satellite name
    if satellite_name:
        print(f"\nTesting /api/position/{satellite_name} endpoint...")
        try:
            response = requests.get(f"{base_url}/api/position/{satellite_name}")
            print(f"Status code: {response.status_code}")
            print(f"Content type: {response.headers.get('content-type', 'None')}")
            
            if response.status_code == 200:
                if 'application/json' in response.headers.get('content-type', ''):
                    data = response.json()
                    print(f"Position data: {json.dumps(data, indent=2)}")
                else:
                    print("WARNING: Response is not JSON")
                    print(f"First 100 characters of response: {response.text[:100]}...")
            else:
                print(f"Error: {response.text}")
        except Exception as e:
            print(f"Exception occurred: {str(e)}")

if __name__ == "__main__":
    test_api_endpoints()