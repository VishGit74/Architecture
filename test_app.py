import pytest
from app import app, countries_capitals


# Create a test client (simulates a browser making requests)
@pytest.fixture
def client():
    """Set up a test client for our Flask app."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


# ----- TEST 1: Simple dictionary check -----
def test_countries_capitals_has_data():
    """Test that our dictionary is not empty."""
    assert len(countries_capitals) > 0, "Dictionary should have countries"


# ----- TEST 2: Check a known capital -----
def test_japan_capital_is_tokyo():
    """Test that Japan's capital is Tokyo."""
    assert countries_capitals["Japan"] == "Tokyo"


# ----- TEST 3: Test the API endpoint -----
def test_get_capital_success(client):
    """Test that /get_capital returns correct capital for valid country."""
    response = client.post('/get_capital', data={'country': 'France'})
    json_data = response.get_json()
    
    assert response.status_code == 200
    assert json_data['success'] == True
    assert json_data['capital'] == 'Paris'


# ----- TEST 4: Test invalid country -----
def test_get_capital_not_found(client):
    """Test that /get_capital handles unknown countries."""
    response = client.post('/get_capital', data={'country': 'Narnia'})
    json_data = response.get_json()
    
    assert response.status_code == 200
    assert json_data['success'] == False
