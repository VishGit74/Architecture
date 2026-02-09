from flask import Flask, render_template, request, jsonify
import os
import boto3
import io
from PIL import Image

app = Flask(__name__)

# Database configuration - use SQLite for tests, PostgreSQL for production
USE_SQLITE = os.environ.get('USE_SQLITE', 'false').lower() == 'true'

if USE_SQLITE:
    import sqlite3
    DATABASE_FILE = os.environ.get('DATABASE_FILE', 'countries.db')
else:
    import psycopg2
    import psycopg2.extras
    DB_HOST = os.environ.get('DB_HOST', 'capital-app-db.c4ta0e8oeblz.us-east-1.rds.amazonaws.com')
    DB_NAME = os.environ.get('DB_NAME', 'capitalapp')
    DB_USER = os.environ.get('DB_USER', 'capitaladmin')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', 'CapitalApp2026!')

# S3 configuration
S3_BUCKET = 'vishal-capital-app-images'
S3_REGION = 'us-east-1'
S3_BASE_URL = f'https://{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com'

MIN_LENGTH = 2
MAX_LENGTH = 100
MAX_IMAGE_WIDTH = 800

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

s3_client = boto3.client('s3', region_name=S3_REGION)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


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
    if USE_SQLITE:
        conn = sqlite3.connect(DATABASE_FILE)
        conn.row_factory = sqlite3.Row
        return conn
    else:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        return conn


def get_image_url(image_key):
    if image_key:
        return f'{S3_BASE_URL}/{image_key}'
    return f'{S3_BASE_URL}/images/placeholder.jpg'


def resize_image(file):
    image = Image.open(file)
    if image.mode == 'RGBA':
        background = Image.new('RGB', image.size, (255, 255, 255))
        background.paste(image, mask=image.split()[3])
        image = background
    elif image.mode != 'RGB':
        image = image.convert('RGB')
    if image.width > MAX_IMAGE_WIDTH:
        ratio = MAX_IMAGE_WIDTH / image.width
        new_height = int(image.height * ratio)
        image = image.resize((MAX_IMAGE_WIDTH, new_height), Image.LANCZOS)
    output = io.BytesIO()
    image.save(output, format='JPEG', quality=85)
    output.seek(0)
    return output


def upload_to_s3(file, country_name):
    safe_name = country_name.lower().replace(' ', '-')
    image_key = f'images/{safe_name}.jpg'
    try:
        resized = resize_image(file)
        s3_client.upload_fileobj(
            resized,
            S3_BUCKET,
            image_key,
            ExtraArgs={'ContentType': 'image/jpeg'}
        )
        return True, image_key
    except Exception as e:
        return False, str(e)


def db_execute(cursor, query, params=()):
    """Execute query with correct parameter style for current database."""
    if USE_SQLITE:
        # SQLite uses ? for parameters
        query = query.replace('%s', '?')
    cursor.execute(query, params)


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
    if USE_SQLITE:
        cursor = conn.cursor()
    else:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    db_execute(cursor, 'SELECT country, capital, image_key FROM countries WHERE LOWER(country) = LOWER(%s)', (country,))
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
    db_execute(cursor, 'SELECT country FROM countries ORDER BY country')
    rows = cursor.fetchall()
    conn.close()
    if USE_SQLITE:
        return jsonify([row['country'] for row in rows])
    else:
        return jsonify([row[0] for row in rows])


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
    if USE_SQLITE:
        cursor = conn.cursor()
    else:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    db_execute(cursor, 'SELECT country, capital FROM countries WHERE LOWER(country) = LOWER(%s)', (country,))
    existing = cursor.fetchone()
    if existing:
        conn.close()
        return jsonify({'success': False, 'message': f'Country "{existing["country"]}" already exists.'}), 409
    
    image_key = None
    if 'image' in request.files:
        file = request.files['image']
        if file and file.filename and allowed_file(file.filename):
            success, result = upload_to_s3(file, country)
            if success:
                image_key = result
            else:
                conn.close()
                return jsonify({'success': False, 'message': f'Image upload failed: {result}'}), 500
        elif file and file.filename:
            conn.close()
            return jsonify({'success': False, 'message': 'Invalid file type. Allowed: png, jpg, jpeg, gif, webp'}), 400
    
    try:
        db_execute(cursor, 'INSERT INTO countries (country, capital, image_key) VALUES (%s, %s, %s)', (country, capital, image_key))
        conn.commit()
        conn.close()
        message = f'Added {country} with capital {capital}.'
        if image_key:
            message += ' Image uploaded successfully.'
        return jsonify({'success': True, 'message': message}), 201
    except Exception as e:
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
    if USE_SQLITE:
        cursor = conn.cursor()
    else:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    db_execute(cursor, 'SELECT id, country, capital FROM countries WHERE LOWER(country) = LOWER(%s)', (country,))
    existing = cursor.fetchone()
    if not existing:
        conn.close()
        return jsonify({'success': False, 'message': f'Country "{country}" not found.'}), 404
    old_capital = existing['capital']
    db_execute(cursor, 'UPDATE countries SET capital = %s WHERE id = %s', (new_capital, existing['id']))
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
    if USE_SQLITE:
        cursor = conn.cursor()
    else:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    db_execute(cursor, 'SELECT id, country, capital FROM countries WHERE LOWER(country) = LOWER(%s)', (country,))
    existing = cursor.fetchone()
    if not existing:
        conn.close()
        return jsonify({'success': False, 'message': f'Country "{country}" not found.'}), 404
    db_execute(cursor, 'DELETE FROM countries WHERE id = %s', (existing['id'],))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': f'Deleted {existing["country"]} (capital was {existing["capital"]})'})


if __name__ == '__main__':
    app.run(debug=True)
