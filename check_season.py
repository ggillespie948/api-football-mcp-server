import requests
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('RAPID_API_KEY_FOOTBALL')

print("Checking Premier League seasons...")

response = requests.get(
    'https://v3.football.api-sports.io/leagues',
    headers={'x-apisports-key': api_key},
    params={'id': 39},
    timeout=10
)

if response.status_code == 200:
    data = response.json()
    league_info = data['response'][0]
    seasons = league_info['seasons']
    
    print('Available Premier League seasons:')
    for season in seasons[-5:]:
        year = season['year'] 
        current = season.get('current', False)
        start = season.get('start', '')
        end = season.get('end', '')
        print(f'  {year} - Current: {current} ({start} to {end})')
        
    current_seasons = [s for s in seasons if s.get('current', False)]
    if current_seasons:
        current_year = current_seasons[0]['year']
        print(f'CURRENT SEASON: {current_year}')
    else:
        print('No current season marked - using latest')
        latest = seasons[-1]['year']
        print(f'LATEST SEASON: {latest}')
else:
    print(f'Error: {response.status_code}')
