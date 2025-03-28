from flask import Flask, render_template, jsonify
from datetime import datetime
import json
import os

app = Flask(__name__)

def load_lunch_data():
    """Load lunch data from JSON file"""
    try:
        with open('lunch_data.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

@app.route('/')
def index():
    """Render the main page"""
    lunch_data = load_lunch_data()
    current_date = datetime.now().strftime('%Y-%m-%d')
    return render_template('index.html', 
                         lunch_data=lunch_data,
                         current_date=current_date)

@app.route('/api/lunch-deals')
def get_lunch_deals():
    """API endpoint to get lunch deals"""
    return jsonify(load_lunch_data())

if __name__ == '__main__':
    app.run(debug=True) 