import os
import time
from dotenv import load_dotenv
import logging
import requests
from typing import Optional, Dict, Any
from functools import wraps
import json

load_dotenv()

logging.basicConfig(level=logging.INFO)

MAX_RETRIES = 3
RETRY_DELAY = 1

def retry_on_failure(retries: int = MAX_RETRIES, delay: float = RETRY_DELAY):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(retries + 1):
                try:
                    result = func(*args, **kwargs)
                    if result is not None:
                        return result
                    raise Exception("API returned None")
                except Exception as e:
                    last_exception = e
                    if attempt < retries:
                        logging.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {e}. Retrying in {delay}s...")
                        time.sleep(delay * (attempt + 1))
                    else:
                        logging.error(f"All {retries + 1} attempts failed for {func.__name__}: {e}")
            return None
        return wrapper
    return decorator

def validate_api_response(response_data: Dict[Any, Any]) -> bool:
    if not isinstance(response_data, dict):
        return False
    if 'response' not in response_data:
        return False
    if not isinstance(response_data['response'], list):
        return False
    return True

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

@retry_on_failure(retries=MAX_RETRIES)
def fetch_stats(league_code: int, year: int) -> Optional[Dict[Any, Any]]:
    start_time = time.time()
    api_key = os.environ.get('API_KEY')

    if not api_key:
        logging.error("API_KEY environment variable is missing")
        return None

    headers = {
        'x-rapidapi-host': 'api-football-v1.p.rapidapi.com',
        'x-rapidapi-key': api_key
    }
    base_url = 'https://api-football-v1.p.rapidapi.com/v3/'
    endpoint = f'standings?league={league_code}&season={year}'
    url = base_url + endpoint

    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()

        if not validate_api_response(data):
            raise ValueError("Invalid API response structure")

        logging.debug(f"Fetched standings for league {league_code}, year {year}")
        return data

    except (requests.RequestException, ValueError, json.JSONDecodeError) as e:
        logging.error(f"Failed to fetch standings for league {league_code}, year {year}: {e}")
        raise e

def fetch_top_scorers(league_code, year):
    api_key = os.environ.get('API_KEY')
    if not api_key:
        logging.error("API_KEY environment variable is missing")
        return None

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
        logging.debug(f"Fetched top scorers for league {league_code}, year {year}: {data}")
        return data
    except requests.RequestException as e:
        logging.error(f"Failed to fetch top scorers for league {league_code}, year {year}: {e}")
        return None

def fetch_top_assists(league_code, year):
    api_key = os.environ.get('API_KEY')
    if not api_key:
        logging.error("API_KEY environment variable is missing")
        return None

    headers = {
        'x-rapidapi-host': 'api-football-v1.p.rapidapi.com',
        'x-rapidapi-key': api_key
    }
    base_url = 'https://api-football-v1.p.rapidapi.com/v3/'
    endpoint = f'players/topassists?league={league_code}&season={year}'
    url = base_url + endpoint

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        logging.debug(f"Fetched top assists for league {league_code}, year {year}: {data}")
        return data
    except requests.RequestException as e:
        logging.error(f"Failed to fetch top assists for league {league_code}, year {year}: {e}")
        return None

def get_league_logos():
    api_key = os.environ.get('API_KEY')
    if not api_key:
        logging.error("API_KEY environment variable is missing")
        return {}

    url = "https://api-football-v1.p.rapidapi.com/v3/leagues"
    headers = {
        'x-rapidapi-host': "api-football-v1.p.rapidapi.com",
        'x-rapidapi-key': api_key
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        logging.error(f"Failed to fetch league logos: {e}")
        return {}

    target_ids = {39, 140, 135, 78, 61, 2}

    leagues = data.get('response', [])
    league_logos = {}
    for league in leagues:
        league_id = league.get('league', {}).get('id')
        if league_id in target_ids:
            league_logos[league_id] = league.get('league', {}).get('logo', '')
    logging.debug(f"Retrieved league logos: {league_logos}")
    return league_logos

def fetch_player_stats_by_name(player_name, year):
    api_key = os.environ.get('API_KEY')
    if not api_key:
        logging.error("API_KEY environment variable is missing")
        return None

    url = "https://api-football-v1.p.rapidapi.com/v3/players"
    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
    }
    league_ids = [39, 140, 135, 78, 61, 2]

    for league_id in league_ids:
        querystring = {"search": player_name, "season": year, "league": league_id}
        try:
            response = requests.get(url, headers=headers, params=querystring)
            response.raise_for_status()
            data = response.json()
            logging.info(f"API Response for {player_name} in league {league_id}: {data}")
            if 'response' in data and data['response']:
                return data
        except requests.RequestException as e:
            logging.error(f"Request error for {player_name} in league {league_id}: {e}")
    logging.warning(f"No data found for player: {player_name} in any league for year {year}")
    return None

def fetch_player_career_stats(player_name, seasons=None):
    if seasons is None:
        seasons = ['2025', '2024', '2023', '2022', '2021']

    api_key = os.environ.get('API_KEY')
    if not api_key:
        logging.error("API_KEY environment variable is missing")
        return None

    url = "https://api-football-v1.p.rapidapi.com/v3/players"
    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
    }
    league_ids = [39, 140, 135, 78, 61, 2]
    found_league = None
    player_info = None

    for league_id in league_ids:
        querystring = {"search": player_name, "season": "2024", "league": league_id}
        try:
            response = requests.get(url, headers=headers, params=querystring)
            response.raise_for_status()
            data = response.json()
            if 'response' in data and data['response']:
                found_league = league_id
                player_info = data['response'][0].get('player', {})
                break
        except requests.RequestException as e:
            logging.error(f"Request error for {player_name} in league {league_id}: {e}")

    if not found_league or not player_info:
        return None

    season_stats = []
    for season in seasons:
        querystring = {"search": player_name, "season": season, "league": found_league}
        try:
            response = requests.get(url, headers=headers, params=querystring)
            response.raise_for_status()
            data = response.json()
            if 'response' in data and data['response']:
                stats = data['response'][0].get('statistics', [{}])[0] if data['response'][0].get('statistics') else {}
                season_stats.append({
                    'season': season,
                    'team': stats.get('team', {}).get('name', 'Unknown'),
                    'games': stats.get('games', {}).get('appearences', 0) or 0,
                    'goals': stats.get('goals', {}).get('total', 0) or 0,
                    'assists': stats.get('goals', {}).get('assists', 0) or 0,
                    'yellow_cards': stats.get('cards', {}).get('yellow', 0) or 0,
                    'red_cards': stats.get('cards', {}).get('red', 0) or 0,
                    'rating': stats.get('games', {}).get('rating', None)
                })
            else:
                season_stats.append({
                    'season': season,
                    'team': 'N/A',
                    'games': 0, 'goals': 0, 'assists': 0,
                    'yellow_cards': 0, 'red_cards': 0, 'rating': None
                })
        except requests.RequestException as e:
            logging.error(f"Request error for {player_name} in season {season}: {e}")
            season_stats.append({
                'season': season,
                'team': 'N/A',
                'games': 0, 'goals': 0, 'assists': 0,
                'yellow_cards': 0, 'red_cards': 0, 'rating': None
            })

    current = season_stats[0] if season_stats else {}

    return {
        'name': player_info.get('name', player_name),
        'photo': player_info.get('photo', ''),
        'seasons': season_stats,
        'current': {
            'goals': current.get('goals', 0),
            'assists': current.get('assists', 0),
            'games': current.get('games', 0),
        }
    }

def extract_player_data(player_data):
    if not player_data or 'response' not in player_data or not player_data['response']:
        logging.error("Invalid or empty player data")
        return None

    try:
        player_info = player_data['response'][0]['player']
        statistics = player_data['response'][0].get('statistics', [{}])[0] if player_data['response'][0].get('statistics') else {}

        return {
            'name': player_info.get('name', 'Unknown'),
            'age': player_info.get('age', 'N/A'),
            'nationality': player_info.get('nationality', 'Unknown'),
            'position': statistics.get('games', {}).get('position', 'Unknown'),
            'team': statistics.get('team', {}).get('name', 'Unknown'),
            'games': statistics.get('games', {}).get('appearences', 0),
            'goals': statistics.get('goals', {}).get('total', 0),
            'assists': statistics.get('goals', {}).get('assists', 0),
            'yellow_cards': statistics.get('cards', {}).get('yellow', 0),
            'red_cards': statistics.get('cards', {}).get('red', 0),
            'photo': player_info.get('photo', '')
        }
    except (KeyError, IndexError) as e:
        logging.error(f"Error extracting player data: {e}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error in extract_player_data: {e}")
        return None
