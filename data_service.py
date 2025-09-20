import os
import json
from datetime import datetime, timedelta
from celery import Celery
from database import db, League, Team, Player, PlayerStats, APICache
from stats_data import fetch_stats, fetch_top_scorers, fetch_top_assists
from flask import current_app
from pydantic import BaseModel, validator
from typing import List, Optional

# Celery configuration
def make_celery(app):
    celery = Celery(
        app.import_name,
        backend=app.config.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0'),
        broker=app.config.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    )
    celery.conf.update(app.config)
    return celery

# Data validation models
class PlayerStatsValidation(BaseModel):
    player_name: str
    team_name: str
    league_name: str
    goals: Optional[int] = 0
    assists: Optional[int] = 0
    appearances: Optional[int] = 0
    rating: Optional[float] = None

    @validator('goals', 'assists', 'appearances')
    def validate_non_negative(cls, v):
        return max(0, v or 0)

class DataService:
    """Service class for handling data operations"""

    @staticmethod
    def get_cached_data(cache_key: str) -> Optional[dict]:
        """Retrieve data from database cache"""
        cached = APICache.query.filter_by(cache_key=cache_key).first()
        if cached and cached.expires_at > datetime.utcnow():
            return json.loads(cached.data)
        return None

    @staticmethod
    def cache_data(cache_key: str, data: dict, ttl_minutes: int = 60):
        """Cache data in database with TTL"""
        expires_at = datetime.utcnow() + timedelta(minutes=ttl_minutes)

        # Update or create cache entry
        cached = APICache.query.filter_by(cache_key=cache_key).first()
        if cached:
            cached.data = json.dumps(data)
            cached.expires_at = expires_at
        else:
            cached = APICache(
                cache_key=cache_key,
                data=json.dumps(data),
                expires_at=expires_at
            )
            db.session.add(cached)

        db.session.commit()

    @staticmethod
    def get_or_create_league(api_id: int, name: str, logo_url: str = None) -> League:
        """Get existing league or create new one"""
        league = League.query.filter_by(api_id=api_id).first()
        if not league:
            league = League(api_id=api_id, name=name, logo_url=logo_url)
            db.session.add(league)
            db.session.commit()
        return league

    @staticmethod
    def get_or_create_team(api_id: int, name: str, league_id: int, logo_url: str = None) -> Team:
        """Get existing team or create new one"""
        team = Team.query.filter_by(api_id=api_id).first()
        if not team:
            team = Team(api_id=api_id, name=name, league_id=league_id, logo_url=logo_url)
            db.session.add(team)
            db.session.commit()
        return team

    @staticmethod
    def get_or_create_player(api_id: int, name: str, **kwargs) -> Player:
        """Get existing player or create new one"""
        player = Player.query.filter_by(api_id=api_id).first()
        if not player:
            player = Player(api_id=api_id, name=name, **kwargs)
            db.session.add(player)
            db.session.commit()
        return player

# Background tasks using Celery
def create_background_tasks(celery_app):

    @celery_app.task
    def fetch_and_store_league_data(league_code: int, year: int):
        """Background task to fetch and store league data"""
        try:
            # Fetch data from API
            standings_data = fetch_stats(league_code, year)
            scorers_data = fetch_top_scorers(league_code, year)
            assists_data = fetch_top_assists(league_code, year)

            if not all([standings_data, scorers_data, assists_data]):
                return {"status": "error", "message": "Failed to fetch all data"}

            # Store in database cache
            cache_key_standings = f"standings_{league_code}_{year}"
            cache_key_scorers = f"scorers_{league_code}_{year}"
            cache_key_assists = f"assists_{league_code}_{year}"

            DataService.cache_data(cache_key_standings, standings_data, ttl_minutes=60)
            DataService.cache_data(cache_key_scorers, scorers_data, ttl_minutes=60)
            DataService.cache_data(cache_key_assists, assists_data, ttl_minutes=60)

            # TODO: Process and store normalized data in relational tables

            return {
                "status": "success",
                "league_code": league_code,
                "year": year,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            return {"status": "error", "message": str(e)}

    @celery_app.task
    def refresh_all_leagues(year: int = 2024):
        """Refresh data for all supported leagues"""
        league_codes = [39, 140, 135, 78, 61]  # Premier League, La Liga, Serie A, Bundesliga, Ligue 1
        results = []

        for league_code in league_codes:
            result = fetch_and_store_league_data.delay(league_code, year)
            results.append(result.id)

        return {"status": "scheduled", "task_ids": results}

    return {
        'fetch_and_store_league_data': fetch_and_store_league_data,
        'refresh_all_leagues': refresh_all_leagues
    }

# Enhanced data retrieval with caching
def get_league_data_with_cache(league_code: int, year: int) -> dict:
    """Get league data with database caching fallback"""

    # Try database cache first
    cache_key_standings = f"standings_{league_code}_{year}"
    cache_key_scorers = f"scorers_{league_code}_{year}"
    cache_key_assists = f"assists_{league_code}_{year}"

    standings = DataService.get_cached_data(cache_key_standings)
    scorers = DataService.get_cached_data(cache_key_scorers)
    assists = DataService.get_cached_data(cache_key_assists)

    # If cache miss, fetch from API and cache
    if not standings:
        standings = fetch_stats(league_code, year)
        if standings:
            DataService.cache_data(cache_key_standings, standings)

    if not scorers:
        scorers = fetch_top_scorers(league_code, year)
        if scorers:
            DataService.cache_data(cache_key_scorers, scorers)

    if not assists:
        assists = fetch_top_assists(league_code, year)
        if assists:
            DataService.cache_data(cache_key_assists, assists)

    return {
        'standings': standings,
        'top_scorers': scorers,
        'top_assists': assists
    }