"""
Country Capital Finder - Flask Application
Now powered by SQLite database for persistent storage.
"""

from flask import Flask, render_template, request, jsonify
import sqlite3

app = Flask(__name__)

# --- DATABASE CONFIGURATION ---
DATABASE_FILE = 'countries.db'


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
    
    Old way (dictionary):
        capital = countries_capitals.get(country)
    
    New way (database):
        SELECT capital FROM countries WHERE country = ?
    """
    country = request.form.get('country', '').strip()
    
    if not country:
        return jsonify({'success': False, 'message': 'Please enter a country name.'})
    
    # Connect to database
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Search for the country (case-insensitive using LOWER())
    cursor.execute('''
        SELECT country, capital 
        FROM countries 
        WHERE LOWER(country) = LOWER(?)
    ''', (country,))
    
    # Note: (country,) is a tuple with one element
    # The comma is required! (country) without comma is just parentheses
    
    row = cursor.fetchone()  # Get first matching row (or None)
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
    
    Old way (dictionary):
        return jsonify(list(countries_capitals.keys()))
    
    New way (database):
        SELECT country FROM countries ORDER BY country
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT country FROM countries ORDER BY country')
    rows = cursor.fetchall()  # Get ALL rows as a list
    
    conn.close()
    
    # Convert rows to a simple list of country names
    countries = [row['country'] for row in rows]
    
    return jsonify(countries)


@app.route('/add_capital', methods=['POST'])
def add_capital():
    """
    Add a new country-capital pair.
    
    Old way (dictionary):
        countries_capitals[country] = capital
    
    New way (database):
        INSERT INTO countries (country, capital) VALUES (?, ?)
    """
    country = request.form.get('country', '').strip()
    capital = request.form.get('capital', '').strip()
    
    if not country or not capital:
        return jsonify({
            'success': False,
            'message': 'Both country and capital are required.'
        }), 400
    
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
        }), 409  # 409 = Conflict
    
    # Insert new country
    try:
        cursor.execute('''
            INSERT INTO countries (country, capital) 
            VALUES (?, ?)
        ''', (country, capital))
        
        conn.commit()  # Save the change! Without this, nothing is saved.
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'Added {country} with capital {capital}.'
        }), 201  # 201 = Created
        
    except sqlite3.Error as e:
        conn.close()
        return jsonify({
            'success': False,
            'message': f'Database error: {str(e)}'
        }), 500  # 500 = Server Error


@app.route('/update_capital', methods=['POST'])
def update_capital():
    """
    Update the capital of an existing country.
    
    SQL: UPDATE countries SET capital = ? WHERE country = ?
    
    Example usage:
        curl -X POST http://localhost:5000/update_capital \
             -d "country=Japan&capital=New Tokyo"
    """
    country = request.form.get('country', '').strip()
    new_capital = request.form.get('capital', '').strip()
    
    if not country or not new_capital:
        return jsonify({
            'success': False,
            'message': 'Both country and new capital are required.'
        }), 400
    
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
        }), 404  # 404 = Not Found
    
    old_capital = existing['capital']
    
    # Update the capital
    cursor.execute('''
        UPDATE countries 
        SET capital = ? 
        WHERE id = ?
    ''', (new_capital, existing['id']))
    
    conn.commit()  # Save changes
    conn.close()
    
    return jsonify({
        'success': True,
        'message': f'Updated {existing["country"]}: {old_capital} → {new_capital}'
    })


@app.route('/delete_country', methods=['POST'])
def delete_country():
    """
    Delete a country from the database.
    
    SQL: DELETE FROM countries WHERE country = ?
    
    Example usage:
        curl -X POST http://localhost:5000/delete_country \
             -d "country=Japan"
    """
    country = request.form.get('country', '').strip()
    
    if not country:
        return jsonify({
            'success': False,
            'message': 'Country name is required.'
        }), 400
    
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
    
    conn.commit()  # Save changes
    conn.close()
    
    return jsonify({
        'success': True,
        'message': f'Deleted {existing["country"]} (capital was {existing["capital"]})'
    })

if __name__ == '__main__':
    app.run(debug=True)
