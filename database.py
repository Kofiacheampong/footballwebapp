# database.py
import os
import requests
from flask_sqlalchemy import SQLAlchemy
from flask import current_app
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Initialize the SQLAlchemy object
db = SQLAlchemy()

class League(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    api_id = db.Column(db.Integer, unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    country = db.Column(db.String(100))
    logo_url = db.Column(db.String(255))

    def __repr__(self):
        return f'<League {self.name}>'

class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    api_id = db.Column(db.Integer, unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    logo_url = db.Column(db.String(255))
    league_id = db.Column(db.Integer, db.ForeignKey('league.id'))

    league = db.relationship('League', backref='teams')

    def __repr__(self):
        return f'<Team {self.name}>'

class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    api_id = db.Column(db.Integer, unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer)
    nationality = db.Column(db.String(100))
    photo_url = db.Column(db.String(255))
    height = db.Column(db.String(20))
    weight = db.Column(db.String(20))

    def __repr__(self):
        return f'<Player {self.name}>'

class PlayerStats(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    league_id = db.Column(db.Integer, db.ForeignKey('league.id'), nullable=False)
    season = db.Column(db.Integer, nullable=False)
    appearances = db.Column(db.Integer, default=0)
    goals = db.Column(db.Integer, default=0)
    assists = db.Column(db.Integer, default=0)
    shots_total = db.Column(db.Integer, default=0)
    shots_on_target = db.Column(db.Integer, default=0)
    rating = db.Column(db.Float)
    yellow_cards = db.Column(db.Integer, default=0)
    red_cards = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    player = db.relationship('Player', backref='stats')
    team = db.relationship('Team', backref='player_stats')
    league = db.relationship('League', backref='player_stats')

    def __repr__(self):
        return f'<PlayerStats {self.player.name} - {self.season}>'

class APICache(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cache_key = db.Column(db.String(255), unique=True, nullable=False)
    data = db.Column(db.Text, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<APICache {self.cache_key}>'

def fetch_data_from_api(league_code, year):
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
        response.raise_for_status()
        data = response.json()

        if 'response' in data:
            return data['response']
        else:
            raise ValueError("Unexpected response format")

    except requests.RequestException as e:
        current_app.logger.error(f"API request failed: {str(e)}")
        return []
    except ValueError as ve:
        current_app.logger.error(f"Data parsing error: {str(ve)}")
        return []

def populate_database(league_code, year):
    data = fetch_data_from_api(league_code, year)

    for player in data:
        new_player = Player(
            name=player['name'],
            year=player['year'],
            goals=player.get('goals', 0),
            assists=player.get('assists', 0)
        )
        db.session.add(new_player)

    db.session.commit()