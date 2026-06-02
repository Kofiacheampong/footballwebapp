import os
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class League(db.Model):
    __tablename__ = 'league'
    id = db.Column(db.Integer, primary_key=True)
    api_id = db.Column(db.Integer, unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    country = db.Column(db.String(100))
    logo_url = db.Column(db.String(255))

    teams = db.relationship('Team', backref='league', lazy='dynamic')
    player_stats = db.relationship('PlayerStats', backref='league', lazy='dynamic')

    def __repr__(self):
        return f'<League {self.name}>'


class Team(db.Model):
    __tablename__ = 'team'
    id = db.Column(db.Integer, primary_key=True)
    api_id = db.Column(db.Integer, unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    logo_url = db.Column(db.String(255))
    league_id = db.Column(db.Integer, db.ForeignKey('league.id'))

    player_stats = db.relationship('PlayerStats', backref='team', lazy='dynamic')

    def __repr__(self):
        return f'<Team {self.name}>'


class Player(db.Model):
    __tablename__ = 'player'
    id = db.Column(db.Integer, primary_key=True)
    api_id = db.Column(db.Integer, unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer)
    nationality = db.Column(db.String(100))
    photo_url = db.Column(db.String(255))

    stats = db.relationship('PlayerStats', backref='player', lazy='dynamic')

    def __repr__(self):
        return f'<Player {self.name}>'


class PlayerStats(db.Model):
    __tablename__ = 'player_stats'
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

    __table_args__ = (
        db.UniqueConstraint('player_id', 'team_id', 'league_id', 'season', name='uq_player_stats'),
    )

    def __repr__(self):
        return f'<PlayerStats {self.player_id} - {self.season}>'