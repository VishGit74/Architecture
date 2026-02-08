"""
Unit tests for Country Capital Finder API.
Tests database operations and input validation.
"""

import pytest
import os
import sqlite3
from app import app, validate_input

TEST_DATABASE = 'test_countries.db'


@pytest.fixture
def client():
    """Set up a test client with a fresh test database."""
    app.config['TESTING'] = True
    
    import app as app_module
    original_db = app_module.DATABASE_FILE
    app_module.DATABASE_FILE = TEST_DATABASE
    
    conn = sqlite3.connect(TEST_DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS countries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            country TEXT NOT NULL UNIQUE,
            capital TEXT NOT NULL,
            image_key TEXT
        )
    ''')
    cursor.executemany(
        'INSERT INTO countries (country, capital, image_key) VALUES (?, ?, ?)',
        [
            ('Japan', 'Tokyo', 'images/tokyo.jpg'),
            ('France', 'Paris', None),
            ('Germany', 'Berlin', None)
        ]
    )
    conn.commit()
    conn.close()
    
    with app.test_client() as client:
        yield client
    
    app_module.DATABASE_FILE = original_db
    if os.path.exists(TEST_DATABASE):
        os.remove(TEST_DATABASE)


# --- VALIDATION TESTS ---

def test_validate_input_success():
    """Should return cleaned value for valid input."""
    valid, result = validate_input('  Japan  ', 'Country')
    assert valid is True
    assert result == 'Japan'


def test_validate_input_empty():
    """Should reject empty string."""
    valid, result = validate_input('', 'Country')
    assert valid is False
    assert 'cannot be empty' in result


def test_validate_input_only_spaces():
    """Should reject string with only spaces."""
    valid, result = validate_input('   ', 'Country')
    assert valid is False
    assert 'cannot be empty' in result


def test_validate_input_too_short():
    """Should reject input shorter than minimum length."""
    valid, result = validate_input('A', 'Country')
    assert valid is False
    assert 'at least' in result


def test_validate_input_too_long():
    """Should reject input longer than maximum length."""
    valid, result = validate_input('A' * 101, 'Country')
    assert valid is False
    assert 'less than' in result


# --- GET CAPITAL TESTS ---

def test_get_capital_success(client):
    """Should return capital for valid country."""
    response = client.post('/get_capital', data={'country': 'Japan'})
    json_data = response.get_json()
    
    assert response.status_code == 200
    assert json_data['success'] is True
    assert json_data['capital'] == 'Tokyo'
    assert json_data['country'] == 'Japan'
    assert 'image_url' in json_data


def test_get_capital_case_insensitive(client):
    """Should find country regardless of case."""
    response = client.post('/get_capital', data={'country': 'JAPAN'})
    json_data = response.get_json()
    
    assert response.status_code == 200
    assert json_data['success'] is True
    assert json_data['capital'] == 'Tokyo'


def test_get_capital_not_found(client):
    """Should return error for unknown country."""
    response = client.post('/get_capital', data={'country': 'Narnia'})
    json_data = response.get_json()
    
    assert response.status_code == 200
    assert json_data['success'] is False
    assert 'not found' in json_data['message']


def test_get_capital_empty_input(client):
    """Should return error for empty input."""
    response = client.post('/get_capital', data={'country': ''})
    json_data = response.get_json()
    
    assert response.status_code == 400
    assert json_data['success'] is False


# --- GET COUNTRIES TESTS ---

def test_get_countries(client):
    """Should return list of all countries."""
    response = client.get('/get_countries')
    json_data = response.get_json()
    
    assert response.status_code == 200
    assert isinstance(json_data, list)
    assert 'Japan' in json_data
    assert 'France' in json_data
    assert 'Germany' in json_data


# --- ADD CAPITAL TESTS ---

def test_add_capital_success(client):
    """Should add new country successfully."""
    response = client.post('/add_capital', data={
        'country': 'Spain',
        'capital': 'Madrid'
    })
    json_data = response.get_json()
    
    assert response.status_code == 201
    assert json_data['success'] is True
    assert 'Added' in json_data['message']


def test_add_capital_duplicate(client):
    """Should reject duplicate country."""
    response = client.post('/add_capital', data={
        'country': 'Japan',
        'capital': 'Kyoto'
    })
    json_data = response.get_json()
    
    assert response.status_code == 409
    assert json_data['success'] is False
    assert 'already exists' in json_data['message']


def test_add_capital_empty_country(client):
    """Should reject empty country name."""
    response = client.post('/add_capital', data={
        'country': '',
        'capital': 'Madrid'
    })
    json_data = response.get_json()
    
    assert response.status_code == 400
    assert json_data['success'] is False


def test_add_capital_empty_capital(client):
    """Should reject empty capital name."""
    response = client.post('/add_capital', data={
        'country': 'Spain',
        'capital': ''
    })
    json_data = response.get_json()
    
    assert response.status_code == 400
    assert json_data['success'] is False


# --- UPDATE CAPITAL TESTS ---

def test_update_capital_success(client):
    """Should update existing country's capital."""
    response = client.post('/update_capital', data={
        'country': 'Japan',
        'capital': 'Kyoto'
    })
    json_data = response.get_json()
    
    assert response.status_code == 200
    assert json_data['success'] is True
    assert 'Updated' in json_data['message']


def test_update_capital_not_found(client):
    """Should return error for non-existent country."""
    response = client.post('/update_capital', data={
        'country': 'Atlantis',
        'capital': 'Poseidon City'
    })
    json_data = response.get_json()
    
    assert response.status_code == 404
    assert json_data['success'] is False


# --- DELETE COUNTRY TESTS ---

def test_delete_country_success(client):
    """Should delete existing country."""
    response = client.post('/delete_country', data={'country': 'Germany'})
    json_data = response.get_json()
    
    assert response.status_code == 200
    assert json_data['success'] is True
    assert 'Deleted' in json_data['message']


def test_delete_country_not_found(client):
    """Should return error for non-existent country."""
    response = client.post('/delete_country', data={'country': 'Atlantis'})
    json_data = response.get_json()
    
    assert response.status_code == 404
    assert json_data['success'] is False


def test_delete_country_empty(client):
    """Should return error for empty country name."""
    response = client.post('/delete_country', data={'country': ''})
    json_data = response.get_json()
    
    assert response.status_code == 400
    assert json_data['success'] is False
