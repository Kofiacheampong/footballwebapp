import os
import time
import logging
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

HEADERS = {
    'x-rapidapi-host': 'api-football-v1.p.rapidapi.com',
    'x-rapidapi-key': os.environ.get('API_KEY', '')
}
BASE_URL = 'https://api-football-v1.p.rapidapi.com/v3/'

LEAGUES = [
    {'id': 39, 'name': 'Premier League', 'country': 'England'},
    {'id': 140, 'name': 'La Liga', 'country': 'Spain'},
    {'id': 135, 'name': 'Serie A', 'country': 'Italy'},
    {'id': 78, 'name': 'Bundesliga', 'country': 'Germany'},
    {'id': 61, 'name': 'Ligue 1', 'country': 'France'},
    {'id': 2, 'name': 'UEFA Champions League', 'country': 'Europe'},
]
SEASONS = ['2025', '2024', '2023', '2022', '2021']

REQUEST_DELAY = 1.5
MAX_RETRIES = 5
BACKOFF_BASE = 2


def api_get(endpoint):
    url = BASE_URL + endpoint
    for attempt in range(MAX_RETRIES + 1):
        time.sleep(REQUEST_DELAY)
        try:
            r = requests.get(url, headers=HEADERS, timeout=30)
            if r.status_code == 429:
                retry_after = int(r.headers.get('Retry-After', BACKOFF_BASE ** attempt))
                logger.warning(f"429 on {endpoint}, retrying after {retry_after}s (attempt {attempt+1}/{MAX_RETRIES})")
                time.sleep(retry_after)
                continue
            r.raise_for_status()
            return r.json()
        except requests.exceptions.HTTPError as e:
            if r.status_code == 429 and attempt < MAX_RETRIES:
                retry_after = int(r.headers.get('Retry-After', BACKOFF_BASE ** attempt))
                logger.warning(f"429 on {endpoint}, retry {retry_after}s (attempt {attempt+1}/{MAX_RETRIES})")
                time.sleep(retry_after)
                continue
            logger.error(f"API GET {endpoint} failed: {e}")
            return None
        except Exception as e:
            logger.error(f"API GET {endpoint} failed: {e}")
            return None
    logger.error(f"API GET {endpoint} exhausted retries")
    return None


def _upsert(model, db, **kwargs):
    session = db.session
    ident = {k: v for k, v in kwargs.items() if k.endswith('_id') or k in ('api_id',)}
    filters = {k: v for k, v in ident.items() if v is not None}
    obj = None
    if filters:
        obj = session.query(model).filter_by(**filters).first()
    if not obj and 'api_id' in kwargs and kwargs['api_id']:
        obj = session.query(model).filter_by(api_id=kwargs['api_id']).first()
    if obj:
        for k, v in kwargs.items():
            if v is not None:
                setattr(obj, k, v)
        return obj
    obj = model(**{k: v for k, v in kwargs.items() if v is not None or k in ('api_id',)})
    session.add(obj)
    session.flush()
    return obj


def run_etl(db, League, Team, Player, PlayerStats):
    logger.info("=== ETL START ===")
    start = datetime.now()

    if not HEADERS.get('x-rapidapi-key'):
        logger.error("API_KEY not set, skipping ETL")
        return

    session = db.session

    for league_info in LEAGUES:
        lid = league_info['id']
        logger.info(f"Processing: {league_info['name']}")

        data = api_get(f'leagues?id={lid}')
        if not data or not data.get('response'):
            continue
        api = data['response'][0]['league']
        league = _upsert(League, db,
            api_id=lid, name=api.get('name'),
            country=league_info['country'],
            logo_url=api.get('logo', '')
        )

        for season in SEASONS:
            logger.info(f"  {season}: standings...")
            sdata = api_get(f'standings?league={lid}&season={season}')
            if sdata and sdata.get('response'):
                for entry in sdata['response']:
                    for group in (entry.get('league', {}).get('standings', []) or []):
                        for te in group:
                            tm = te.get('team', {})
                            if tm.get('id'):
                                _upsert(Team, db,
                                    api_id=tm['id'], name=tm.get('name'),
                                    logo_url=tm.get('logo'), league_id=league.id
                                )

            logger.info(f"  {season}: top scorers...")
            scdata = api_get(f'players/topscorers?league={lid}&season={season}')
            if scdata and scdata.get('response'):
                for entry in scdata['response']:
                    stats_list = entry.get('statistics') or []
                    if not stats_list:
                        continue
                    s = stats_list[0]
                    p = entry.get('player', {})
                    t = s.get('team', {})
                    l = s.get('league', {})
                    if not p.get('id') or not t.get('id'):
                        continue

                    lobj = session.query(League).filter_by(api_id=l.get('id')).first()
                    if not lobj:
                        continue

                    player = _upsert(Player, db,
                        api_id=p['id'], name=p.get('name'),
                        age=p.get('age'), nationality=p.get('nationality'),
                        photo_url=p.get('photo')
                    )
                    team = _upsert(Team, db,
                        api_id=t['id'], name=t.get('name'),
                        logo_url=t.get('logo'), league_id=lobj.id
                    )

                    g = s.get('games', {}) or {}
                    go = s.get('goals', {}) or {}
                    sh = s.get('shots', {}) or {}
                    c = s.get('cards', {}) or {}

                    stat = session.query(PlayerStats).filter_by(
                        player_id=player.id, team_id=team.id,
                        league_id=lobj.id, season=int(season)
                    ).first()
                    if not stat:
                        stat = PlayerStats(
                            player_id=player.id, team_id=team.id,
                            league_id=lobj.id, season=int(season),
                            appearances=g.get('appearences', 0) or 0,
                            goals=go.get('total', 0) or 0,
                            assists=go.get('assists', 0) or 0,
                            shots_total=sh.get('total', 0) or 0,
                            shots_on_target=sh.get('on', 0) or 0,
                            rating=g.get('rating'),
                            yellow_cards=c.get('yellow', 0) or 0,
                            red_cards=c.get('red', 0) or 0,
                        )
                        session.add(stat)
                    else:
                        stat.appearances = g.get('appearences', stat.appearances) or stat.appearances
                        stat.goals = go.get('total', stat.goals) or stat.goals
                        stat.assists = go.get('assists', stat.assists) or stat.assists
                        stat.shots_total = sh.get('total', stat.shots_total) or stat.shots_total
                        stat.shots_on_target = sh.get('on', stat.shots_on_target) or stat.shots_on_target
                        if g.get('rating'):
                            stat.rating = g['rating']
                        stat.yellow_cards = c.get('yellow', stat.yellow_cards) or stat.yellow_cards
                        stat.red_cards = c.get('red', stat.red_cards) or stat.red_cards

            logger.info(f"  {season}: top assists...")
            adata = api_get(f'players/topassists?league={lid}&season={season}')
            if adata and adata.get('response'):
                for entry in adata['response']:
                    stats_list = entry.get('statistics') or []
                    if not stats_list:
                        continue
                    s = stats_list[0]
                    p = entry.get('player', {})
                    t = s.get('team', {})
                    l = s.get('league', {})
                    if not p.get('id') or not t.get('id'):
                        continue

                    lobj = session.query(League).filter_by(api_id=l.get('id')).first()
                    if not lobj:
                        continue

                    player = _upsert(Player, db,
                        api_id=p['id'], name=p.get('name'),
                        age=p.get('age'), nationality=p.get('nationality'),
                        photo_url=p.get('photo')
                    )
                    team = _upsert(Team, db,
                        api_id=t['id'], name=t.get('name'),
                        logo_url=t.get('logo'), league_id=lobj.id
                    )

                    g = s.get('games', {}) or {}
                    go = s.get('goals', {}) or {}
                    c = s.get('cards', {}) or {}

                    stat = session.query(PlayerStats).filter_by(
                        player_id=player.id, team_id=team.id,
                        league_id=lobj.id, season=int(season)
                    ).first()
                    if not stat:
                        stat = PlayerStats(
                            player_id=player.id, team_id=team.id,
                            league_id=lobj.id, season=int(season),
                            appearances=g.get('appearences', 0) or 0,
                            goals=go.get('total', 0) or 0,
                            assists=go.get('assists', 0) or 0,
                            rating=g.get('rating'),
                            yellow_cards=c.get('yellow', 0) or 0,
                            red_cards=c.get('red', 0) or 0,
                        )
                        session.add(stat)
                    else:
                        stat.appearances = g.get('appearences', stat.appearances) or stat.appearances
                        stat.goals = go.get('total', stat.goals) or stat.goals
                        stat.assists = go.get('assists', stat.assists) or stat.assists
                        if g.get('rating'):
                            stat.rating = g['rating']
                        stat.yellow_cards = c.get('yellow', stat.yellow_cards) or stat.yellow_cards
                        stat.red_cards = c.get('red', stat.red_cards) or stat.red_cards

        session.commit()

    elapsed = (datetime.now() - start).total_seconds()
    logger.info(f"=== ETL END ({elapsed:.1f}s) ===")
