import os
from flask import Flask, render_template, jsonify
from dotenv import load_dotenv
import requests

load_dotenv()

app = Flask(__name__)

def fetch_stats(league_code):
    api_key = os.environ['API_KEY']
    headers = {
        'x-rapidapi-host': 'api-football-v1.p.rapidapi.com',
        'x-rapidapi-key': api_key
    }
    base_url = 'https://api-football-v1.p.rapidapi.com/v3/'
    endpoint = f'standings?league={league_code}&season=2023'
    url = base_url + endpoint
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None

def fetch_top_scorers(league_code):
    api_key = os.environ['API_KEY']
    headers = {
        'x-rapidapi-host': 'api-football-v1.p.rapidapi.com',
        'x-rapidapi-key': api_key
    }
    base_url = 'https://api-football-v1.p.rapidapi.com/v3/'
    endpoint = f'players/topscorers?league={league_code}&season=2023'
    url = base_url + endpoint
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/league/<league_name>')
def league(league_name):
    league_codes = {
        'premier-league': 39,
        'la-liga': 140,
        'serie-a': 135,
        'bundesliga': 78,
        'ligue-1': 61
    }
    
    league_code = league_codes.get(league_name.lower())
    if league_code:
        standings = fetch_stats(league_code)
        if standings:
            return render_template('league.html', standings=standings, league_name=league_name.replace('-', ' ').title())
        else:
            return "Could not fetch standings data", 500
    else:
        return "League not found", 404

@app.route('/top-scorer')
def top_scorer():
    league_codes = [39, 140, 135, 78, 61]
    top_scorers = []
    
    for code in league_codes:
        data = fetch_top_scorers(code)
        if data and 'response' in data:
            top_scorers.extend(data['response'])
    
    top_scorers.sort(key=lambda x: x['statistics'][0]['goals']['total'], reverse=True)
    return render_template('top_scorer.html', top_scorers=top_scorers)

if __name__ == '__main__':
    app.run(debug=True)