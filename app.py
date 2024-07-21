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
        retu