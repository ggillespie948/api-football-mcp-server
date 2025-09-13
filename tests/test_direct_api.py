import requests
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('RAPID_API_KEY_FOOTBALL')

print("Testing direct API call for Premier League teams...")

response = requests.get(
    'https://v3.football.api-sports.io/teams',
    headers={'x-apisports-key': api_key},
    params={'league': 39, 'season': 2024},
    timeout=10
)

print(f'Status: {response.status_code}')
if response.status_code == 200:
    data = response.json()
    teams = data.get('response', [])
    print(f'SUCCESS: Got {len(teams)} Premier League teams')
    if teams:
        team_name = teams[0]['team']['name']
        print(f'First team: {team_name}')
        print('API WORKING - can scrape data!')
else:
    print(f'Error: {response.text[:200]}')
