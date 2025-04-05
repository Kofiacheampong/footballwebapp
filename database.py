# database.py
import os
import requests
from flask_sqlalchemy import SQLAlchemy
from flask import current_app

from dotenv import load_dotenv
load_dotenv()

# Initialize the SQLAlchemy object
db = SQLAlchemy()

class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    goals = db.Column(db.Integer, default=0)
    assists = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f'<Player {self.name}>'

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