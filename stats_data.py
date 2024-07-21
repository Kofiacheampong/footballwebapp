import os
import time
from dotenv import load_dotenv

import requests
load_dotenv()

def fetch_stats(league_code):
    api_key = os.environ['API_KEY']
    headers = {
        'x-rapidapi-host': 'api-football-v1.p.rapidapi.com',
        'x-rapidapi-key': api_key
    }
    base_url = '"https://api-football-vl.p.rapidapi.com/v2/teams/league/442" '
    url = f'{base_url}standings?league={league_code}&season=2023'
    response = requests.get(url, headers=headers)
    print(response.json())


# def fetch_stats(league_code):
#     api_key = os.environ['API_KEY']
#     if not api_key:
#         print("API key is missing!")
#     print(f"Using API key")  # Print the API key for debugging

#     headers = {
#         'x-rapidapi-host': 'api-football-v1.p.rapidapi.com',
#         'x-rapidapi-key': api_key
#     }
#     base_url = 'https://api-football-v1.p.rapidapi.com/v3/leagues'

#     url = f'{base_url}standings?league={league_code}&season=2023'
#     response = requests.get(url, headers=headers)

#     if response.status_code == 200:
#         data = response.json()
#         players_stats = []

#         for team in data['response'][0]['league']['standings'][0]:
#             team_data = {
#                 'position': team['rank'],
#                 'team': team['team']['name'],
#                 'points': team['points'],
#                 'emblem': team['team']['logo']
#             }
#             players_stats.append(team_data)

#         return players_stats
#     elif response.status_code == 401:
#         print("Error fetching data: 401 Unauthorized. Check your API key.")
#     elif response.status_code == 429:
#         print("Error fetching data: 429 Too Many Requests. Rate limit exceeded.")
#         print("Retrying after a delay...")
#         time.sleep(60)  # Wait for 60 seconds before retrying
#         return fetch_stats(league_code)
#     else:
#         print(f"Error fetching data: {response.status_code}")

#     return [