import os
import time
from dotenv import load_dotenv
import logging
import json

import requests
load_dotenv()

# context_processors.py

def league_logos_processor():
    return {
        'league_logos': {
            'Premier League': 'https://example.com/epl_logo.png',
            'La Liga': 'https://example.com/la_liga_logo.png',
            'Serie A': 'https://example.com/serie_a_logo.png',
            'Bundesliga': 'https://example.com/bundesliga_logo.png',
            'Ligue 1': 'https://example.com/ligue_1_logo.png'
        }
    }

def fetch_stats(league_code, year):
    api_key = os.environ['API_KEY']
    headers = {
        'x-rapidapi-host': 'api-football-v1.p.rapidapi.com',
        'x-rapidapi-key': api_key
    }
    base_url = 'https://api-football-v1.p.rapidapi.com/v3/'
    endpoint = f'standings?league={league_code}&season={year}'
    url = base_url + endpoint
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None

def fetch_top_scorers(league_code,year):
    api_key = os.environ['API_KEY']
    headers = {
        'x-rapidapi-host': 'api-football-v1.p.rapidapi.com',
        'x-rapidapi-key': api_key
    }
    base_url = 'https://api-football-v1.p.rapidapi.com/v3/'
    endpoint = f'players/topscorers?league={league_code}&season={year}'
    url = base_url + endpoint
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None
    

def fetch_top_assists(league_code, year):
    api_key = os.environ['API_KEY']
    headers = {
        'x-rapidapi-host': 'api-football-v1.p.rapidapi.com',
        'x-rapidapi-key': api_key
    }
    base_url = 'https://api-football-v1.p.rapidapi.com/v3/'
    endpoint = f'players/topassists?league={league_code}&season={year}'
    url = base_url + endpoint
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Will raise HTTPError for bad responses
        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None

def get_league_logos():
    api_key = os.environ['API_KEY']
    url = "https://api-football-v1.p.rapidapi.com/v3/leagues"
    headers = {
        'x-rapidapi-host': "api-football-v1.p.rapidapi.com",
        'x-rapidapi-key': api_key  # Replace with your actual API key
    }
    response = requests.get(url, headers=headers)
    data = response.json()

    # Define relevant leagues by name or ID
    league_codes = {
        'premier-league': 39,
        'la-liga': 140,
        'serie-a': 135,
        'bundesliga': 78,
        'ligue-1': 61
    }
 
    leagues = data.get('response', [])
    league_logos = {}
    for league in leagues:
        league_id = league['league']['id']
        league_name = league['league']['name'].lower().replace(" ", "-")
        if league_id in league_codes.values():
            league_logos[league_name] = league['league']['logo']

    return league_logos

def fetch_player_stats_by_name(player_name, year):
    api_key = os.environ['API_KEY']
    url = "https://api-football-v1.p.rapidapi.com/v3/players"
    
    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
    }
    
    # List of major league IDs
    league_ids = [39, 140, 135, 78, 61]  # Premier League, La Liga, Serie A, Bundesliga, Ligue 1
    
    for league_id in league_ids:
        querystring = {"search": player_name, "season": year, "league": league_id}
        
        try:
            response = requests.get(url, headers=headers, params=querystring)
            response.raise_for_status()

            data = response.json()
            logging.info(f"API Response for {player_name} in league {league_id}: {data}")

            if 'response' in data and data['response']:
                return data
        except requests.exceptions.RequestException as e:
            logging.error(f"Request error for {player_name} in league {league_id}: {e}")
        except ValueError as e:
            logging.error(f"JSON parsing error for {player_name} in league {league_id}: {e}")
    
    logging.warning(f"No data found for player: {player_name} in any league")
    return None

def extract_player_data(player_data):
    if not player_data or 'response' not in player_data or not player_data['response']:
        logging.error("Invalid or empty player data")
        return None

    try:
        # Extract player info and stats
        player_info = player_data['response'][0]['player']
        stats_by_league = player_data['response'][0]['statistics']

        # Create player details dictionary
        player_details = {
            'name': player_info.get('name', 'N/A'),
            'age': player_info.get('age', 'N/A'),
            'photo': player_info.get('photo', 'N/A'),
            'height': player_info.get('height', 'N/A'),
            'weight': player_info.get('weight', 'N/A'),
            'nationality': player_info.get('nationality', 'N/A'),
            'leagues': []
        }

        # Process statistics for each league
        for stats in stats_by_league:
            league_data = {
                'league_name': stats['league'].get('name', 'N/A'),
                'league_logo': stats['league'].get('logo', 'N/A'),
                'team_name': stats['team'].get('name', 'N/A'),
                'team_logo': stats['team'].get('logo', 'N/A'),
                'appearences': stats['games'].get('appearences', 0),  # Changed from 'appearances' to 'appearences'
                'goals': stats['goals'].get('total', 0),
                'assists': stats['goals'].get('assists', 0),
                'shots_total': stats['shots'].get('total', 0),
                'shots_on_target': stats['shots'].get('on', 0),
                'dribbles_attempted': stats['dribbles'].get('attempts', 0),
                'dribbles_success': stats['dribbles'].get('success', 0),
                'fouls_drawn': stats['fouls'].get('drawn', 0),
                'fouls_committed': stats['fouls'].get('committed', 0),
                'yellow_cards': stats['cards'].get('yellow', 0),
                'red_cards': stats['cards'].get('red', 0),
                'rating': stats['games'].get('rating', 0)
            }
            player_details['leagues'].append(league_data)

        return player_details

    except (KeyError, IndexError) as e:
        logging.error(f"Error extracting player data: {e}")
        logging.debug(f"Player data: {player_data}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error occurred: {e}")
        logging.debug(f"Player data: {player_data}")
        return None


# if __name__ == "__main__":
#     load_dotenv()
#     league_codes = [39, 140, 135, 78, 61]
#     for code in league_codes:
#         data = fetch_top_assists(code)
#         print(data)

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

#     return []
