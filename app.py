import os
from flask import Flask, render_template, jsonify, request
from dotenv import load_dotenv
import requests
import logging
from stats_data import fetch_top_assists, fetch_stats, fetch_top_scorers, get_league_logos, fetch_player_stats_by_name, extract_player_data, league_logos_processor
from flask_caching import Cache
from functools import wraps

load_dotenv()

app = Flask(__name__)
cache = Cache(app, config={'CACHE_TYPE': 'simple'})

app.context_processor(league_logos_processor)
logging.basicConfig(level=logging.DEBUG)

def handle_api_error(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except requests.RequestException as e:
            app.logger.error(f"API request failed: {str(e)}")
            return jsonify({"error": "Failed to fetch data from the API"}), 503
    return wrapper

@app.route('/')
def index():
    year = request.args.get('year', '2024')
    league_logos = get_league_logos()
    league_codes = {
        'premier-league': 39,
        'la-liga': 140,
        'serie-a': 135,
        'bundesliga': 78,
        'ligue-1': 61
    }
    return render_template('index.html', year=year, league_logos=league_logos, league_codes=league_codes)

@app.route('/league/<league_name>')
@cache.cached(timeout=300, query_string=True)  # Cache for 5 minutes, include query string
@handle_api_error
def league(league_name):
    league_codes = {
        'premier-league': 39,
        'la-liga': 140,
        'serie-a': 135,
        'bundesliga': 78,
        'ligue-1': 61
    }
    
    league_code = league_codes.get(league_name.lower())
    year = request.args.get('year', '2024')
    league_logos = get_league_logos()

    if not league_code:
        return "League not found", 404

    standings = fetch_stats(league_code, year)
    top_scorers = fetch_top_scorers(league_code, year)
    top_assists = fetch_top_assists(league_code, year)

    # Validate API responses
    if not (isinstance(standings, dict) and 'response' in standings):
        app.logger.error(f"Invalid standings data for league {league_code}, year {year}: {standings}")
    if not (isinstance(top_scorers, dict) and 'response' in top_scorers):
        app.logger.error(f"Invalid top scorers data for league {league_code}, year {year}: {top_scorers}")
    if not (isinstance(top_assists, dict) and 'response' in top_assists):
        app.logger.error(f"Invalid top assists data for league {league_code}, year {year}: {top_assists}")

    if (isinstance(standings, dict) and 'response' in standings and
        isinstance(top_scorers, dict) and 'response' in top_scorers and
        isinstance(top_assists, dict) and 'response' in top_assists):
        top_scorers_list = top_scorers['response'][:10]
        top_assists_list = top_assists['response'][:10]
        return render_template(
            'league.html',
            standings=standings['response'],
            league_name=league_name.replace('-', ' ').title(),
            top_scorers=top_scorers_list,
            top_assists=top_assists_list,
            year=year,
            league_logos=league_logos
        )
    else:
        return jsonify({"error": "Incomplete or invalid data from API"}), 500

@app.route('/top-scorer')
@cache.cached(timeout=300, query_string=True)  # Cache for 5 minutes, include query string
@handle_api_error
def top_scorer():
    year = request.args.get('year', '2024')
    league_codes = [39, 140, 135, 78, 61]
    top_scorers = []
    league_logos = get_league_logos()

    for code in league_codes:
        data = fetch_top_scorers(code, year)
        if isinstance(data, dict) and 'response' in data:
            top_scorers.extend(data['response'])
        else:
            app.logger.warning(f"Failed to fetch top scorers for league {code}, year {year}: {data}")

    top_scorers.sort(key=lambda x: x.get('statistics', [{}])[0].get('goals', {}).get('total', 0), reverse=True)
    return render_template('top_scorer.html', top_scorers=top_scorers, year=year, league_logos=league_logos)

@app.route('/top-assists')
@cache.cached(timeout=300, query_string=True)  # Cache for 5 minutes, include query string
@handle_api_error
def top_assists():
    year = request.args.get('year', '2024')
    league_codes = [39, 140, 135, 78, 61]
    assists_list = []
    league_logos = get_league_logos()

    for code in league_codes:
        data = fetch_top_assists(code, year)
        if isinstance(data, dict) and 'response' in data:
            assists_list.extend(data['response'])
        else:
            app.logger.warning(f"Failed to fetch top assists for league {code}, year {year}: {data}")

    assists_list.sort(
        key=lambda x: x.get('statistics', [{}])[0].get('goals', {}).get('assists', 0),
        reverse=True
    )
    return render_template('top_assists.html', assists_list=assists_list, year=year, league_codes=league_codes, league_logos=league_logos)

@app.route('/player_comparison', methods=['GET'])
@cache.cached(timeout=300, query_string=True)  # Cache for 5 minutes, consider query parameters
@handle_api_error
def compare_players():
    player1_name = request.args.get('player1')
    player2_name = request.args.get('player2')
    year = request.args.get('year', '2024')
    league_logos = get_league_logos()
    errors = []
    player1_details = player2_details = None

    if not (player1_name and player2_name):
        errors.append("Please provide both player1 and player2 names.")
        return render_template('player_comparison.html', errors=errors, league_logos=league_logos, year=year)

    player1_data = fetch_player_stats_by_name(player1_name, year)
    player2_data = fetch_player_stats_by_name(player2_name, year)

    if isinstance(player1_data, dict) and player1_data:
        player1_details = extract_player_data(player1_data)
    else:
        errors.append(f"Could not find data for {player1_name} in the specified year.")
        app.logger.error(f"Invalid player1 data for {player1_name}, year {year}: {player1_data}")

    if isinstance(player2_data, dict) and player2_data:
        player2_details = extract_player_data(player2_data)
    else:
        errors.append(f"Could not find data for {player2_name} in the specified year.")
        app.logger.error(f"Invalid player2 data for {player2_name}, year {year}: {player2_data}")

    return render_template(
        'player_comparison.html',
        player1=player1_details,
        player2=player2_details,
        league_logos=league_logos,
        errors=errors,
        year=year
    )

if __name__ == '__main__':
    app.run(debug=True)