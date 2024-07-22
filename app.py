import os
from flask import Flask, render_template, jsonify
from dotenv import load_dotenv
import requests
from stats_data import fetch_top_assists, fetch_stats, fetch_top_scorers

load_dotenv()

app = Flask(__name__)


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
        top_scorers = fetch_top_scorers(league_code)
        top_assists = fetch_top_assists(league_code)
        
        if standings and 'response' in standings and top_scorers and 'response' in top_scorers and top_assists and 'response' in top_assists:
            # Slice the lists to get the top 10
            top_scorers = top_scorers['response'][:10]
            top_assists = top_assists['response'][:10]
            
            return render_template(
                'league.html', 
                standings=standings['response'],
                league_name=league_name.replace('-', ' ').title(),
                top_scorers=top_scorers,
                top_assists=top_assists
            )
        else:
            return "Could not fetch data", 500
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

@app.route('/top-assists')
def top_assists():
    league_codes = [39, 140, 135, 78, 61]
    assists_list = []
    
    for code in league_codes:
        data = fetch_top_assists(code)
        if data:
            assists_list.extend(data['response'])
    
    # Sort the list by assists, ensuring we handle missing keys gracefully
    assists_list.sort(
        key=lambda x: x['statistics'][0]['goals']['assists'] if 'assists' in x['statistics'][0]['goals'] else 0, 
        reverse=True
    )
    
    return render_template('top_assists.html', assists_list=assists_list)

if __name__ == '__main__':
    app.run(debug=True)