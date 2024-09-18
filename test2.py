import requests
import os
from dotenv import load_dotenv

load_dotenv()

import requests
def fetch_player_stats_by_name(player_name):
    api_key = os.environ.get('API_KEY')

    if not api_key:
        print("API_KEY environment variable is not set.")
        return

    url = "https://api-football-v1.p.rapidapi.com/v3/players"
    querystring = {"search": player_name}
    
    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
    }
    
    try:
        response = requests.get(url, headers=headers, params=querystring)
        response.raise_for_status()  # Raise an error for HTTP requests with status codes 4xx/5xx
        
        # Print the response status code and JSON data
        print("Response Status Code:", response.status_code)
        print("Response JSON Data:", response.json())
        
        return response.json()
    
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None