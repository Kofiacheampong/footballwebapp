# app.py
from flask import Flask, render_template
from stats_data import fetch_stats
from dotenv import load_dotenv
import os


app = Flask(__name__)

@app.route('/')
def home():
    api_key = os.getenv('APIKEY')  # Replace with your actual API key
    stats = fetch_stats(api_key)
    print(f"Fetched stats: {stats}")  # Print fetched data to verify
    return render_template('index.html', stats=stats)

if __name__ == '__main__':
    app.run(debug=True)