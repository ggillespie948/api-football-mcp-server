import requests
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('RAPID_API_KEY_FOOTBALL')

# Test the endpoint you mentioned
print("Testing https://v3.football.api-sports.io")

headers = {
    'x-apisports-key': api_key
}

try:
    response = requests.get(
        'https://v3.football.api-sports.io/status',
        headers=headers,
        timeout=10
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print("SUCCESS: Direct API-Sports endpoint works!")
        data = response.json()
        print(f"Requests today: {data.get('response', {}).get('requests', {}).get('current', 'unknown')}")
    else:
        print(f"Failed: {response.text[:100]}")
        
except Exception as e:
    print(f"Error: {e}")

# Test RapidAPI endpoint too
print("\nTesting RapidAPI endpoint...")

headers_rapid = {
    'x-rapidapi-host': 'api-football-v1.p.rapidapi.com',
    'x-rapidapi-key': api_key
}

try:
    response = requests.get(
        'https://api-football-v1.p.rapidapi.com/v3/status',
        headers=headers_rapid,
        timeout=10
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print("SUCCESS: RapidAPI endpoint works!")
    else:
        print(f"Failed: {response.text[:100]}")
        
except Exception as e:
    print(f"Error: {e}")
