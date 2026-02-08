from flask import Flask, render_template, request, jsonify
import sqlite3

app = Flask(__name__)

DATABASE_FILE = 'countries.db'
S3_BUCKET = 'vishal-capital-app-images'
S3_REGION = 'us-east-1'
S3_BASE_URL = f'https://{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com'

MIN_LENGTH = 2
MAX_LENGTH = 100


def validate_input(value, field_name):
    if not value or not value.strip():
        return False, f'{field_name} cannot be empty.'
    cleaned = value.strip()
    if len(cleaned) < MIN_LENGTH:
        return False, f'{field_name} must be at least {MIN_LENGTH} characters.'
    if len(cleaned) > MAX_LENGTH:
        return False, f'{field_name} must be less than {MAX_LENGTH} characters.'
    return True, cleaned


def get_db_connection():
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def get_image_url(image_key):
    if image_key:
        return f'{S3_BASE_URL}/{image_key}'
    return None


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/get_capital', methods=['POST'])
def get_capital():
    country_raw = request.form.get('country', '')
    valid, result = validate_input(country_raw, 'Country')
    if not valid:
        return jsonify({'success': False, 'message': result}), 400
    country = result
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT country, capital, image_key FROM countries WHERE LOWER(country) = LOWER(?)', (country,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return jsonify({
            'success': True,
            'capital': row['capital'],
            'country': row['country'],
            'image_url': get_image_url(row['image_key'])
        })
    else:
        return jsonify({'success': False, 'message': f'Country "{country}" not found in database.'})


@app.route('/get_countries')
def get_countries():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT country FROM countries ORDER BY country')
    rows = cursor.fetchall()
    conn.close()
    return jsonify([row['country'] for row in rows])


@app.route('/add_capital', methods=['POST'])
def add_capital():
    country_raw = request.form.get('country', '')
    capital_raw = request.form.get('capital', '')
    valid, result = validate_input(country_raw, 'Country')
    if not valid:
        return jsonify({'success': False, 'message': result}), 400
    country = result
    valid, result = validate_input(capital_raw, 'Capital')
    if not valid:
        return jsonify({'success': False, 'message': result}), 400
    capital = result
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT country, capital FROM countries WHERE LOWER(country) = LOWER(?)', (country,))
    existing = cursor.fetchone()
    if existing:
        conn.close()
        return jsonify({'success': False, 'message': f'Country "{existing["country"]}" already exists.'}), 409
    try:
        cursor.execute('INSERT INTO countries (country, capital, image_key) VALUES (?, ?, NULL)', (country, capital))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': f'Added {country} with capital {capital}.'}), 201
    except sqlite3.Error as e:
        conn.close()
        return jsonify({'success': False, 'message': f'Database error: {str(e)}'}), 500


@app.route('/update_capital', methods=['POST'])
def update_capital():
    country_raw = request.form.get('country', '')
    capital_raw = request.form.get('capital', '')
    valid, result = validate_input(country_raw, 'Country')
    if not valid:
        return jsonify({'success': False, 'message': result}), 400
    country = result
    valid, result = validate_input(capital_raw, 'Capital')
    if not valid:
        return jsonify({'success': False, 'message': result}), 400
    new_capital = result
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, country, capital FROM countries WHERE LOWER(country) = LOWER(?)', (country,))
    existing = cursor.fetchone()
    if not existing:
        conn.close()
        return jsonify({'success': False, 'message': f'Country "{country}" not found.'}), 404
    old_capital = existing['capital']
    cursor.execute('UPDATE countries SET capital = ? WHERE id = ?', (new_capital, existing['id']))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': f'Updated {existing["country"]}: {old_capital} to {new_capital}'})


@app.route('/delete_country', methods=['POST'])
def delete_country():
    country_raw = request.form.get('country', '')
    valid, result = validate_input(country_raw, 'Country')
    if not valid:
        return jsonify({'success': False, 'message': result}), 400
    country = result
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, country, capital FROM countries WHERE LOWER(country) = LOWER(?)', (country,))
    existing = cursor.fetchone()
    if not existing:
        conn.close()
        return jsonify({'success': False, 'message': f'Country "{country}" not found.'}), 404
    cursor.execute('DELETE FROM countries WHERE id = ?', (existing['id'],))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': f'Deleted {existing["country"]} (capital was {existing["capital"]})'})


if __name__ == '__main__':
    app.run(debug=True)
