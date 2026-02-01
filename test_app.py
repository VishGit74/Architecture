"""
Unit tests for Country Capital Finder API.
Tests database operations and input validation.
"""

import pytest
import os
import sqlite3
from app import app, get_db_connection, validate_input

# --- TEST CONFIGURATION ---
TEST_DATABASE = 'test_countries.db'


@pytest.fixture
def client():
    """
    Set up a test client with a fresh test database.
    
    This fixture:
    1. Creates a test database before each test
    2. Provides a test client to make requests
    3. Cleans up the test database after each test
    """
    # Point app to test database instead of real one
    app.config['TESTING'] = True
    
    # Temporarily change the database file
    import app as app_module
    original_db = app_module.DATABASE_FILE
    app_module.DATABASE_FILE = TEST_DATABASE
    
    # Create test database with sample data
    conn = sqlite3.connect(TEST_DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS countries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            country TEXT NOT NULL UNIQUE,
            capital TEXT NOT NULL
        )
    ''')
    # Add a few test countries
    cursor.executemany(
        'INSERT INTO countries (country, capital) VALUES (?, ?)',
        [
            ('Japan', 'Tokyo'),
            ('France', 'Paris'),
            ('Germany', 'Berlin')
        ]
    )
    conn.commit()
    conn.close()
    
    # Provide the test client
    with app.test_client() as client:
        yield client
    
    # Cleanup: remove test database
    app_module.DATABASE_FILE = original_db
    if os.path.exists(TEST_DATABASE):
        os.remove(TEST_DATABASE)

# --- VALIDATION TESTS ---

def test_validate_input_success():
    """Valid input should return True and cleaned value."""
    valid, result = validate_input('  Japan  ', 'Country')
    assert valid == True
    assert result == 'Japan'  # Stripped of spaces


def test_validate_input_empty():
    """Empty input should fail."""
    valid, result = validate_input('', 'Country')
    assert valid == False
    assert 'empty' in result.lower()


def test_validate_input_only_spaces():
    """Input with only spaces should fail."""
    valid, result = validate_input('   ', 'Country')
    assert valid == False
    assert 'empty' in result.lower()


def test_validate_input_too_short():
    """Single character should fail."""
    valid, result = validate_input('X', 'Country')
    assert valid == False
    assert 'at least' in result.lower()


def test_validate_input_too_long():
    """Input over 100 characters should fail."""
    long_input = 'A' * 101
    valid, result = validate_input(long_input, 'Country')
    assert valid == False
    assert 'less than' in result.lower()

# --- GET CAPITAL TESTS ---

def test_get_capital_success(client):
    """Should return capital for valid country."""
    response = client.post('/get_capital', data={'country': 'Japan'})
    json_data = response.get_json()
    
    assert response.status_code == 200
    assert json_data['success'] == True
    assert json_data['capital'] == 'Tokyo'


def test_get_capital_case_insensitive(client):
    """Should find country regardless of case."""
    response = client.post('/get_capital', data={'country': 'JAPAN'})
    json_data = response.get_json()
    
    assert json_data['success'] == True
    assert json_data['capital'] == 'Tokyo'


def test_get_capital_not_found(client):
    """Should return error for unknown country."""
    response = client.post('/get_capital', data={'country': 'Narnia'})
    json_data = response.get_json()
    
    assert json_data['success'] == False
    assert 'not found' in json_data['message'].lower()


def test_get_capital_empty_input(client):
    """Should reject empty input."""
    response = client.post('/get_capital', data={'country': ''})
    json_data = response.get_json()
    
    assert response.status_code == 400
    assert json_data['success'] == False


# --- GET COUNTRIES TESTS ---

def test_get_countries(client):
    """Should return list of all countries."""
    response = client.get('/get_countries')
    json_data = response.get_json()
    
    assert response.status_code == 200
    assert isinstance(json_data, list)
    assert 'Japan' in json_data
    assert 'France' in json_data
    assert len(json_data) == 3  # We seeded 3 countries


# --- ADD CAPITAL TESTS ---

def test_add_capital_success(client):
    """Should add new country successfully."""
    response = client.post('/add_capital', data={
        'country': 'Spain',
        'capital': 'Madrid'
    })
    json_data = response.get_json()
    
    assert response.status_code == 201
    assert json_data['success'] == True
    assert 'Spain' in json_data['message']


def test_add_capital_duplicate(client):
    """Should reject duplicate country."""
    response = client.post('/add_capital', data={
        'country': 'Japan',
        'capital': 'Kyoto'
    })
    json_data = response.get_json()
    
    assert response.status_code == 409
    assert json_data['success'] == False
    assert 'already exists' in json_data['message'].lower()


def test_add_capital_empty_country(client):
    """Should reject empty country."""
    response = client.post('/add_capital', data={
        'country': '',
        'capital': 'TestCity'
    })
    json_data = response.get_json()
    
    assert response.status_code == 400
    assert json_data['success'] == False


def test_add_capital_empty_capital(client):
    """Should reject empty capital."""
    response = client.post('/add_capital', data={
        'country': 'TestCountry',
        'capital': ''
    })
    json_data = response.get_json()
    
    assert response.status_code == 400
    assert json_data['success'] == False


# --- UPDATE CAPITAL TESTS ---

def test_update_capital_success(client):
    """Should update existing country's capital."""
    response = client.post('/update_capital', data={
        'country': 'Japan',
        'capital': 'Kyoto'
    })
    json_data = response.get_json()
    
    assert response.status_code == 200
    assert json_data['success'] == True
    assert 'Tokyo' in json_data['message']  # Old capital
    assert 'Kyoto' in json_data['message']  # New capital


def test_update_capital_not_found(client):
    """Should reject update for non-existent country."""
    response = client.post('/update_capital', data={
        'country': 'Atlantis',
        'capital': 'Underwater City'
    })
    json_data = response.get_json()
    
    assert response.status_code == 404
    assert json_data['success'] == False


# --- DELETE COUNTRY TESTS ---

def test_delete_country_success(client):
    """Should delete existing country."""
    response = client.post('/delete_country', data={'country': 'Germany'})
    json_data = response.get_json()
    
    assert response.status_code == 200
    assert json_data['success'] == True
    assert 'Berlin' in json_data['message']  # Shows deleted capital


def test_delete_country_not_found(client):
    """Should reject delete for non-existent country."""
    response = client.post('/delete_country', data={'country': 'Atlantis'})
    json_data = response.get_json()
    
    assert response.status_code == 404
    assert json_data['success'] == False


def test_delete_country_empty(client):
    """Should reject empty country name."""
    response = client.post('/delete_country', data={'country': ''})
    json_data = response.get_json()
    
    assert response.status_code == 400
    assert json_data['success'] == False
