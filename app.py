from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Dictionary containing 30 country-capital pairs
countries_capitals = {
    "United States": "Washington D.C.",
    "United Kingdom": "London",
    "France": "Paris",
    "Germany": "Berlin",
    "Japan": "Tokyo",
    "China": "Beijing",
    "India": "New Delhi",
    "Brazil": "Brasilia",
    "Australia": "Canberra",
    "Canada": "Ottawa",
    "Italy": "Rome",
    "Spain": "Madrid",
    "Russia": "Moscow",
    "South Korea": "Seoul",
    "Mexico": "Mexico City",
    "Indonesia": "Jakarta",
    "Netherlands": "Amsterdam",
    "Switzerland": "Bern",
    "Sweden": "Stockholm",
    "Norway": "Oslo",
    "Denmark": "Copenhagen",
    "Poland": "Warsaw",
    "Argentina": "Buenos Aires",
    "Egypt": "Cairo",
    "South Africa": "Pretoria",
    "Thailand": "Bangkok",
    "Vietnam": "Hanoi",
    "Turkey": "Ankara",
    "Greece": "Athens",
    "Portugal": "Lisbon"
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_capital', methods=['POST'])
def get_capital():
    country = request.form.get('country', '').strip()

    # Case-insensitive search
    for key, value in countries_capitals.items():
        if key.lower() == country.lower():
            return jsonify({'success': True, 'capital': value, 'country': key})

    return jsonify({'success': False, 'message': f'Country "{country}" not found in database.'})

@app.route('/get_countries')
def get_countries():
    return jsonify(list(countries_capitals.keys()))

if __name__ == '__main__':
    app.run(debug=True)
