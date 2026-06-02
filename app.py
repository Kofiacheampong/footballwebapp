import os
from flask import Flask, render_template, jsonify, request
from dotenv import load_dotenv
import requests
import logging
from stats_data import fetch_top_assists, fetch_stats, fetch_top_scorers, get_league_logos, fetch_player_stats_by_name, fetch_player_career_stats, extract_player_data, league_logos_processor
from flask_caching import Cache
from functools import wraps
from database import db, League, Team, Player, PlayerStats
from apscheduler.schedulers.background import BackgroundScheduler
from etl import run_etl

load_dotenv()

app = Flask(__name__)

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', os.urandom(32))
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

database_url = os.getenv('DATABASE_URL', 'sqlite:///football_stats.db')
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

if 'postgresql' in database_url or 'postgres' in database_url:
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
    }

if os.getenv('REDIS_URL'):
    cache_config = {
        'CACHE_TYPE': 'redis',
        'CACHE_REDIS_URL': os.getenv('REDIS_URL')
    }
else:
    cache_config = {'CACHE_TYPE': 'simple'}

cache = Cache(app, config=cache_config)
db.init_app(app)
app.context_processor(league_logos_processor)

logging.basicConfig(level=logging.INFO)

scheduler = BackgroundScheduler()


def run_etl_job():
    with app.app_context():
        app.logger.info("Scheduled ETL starting...")
        try:
            run_etl(db, League, Team, Player, PlayerStats)
            app.logger.info("Scheduled ETL complete")
        except Exception as e:
            app.logger.error(f"ETL failed: {e}", exc_info=True)


def schedule_etl():
    if scheduler.get_job('etl'):
        return
    scheduler.add_job(
        func=run_etl_job,
        trigger='interval',
        hours=6,
        id='etl',
        name='ETL every 6 hours',
        misfire_grace_time=3600
    )
    scheduler.start()
    app.logger.info("ETL scheduler started (every 6 hours)")


def db_standings(league_id, season):
    return db.session.query(Team).filter_by(league_id=league_id).all()


def db_top_scorers(league_id, season):
    return db.session.query(PlayerStats).join(Player).join(Team).filter(
        PlayerStats.league_id == league_id,
        PlayerStats.season == season
    ).order_by(PlayerStats.goals.desc()).limit(50).all()


def db_top_assists(league_id, season):
    return db.session.query(PlayerStats).join(Player).join(Team).filter(
        PlayerStats.league_id == league_id,
        PlayerStats.season == season
    ).order_by(PlayerStats.assists.desc()).limit(50).all()


@app.cli.command()
def init_db():
    db.create_all()
    print('Database tables created.')

@app.cli.command()
def reset_db():
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
        except Exception as e:
            app.logger.error(f"Unexpected error: {str(e)}")
            return jsonify({"error": "An unexpected error occurred"}), 500
    return wrapper

@app.route('/')
def index():
    year = request.args.get('year', '2025')
    league_logos = get_league_logos()
    league_codes = {
        'premier-league': 39,
        'la-liga': 140,
        'serie-a': 135,
        'bundesliga': 78,
        'ligue-1': 61,
        'champions-league': 2
    }
    return render_template('index.html', year=year, league_logos=league_logos, league_codes=league_codes)

@app.route('/league/<league_name>')
@cache.cached(timeout=300, query_string=True)
@handle_api_error
def league(league_name):
    league_codes = {
        'premier-league': 39,
        'la-liga': 140,
        'serie-a': 135,
        'bundesliga': 78,
        'ligue-1': 61,
        'champions-league': 2
    }

    league_code = league_codes.get(league_name.lower())
    year = request.args.get('year', '2025')
    league_logos = get_league_logos()

    if not league_code:
        return "League not found", 404

    standings = fetch_stats(league_code, year)
    standings_data = []
    if isinstance(standings, dict) and 'response' in standings:
        standings_data = standings.get('response', [])

    league_obj = db.session.query(League).filter_by(api_id=league_code).first()
    season_int = int(year)

    top_scorers = None
    try:
        db_stats = db_top_scorers(league_obj.id if league_obj else None, season_int) if league_obj else []
        if db_stats:
            top_scorers = []
            for s in db_stats:
                top_scorers.append({
                    'player': {
                        'name': s.player.name,
                        'photo': s.player.photo_url or '',
                        'nationality': s.player.nationality or '',
                        'age': s.player.age or 0,
                    },
                    'statistics': [{
                        'team': {'name': s.team.name, 'logo': s.team.logo_url or ''},
                        'goals': {'total': s.goals, 'assists': s.assists},
                    }]
                })
    except Exception:
        app.logger.warning("DB query for top scorers failed, falling back to API")

    if not top_scorers:
        top_scorers = fetch_top_scorers(league_code, year)
        top_scorers = top_scorers.get('response', [])[:10] if isinstance(top_scorers, dict) and 'response' in top_scorers else []

    top_assists = None
    try:
        db_stats = db_top_assists(league_obj.id if league_obj else None, season_int) if league_obj else []
        if db_stats:
            top_assists = []
            for s in db_stats:
                top_assists.append({
                    'player': {
                        'name': s.player.name,
                        'photo': s.player.photo_url or '',
                        'nationality': s.player.nationality or '',
                        'age': s.player.age or 0,
                    },
                    'statistics': [{
                        'team': {'name': s.team.name, 'logo': s.team.logo_url or ''},
                        'goals': {'total': s.goals, 'assists': s.assists},
                    }]
                })
    except Exception:
        app.logger.warning("DB query for top assists failed, falling back to API")

    if not top_assists:
        top_assists = fetch_top_assists(league_code, year)
        top_assists = top_assists.get('response', [])[:10] if isinstance(top_assists, dict) and 'response' in top_assists else []

    api_error = not (standings_data or top_scorers or top_assists)

    return render_template(
        'league.html',
        standings=standings_data,
        league_name=league_name.replace('-', ' ').title(),
        top_scorers=top_scorers,
        top_assists=top_assists,
        year=year,
        league_logos=league_logos,
        api_error=api_error,
        api_error_messages=[]
    )

@app.route('/top-scorer')
@cache.cached(timeout=300, query_string=True)
@handle_api_error
def top_scorer():
    year = request.args.get('year', '2025')
    league_codes = [39, 140, 135, 78, 61, 2]
    league_logos = get_league_logos()
    api_errors = []

    try:
        db_stats = db.session.query(PlayerStats).join(Player).join(Team).join(League).filter(
            PlayerStats.season == int(year),
            League.api_id.in_(league_codes)
        ).order_by(PlayerStats.goals.desc()).limit(50).all()

        if db_stats and len(db_stats) > 0:
            top_scorers = []
            for s in db_stats:
                top_scorers.append({
                    'player': {
                        'name': s.player.name,
                        'photo': s.player.photo_url or '',
                        'nationality': s.player.nationality or '',
                        'age': s.player.age or 0,
                    },
                    'statistics': [{
                        'team': {'name': s.team.name, 'logo': s.team.logo_url or ''},
                        'league': {'id': s.league.api_id, 'name': s.league.name},
                        'games': {'appearences': s.appearances, 'rating': str(s.rating) if s.rating else None},
                        'goals': {'total': s.goals, 'assists': s.assists},
                        'shots': {'total': s.shots_total, 'on': s.shots_on_target},
                        'cards': {},
                    }]
                })
            return render_template('top_scorer.html', top_scorers=top_scorers, year=year,
                                 league_logos=league_logos, api_error=False, api_error_messages=[])
    except Exception as e:
        app.logger.warning(f"DB query for top scorers failed, falling back to API: {e}")

    top_scorers = []
    for code in league_codes:
        data = fetch_top_scorers(code, year)
        if isinstance(data, dict) and 'response' in data:
            top_scorers.extend(data['response'])
        elif isinstance(data, dict) and 'errors' in data and data['errors']:
            if isinstance(data['errors'], dict):
                api_errors.extend(data['errors'].values())
            else:
                api_errors.append(str(data['errors']))
        else:
            app.logger.warning(f"Failed to fetch top scorers for league {code}, year {year}: {data}")

    top_scorers.sort(key=lambda x: x.get('statistics', [{}])[0].get('goals', {}).get('total', 0), reverse=True)
    return render_template('top_scorer.html', top_scorers=top_scorers, year=year,
                         league_logos=league_logos, api_error=len(top_scorers) == 0,
                         api_error_messages=list(set(api_errors)) if api_errors else [])

@app.route('/top-assists')
@cache.cached(timeout=300, query_string=True)
@handle_api_error
def top_assists():
    year = request.args.get('year', '2025')
    league_codes = [39, 140, 135, 78, 61, 2]
    league_logos = get_league_logos()
    api_errors = []

    try:
        db_stats = db.session.query(PlayerStats).join(Player).join(Team).join(League).filter(
            PlayerStats.season == int(year),
            League.api_id.in_(league_codes)
        ).order_by(PlayerStats.assists.desc()).limit(50).all()

        if db_stats and len(db_stats) > 0:
            assists_list = []
            for s in db_stats:
                assists_list.append({
                    'player': {
                        'name': s.player.name,
                        'photo': s.player.photo_url or '',
                        'nationality': s.player.nationality or '',
                        'age': s.player.age or 0,
                    },
                    'statistics': [{
                        'team': {'name': s.team.name, 'logo': s.team.logo_url or ''},
                        'league': {'id': s.league.api_id, 'name': s.league.name},
                        'games': {'appearences': s.appearances, 'rating': str(s.rating) if s.rating else None},
                        'goals': {'total': s.goals, 'assists': s.assists},
                        'passes': {'total': None, 'accuracy': None},
                        'cards': {},
                    }]
                })
            return render_template('top_assists.html', assists_list=assists_list, year=year,
                                 league_codes=league_codes, league_logos=league_logos,
                                 api_error=False, api_error_messages=[])
    except Exception as e:
        app.logger.warning(f"DB query for top assists failed, falling back to API: {e}")

    assists_list = []
    for code in league_codes:
        data = fetch_top_assists(code, year)
        if isinstance(data, dict) and 'response' in data:
            assists_list.extend(data['response'])
        elif isinstance(data, dict) and 'errors' in data and data['errors']:
            if isinstance(data['errors'], dict):
                api_errors.extend(data['errors'].values())
            else:
                api_errors.append(str(data['errors']))
        else:
            app.logger.warning(f"Failed to fetch top assists for league {code}, year {year}: {data}")

    assists_list.sort(
        key=lambda x: x.get('statistics', [{}])[0].get('goals', {}).get('assists', 0),
        reverse=True
    )
    return render_template('top_assists.html', assists_list=assists_list, year=year,
                         league_codes=league_codes, league_logos=league_logos,
                         api_error=len(assists_list) == 0 and not api_errors,
                         api_error_messages=list(set(api_errors)) if api_errors else [])

@app.route('/player-tracker')
def player_tracker():
    return render_template('player_tracker.html')

@app.route('/api/player-tracker/add')
def api_add_player():
    player_name = request.args.get('name')

    if not player_name:
        return jsonify({'success': False, 'error': 'Player name is required'})

    try:
        career_data = fetch_player_career_stats(player_name)

        if not career_data:
            return jsonify({'success': False, 'error': f'Player {player_name} not found in any top 5 league'})

        return jsonify({'success': True, 'player': career_data})

    except Exception as e:
        app.logger.error(f"Error adding player {player_name}: {e}")
        return jsonify({'success': False, 'error': 'Failed to fetch player data'})

@app.route('/player_comparison', methods=['GET'])
@cache.cached(timeout=300, query_string=True)
@handle_api_error
def compare_players():
    player1_name = request.args.get('player1')
    player2_name = request.args.get('player2')
    year = request.args.get('year', '2025')
    league_logos = get_league_logos()

    errors = []
    player1_details = player2_details = None

    if not (player1_name and player2_name):
        errors.append("Please provide both player1 and player2 names.")
        return render_template('player_comparison.html', errors=errors, league_logos=league_logos, year=year)

    player1_data = fetch_player_stats_by_name(player1_name, year)
    player2_data = fetch_player_stats_by_name(player2_name, year)

    if isinstance(player1_data, dict) and player1_data.get('response'):
        player1_details = extract_player_data(player1_data)
        if not player1_details:
            errors.append(f"Could not find detailed stats for {player1_name} in {year}.")
    else:
        errors.append(f"Could not find {player1_name} in any of the top 5 European leagues for {year}.")
        app.logger.error(f"No player1 data for {player1_name}, year {year}: {player1_data}")

    if isinstance(player2_data, dict) and player2_data.get('response'):
        player2_details = extract_player_data(player2_data)
        if not player2_details:
            errors.append(f"Could not find detailed stats for {player2_name} in {year}.")
    else:
        errors.append(f"Could not find {player2_name} in any of the top 5 European leagues for {year}.")
        app.logger.error(f"No player2 data for {player2_name}, year {year}: {player2_data}")

    return render_template(
        'player_comparison.html',
        player1=player1_details,
        player2=player2_details,
        league_logos=league_logos,
        errors=errors,
        year=year
    )

@app.route('/health')
def health_check():
    return jsonify({
        "status": "healthy",
        "timestamp": "ok",
        "version": "1.0.0"
    }), 200

@app.errorhandler(404)
def not_found_error(error):
    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        return jsonify({'error': 'Resource not found'}), 404
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    app.logger.error(f'Server Error: {error}')
    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        return jsonify({'error': 'Internal server error'}), 500
    return render_template('500.html'), 500

@app.errorhandler(Exception)
def handle_exception(error):
    app.logger.error(f'Unhandled Exception: {error}', exc_info=True)
    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        return jsonify({'error': 'An unexpected error occurred'}), 500
    return render_template('500.html'), 500

with app.app_context():
    try:
        db.create_all()
        app.logger.info('Database tables created successfully')
    except Exception as e:
        app.logger.error(f'Error creating database tables: {e}')

if not os.getenv('SKIP_ETL'):
    with app.app_context():
        try:
            has_data = db.session.query(PlayerStats).first() is not None
            if not has_data:
                app.logger.info('No data found, running initial ETL...')
                run_etl(db, League, Team, Player, PlayerStats)
            else:
                app.logger.info('Data exists, skipping initial ETL')
        except Exception as e:
            app.logger.error(f'Initial ETL failed: {e}')

    schedule_etl()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
