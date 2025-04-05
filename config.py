# config.py
import os
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

# Static league codes (no API calls)
LEAGUE_CODES = {
    'premier-league': 39,
    'la-liga': 140,
    'serie-a': 135,
    'bundesliga': 78,
    'ligue-1': 61
}

# Dynamic league logos (initialize later in app context)
LEAGUE_LOGOS = None

def init_league_logos():
    """Fetch league logos (call this AFTER app initialization)."""
    from stats_data import get_league_logos  # Avoid circular imports
    global LEAGUE_LOGOS
    LEAGUE_LOGOS = get_league_logos()

# Flask settings
class Config:
    CACHE_TYPE = os.getenv('CACHE_TYPE', 'simple')
    CACHE_REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    CACHE_DEFAULT_TIMEOUT = int(os.getenv('CACHE_TIMEOUT', 300))
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')