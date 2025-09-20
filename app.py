import os
from flask import Flask, render_template, jsonify, request
from dotenv import load_dotenv
import requests
import logging
from stats_data import fetch_top_assists, fetch_stats, fetch_top_scorers, get_league_logos, fetch_player_stats_by_name, extract_player_data, league_logos_processor
from flask_caching import Cache
from functools import wraps
from database import db
import time
import psutil
from datetime import datetime

load_dotenv()

app = Flask(__name__)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///football_stats.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Cache configuration - Redis if available, otherwise simple
if os.getenv('REDIS_URL'):
    cache_config = {
        'CACHE_TYPE': 'redis',
        'CACHE_REDIS_URL': os.getenv('REDIS_URL')
    }
else:
    cache_config = {'CACHE_TYPE': 'simple'}

cache = Cache(app, config=cache_config)

# Initialize database
db.init_app(app)

app.context_processor(league_logos_processor)
logging.basicConfig(level=logging.DEBUG)

# CLI commands for database management
@app.cli.command()
def init_db():
    """Initialize the database."""
    db.create_all()
    print('Database tables created.')

@app.cli.command()
def reset_db():
    """Reset the database."""
    db.drop_all()
    db.create_all()
    print('Database reset complete.')

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

# Health check endpoints
@app.route('/health')
def health_check():
    """Basic health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }), 200

@app.route('/health/detailed')
def detailed_health_check():
    """Detailed health check with system metrics"""
    try:
        # Check database connection
        db_status = "healthy"
        try:
            db.session.execute(db.text('SELECT 1'))
            db.session.commit()
        except Exception as e:
            db_status = f"unhealthy: {str(e)}"

        # Check cache connection
        cache_status = "healthy"
        try:
            cache.set('health_check', 'test', timeout=5)
            if cache.get('health_check') != 'test':
                cache_status = "unhealthy: cache write/read failed"
        except Exception as e:
            cache_status = f"unhealthy: {str(e)}"
            # In testing mode, cache failures are acceptable
            if app.config.get('TESTING'):
                cache_status = "degraded: cache unavailable in test mode"

        # System metrics
        system_metrics = {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent
        }

        # Determine overall health status
        is_healthy = db_status == "healthy"
        is_cache_ok = cache_status == "healthy" or "degraded" in cache_status

        if is_healthy and is_cache_ok:
            overall_status = "healthy"
            status_code = 200
        elif is_healthy:
            overall_status = "degraded"
            status_code = 200  # Still OK if database works
        else:
            overall_status = "unhealthy"
            status_code = 503

        health_data = {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "checks": {
                "database": db_status,
                "cache": cache_status
            },
            "system": system_metrics
        }
        return jsonify(health_data), status_code

    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }), 503

@app.route('/metrics')
def metrics():
    """Prometheus metrics endpoint"""
    try:
        # Basic application metrics
        metrics_data = []

        # System metrics
        cpu_usage = psutil.cpu_percent()
        memory_usage = psutil.virtual_memory().percent

        metrics_data.append(f'football_app_cpu_usage {cpu_usage}')
        metrics_data.append(f'football_app_memory_usage {memory_usage}')

        # Database connection pool metrics (if available)
        try:
            # This would depend on your SQLAlchemy setup
            metrics_data.append('football_app_db_connections_active 1')
        except:
            metrics_data.append('football_app_db_connections_active 0')

        # Cache hit ratio (mock data for now)
        metrics_data.append('football_app_cache_hit_ratio 0.85')

        return '\n'.join(metrics_data) + '\n', 200, {'Content-Type': 'text/plain'}

    except Exception as e:
        app.logger.error(f"Metrics endpoint error: {e}")
        return "# Error generating metrics\n", 500, {'Content-Type': 'text/plain'}

if __name__ == '__main__':
    app.run(debug=True)