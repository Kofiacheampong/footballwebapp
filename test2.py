import requests
import os
from dotenv import load_dotenv

load_dotenv()


def get_league_logos():
    api_key = os.environ.get('API_KEY')  # Ensure API_KEY is set
    if not api_key:
        print("API_KEY environment variable is not set")
        return {}

    url = "https://api-football-v1.p.rapidapi.com/v3/leagues"
    headers = {
        'x-rapidapi-host': "api-football-v1.p.rapidapi.com",
        'x-rapidapi-key': api_key
    }

    try:
        print(f"Making request to {url} with headers {headers}")  # Debugging line
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        data = response.json()
        print("Response data:", data)  # Debugging line
        
        # Adjusted based on provided data format
        leagues = data.get('response', [])
        league_logos = {}
        for league in leagues:
            league_name = league['league']['name'].lower().replace(" ", "-")
            league_logos[league_name] = league['league']['logo']

        print("League logos:", league_logos)  # Debugging line
        return league_logos
        
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return {}