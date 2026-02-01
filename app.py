"""
Country Capital Finder - Flask Application
Now powered by SQLite database for persistent storage.
"""

from flask import Flask, render_template, request, jsonify
import sqlite3

app = Flask(__name__)

# --- DATABASE CONFIGURATION ---
DATABASE_FILE = 'countries.db'

# --- VALIDATION RULES ---
MIN_LENGTH = 2
MAX_LENGTH = 100


def validate_input(value, field_name):
    """
    Validate a text input field.
    
    Returns:
        (True, cleaned_value) if valid
        (False, error_message) if invalid
    """
    # Check if empty
    if not value or not value.strip():
        return False, f'{field_name} cannot be empty.'
    
    cleaned = value.strip()
    
    # Check length
    if len(cleaned) < MIN_LENGTH:
        return False, f'{field_name} must be at least {MIN_LENGTH} characters.'
    
    if len(cleaned) > MAX_LENGTH:
        return False, f'{field_name} must be less than {MAX_LENGTH} characters.'
    
    return True, cleaned


def get_db_connection():
    """
    Create a connection to the SQLite database.
    
    Why a function? Each request needs its own connection.
    SQLite connections shouldn't be shared across requests.
    
    row_factory = sqlite3.Row allows us to access columns by name
    instead of by index (row['country'] vs row[0])
    """
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    return conn


# --- ROUTES ---

@app.route('/')
def index():
    """Serve the main HTML page."""
    return render_template('index.html')


@app.route('/get_capital', methods=['POST'])
def get_capital():
    """
    Look up a capital city by country name.
    """
    country_raw = request.form.get('country', '')
    
    # Validate input
    valid, result = validate_input(country_raw, 'Country')
    if not valid:
        return jsonify({'success': False, 'message': result}), 400
    country = result
    
    # Connect to database
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Search for the country (case-insensitive using LOWER())
    cursor.execute('''
        SELECT country, capital 
        FROM countries 
        WHERE LOWER(country) = LOWER(?)
    ''', (country,))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return jsonify({
            'success': True,
            'capital': row['capital'],
            'country': row['country']
        })
    else:
        return jsonify({
            'success': False,
            'message': f'Country "{country}" not found in database.'
        })


@app.route('/get_countries')
def get_countries():
    """
    Return list of all countries.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT country FROM countries ORDER BY country')
    rows = cursor.fetchall()
    
    conn.close()
    
    # Convert rows to a simple list of country names
    countries = [row['country'] for row in rows]
    
    return jsonify(countries)


@app.route('/add_capital', methods=['POST'])
def add_capital():
    """
    Add a new country-capital pair.
    """
    country_raw = request.form.get('country', '')
    capital_raw = request.form.get('capital', '')
    
    # Validate country
    valid, result = validate_input(country_raw, 'Country')
    if not valid:
        return jsonify({'success': False, 'message': result}), 400
    country = result
    
    # Validate capital
    valid, result = validate_input(capital_raw, 'Capital')
    if not valid:
        return jsonify({'success': False, 'message': result}), 400
    capital = result
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if country already exists
    cursor.execute('''
        SELECT country, capital 
        FROM countries 
        WHERE LOWER(country) = LOWER(?)
    ''', (country,))
    
    existing = cursor.fetchone()
    
    if existing:
        conn.close()
        return jsonify({
            'success': False,
            'message': f'Country "{existing["country"]}" already exists with capital "{existing["capital"]}".'
        }), 409
    
    # Insert new country
    try:
        cursor.execute('''
            INSERT INTO countries (country, capital) 
            VALUES (?, ?)
        ''', (country, capital))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'Added {country} with capital {capital}.'
        }), 201
        
    except sqlite3.Error as e:
        conn.close()
        return jsonify({
            'success': False,
            'message': f'Database error: {str(e)}'
        }), 500


@app.route('/update_capital', methods=['POST'])
def update_capital():
    """
    Update the capital of an existing country.
    """
    country_raw = request.form.get('country', '')
    capital_raw = request.form.get('capital', '')
    
    # Validate country
    valid, result = validate_input(country_raw, 'Country')
    if not valid:
        return jsonify({'success': False, 'message': result}), 400
    country = result
    
    # Validate capital
    valid, result = validate_input(capital_raw, 'Capital')
    if not valid:
        return jsonify({'success': False, 'message': result}), 400
    new_capital = result
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # First check if country exists
    cursor.execute('''
        SELECT id, country, capital 
        FROM countries 
        WHERE LOWER(country) = LOWER(?)
    ''', (country,))
    
    existing = cursor.fetchone()
    
    if not existing:
        conn.close()
        return jsonify({
            'success': False,
            'message': f'Country "{country}" not found.'
        }), 404
    
    old_capital = existing['capital']
    
    # Update the capital
    cursor.execute('''
        UPDATE countries 
        SET capital = ? 
        WHERE id = ?
    ''', (new_capital, existing['id']))
    
    conn.commit()
    conn.close()
    
    return jsonify({
        'success': True,
        'message': f'Updated {existing["country"]}: {old_capital} → {new_capital}'
    })


@app.route('/delete_country', methods=['POST'])
def delete_country():
    """
    Delete a country from the database.
    """
    country_raw = request.form.get('country', '')
    
    # Validate country
    valid, result = validate_input(country_raw, 'Country')
    if not valid:
        return jsonify({'success': False, 'message': result}), 400
    country = result
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # First check if country exists
    cursor.execute('''
        SELECT id, country, capital 
        FROM countries 
        WHERE LOWER(country) = LOWER(?)
    ''', (country,))
    
    existing = cursor.fetchone()
    
    if not existing:
        conn.close()
        return jsonify({
            'success': False,
            'message': f'Country "{country}" not found.'
        }), 404
    
    # Delete the country
    cursor.execute('DELETE FROM countries WHERE id = ?', (existing['id'],))
    
    conn.commit()
    conn.close()
    
    return jsonify({
        'success': True,
        'message': f'Deleted {existing["country"]} (capital was {existing["capital"]})'
    })


if __name__ == '__main__':
    app.run(debug=True)
