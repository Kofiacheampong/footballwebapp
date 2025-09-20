import os
import time
from dotenv import load_dotenv
import logging
import requests
from typing import Optional, Dict, Any
from functools import wraps
import json
from datetime import datetime

load_dotenv()

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY = 1

def retry_on_failure(retries: int = MAX_RETRIES, delay: float = RETRY_DELAY):
    """Decorator to retry API calls on failure"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(retries + 1):
                try:
                    result = func(*args, **kwargs)
                    if result is not None:
                        return result
                    # If result is None, treat as failure and retry
                    raise Exception("API returned None")

                except Exception as e:
                    last_exception = e
                    if attempt < retries:
                        logging.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {e}. Retrying in {delay}s...")
                        time.sleep(delay * (attempt + 1))  # Exponential backoff
                    else:
                        logging.error(f"All {retries + 1} attempts failed for {func.__name__}: {e}")

            return None
        return wrapper
    return decorator

def validate_api_response(response_data: Dict[Any, Any]) -> bool:
    """Validate API response structure"""
    if not isinstance(response_data, dict):
        return False

    if 'response' not in response_data:
        return False

    if not isinstance(response_data['response'], list):
        return False

    return True

def log_api_metrics(func_name: str, league_code: int, year: int, success: bool, response_time: float):
    """Log API call metrics for monitoring"""
    status = "SUCCESS" if success else "FAILURE"
    logging.info(f"API_METRICS: {func_name} | League: {league_code} | Year: {year} | Status: {status} | Response Time: {response_time:.2f}s")

# Context processor for league logos (can be imported by Flask app)
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
    """Fetch league standings with retry logic and validation"""
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

        # Validate response structure
        if not validate_api_response(data):
            raise ValueError("Invalid API response structure")

        response_time = time.time() - start_time
        log_api_metrics('fetch_stats', league_code, year, True, response_time)
        logging.debug(f"Fetched standings for league {league_code}, year {year}")
        return data

    except (requests.RequestException, ValueError, json.JSONDecodeError) as e:
        response_time = time.time() - start_time
        log_api_metrics('fetch_stats', league_code, year, False, response_time)
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
        league_id = league.get('league', {}).get('id')
        league_name = league.get('league', {}).get('name', '').lower().replace(" ", "-")
        if league_id in league_codes.values():
            league_logos[league_name] = league.get('league', {}).get('logo', '')
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
        except requests.RequestException as e:
            logging.error(f"Request error for {player_name} in league {league_id}: {e}")
    logging.warning(f"No data found for player: {player_name} in any league for year {year}")
    return None

def extract_player_data(player_data):
    if not player_data or 'response' not in player_data or not player_data['response']:
        logging.error("Invalid or empty player data")
        return None

    try:
        player_info = player_data['response'][0]['player']
        stats_by_league = player_data['response'][0]['statistics']

        player_details = {
            'name': player_info.get('name', 'N/A'),
            'age': player_info.get('age', 'N/A'),
            'photo': player_info.get('photo', 'N/A'),
            'height': player_info.get('height', 'N/A'),
            'weight': player_info.get('weight', 'N/A'),
            'nationality': player_info.get('nationality', 'N/A'),
            'leagues': []
        }

        for stats in stats_by_league:
            league_data = {
                'league_name': stats.get('league', {}).get('name', 'N/A'),
                'league_logo': stats.get('league', {}).get('logo', 'N/A'),
                'team_name': stats.get('team', {}).get('name', 'N/A'),
                'team_logo': stats.get('team', {}).get('logo', 'N/A'),
                'appearances': stats.get('games', {}).get('appearances', 0),  # Fixed typo: 'appearences' -> 'appearances'
                'goals': stats.get('goals', {}).get('total', 0),
                'assists': stats.get('goals', {}).get('assists', 0),
                'shots_total': stats.get('shots', {}).get('total', 0),
                'shots_on_target': stats.get('shots', {}).get('on', 0),
                'dribbles_attempted': stats.get('dribbles', {}).get('attempts', 0),
                'dribbles_success': stats.get('dribbles', {}).get('success', 0),
                'fouls_drawn': stats.get('fouls', {}).get('drawn', 0),
                'fouls_committed': stats.get('fouls', {}).get('committed', 0),
                'yellow_cards': stats.get('cards', {}).get('yellow', 0),
                'red_cards': stats.get('cards', {}).get('red', 0),
                'rating': stats.get('games', {}).get('rating', 'N/A')
            }
            player_details['leagues'].append(league_data)

        return player_details
    except (KeyError, IndexError) as e:
        logging.error(f"Error extracting player data: {e}")
        logging.debug(f"Player data: {player_data}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error in extract_player_data: {e}")
        return None