import os
from flask import Flask, render_template, jsonify,request
from dotenv import load_dotenv
import requests
from stats_data import fetch_top_assists, fetch_stats, fetch_top_scorers, get_league_logos, fetch_player_stats_by_name, extract_player_data, league_logos_processor

load_dotenv()

app = Flask(__name__)

app.context_processor(league_logos_processor)


@app.route('/')
def index():
    year = request.args.get('year', '2023')
    league_logos = get_league_logos()
    league_codes = {
        'premier-league': 39,
        'la-liga': 140,
        'serie-a': 135,
        'bundesliga': 78,
        'ligue-1': 61
    }

    return render_template('index.html', year = year,league_logos = league_logos, league_codes = league_codes)

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
    year = request.args.get('year', '2023')
    league_logos = get_league_logos()

    if league_code:
        standings = fetch_stats(league_code,year)
        top_scorers = fetch_top_scorers(league_code,year)
        top_assists = fetch_top_assists(league_code,year)
        
        if standings and 'response' in standings and top_scorers and 'response' in top_scorers and top_assists and 'response' in top_assists:
            # Slice the lists to get the top 10
            top_scorers = top_scorers['response'][:10]
            top_assists = top_assists['response'][:10]
            
            return render_template(
                'league.html', 
                standings=standings['response'],
                league_name=league_name.replace('-', ' ').title(),
                top_scorers=top_scorers,
                top_assists=top_assists,
                year = year,
                league_logos = league_logos
            )
        else:
            return "Could not fetch data", 500
    else:
        return "League not found", 404

@app.route('/top-scorer')
def top_scorer():
    year = request.args.get('year','2023')
    league_codes = [39, 140, 135, 78, 61]
    top_scorers = []
    league_logos = get_league_logos()

    
    for code in league_codes:
        data = fetch_top_scorers(code, year)
        if data and 'response' in data:
            top_scorers.extend(data['response'])
    
    top_scorers.sort(key=lambda x: x['statistics'][0]['goals']['total'], reverse=True)
    return render_template('top_scorer.html', top_scorers=top_scorers,year = year,league_logos= league_logos)

@app.route('/top-assists')
def top_assists():
    year = request.args.get('year','2023')
    league_codes = [39, 140, 135, 78, 61]
    assists_list = []
    league_logos = get_league_logos()

    
    for code in league_codes:
        data = fetch_top_assists(code,year)
        if data:
            assists_list.extend(data['response'])
    
    # Sort the list by assists, ensuring we handle missing keys gracefully
    assists_list.sort(
        key=lambda x: x['statistics'][0]['goals']['assists'] if 'assists' in x['statistics'][0]['goals'] else 0, 
        reverse=True
    )
    
    return render_template('top_assists.html', assists_list=assists_list, year = year, league_codes = league_codes,league_logos = league_logos)

@app.route('/player_comparison', methods=['GET'])
def compare_players():
    player1_name = request.args.get('player1')
    player2_name = request.args.get('player2')
    # league_code = request.args.get('league')
    year = request.args.get('year', '2023')  # Default year to 2023 if not provided
    
    league_logos = {
        'Premier League': 'https://example.com/epl_logo.png',
        'La Liga': 'https://example.com/la_liga_logo.png',
        'Serie A': 'https://example.com/serie_a_logo.png',
        'Bundesliga': 'https://example.com/bundesliga_logo.png',
        'Ligue 1': 'https://example.com/ligue_1_logo.png'
    }


    if player1_name and player2_name:
        player1_data = fetch_player_stats_by_name(player1_name,year)
        player2_data = fetch_player_stats_by_name(player2_name,year)

        player1_details = extract_player_data(player1_data)
        player2_details = extract_player_data(player2_data)
    else:
        player1_details, player2_details = None, None

    return render_template('player_comparison.html', player1=player1_details, player2=player2_details)

if __name__ == '__main__':
    app.run(debug=True)