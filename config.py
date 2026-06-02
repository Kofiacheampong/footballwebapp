import os
from dotenv import load_dotenv

load_dotenv()

LEAGUE_CODES = {
    'premier-league': 39,
    'la-liga': 140,
    'serie-a': 135,
    'bundesliga': 78,
    'ligue-1': 61,
    'champions-league': 2
}

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', os.urandom(32))
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///football_stats.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CACHE_TYPE = os.getenv('CACHE_TYPE', 'simple')
    CACHE_REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    CACHE_DEFAULT_TIMEOUT = int(os.getenv('CACHE_TIMEOUT', 300))
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
