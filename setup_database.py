"""
Database Setup Script
Creates the SQLite database and populates it with initial country data.
Run this once to initialize the database.
"""

import sqlite3

# --- CONFIGURATION ---
DATABASE_FILE = 'countries.db'

# --- INITIAL DATA ---
# Same 30 countries from your original dictionary
INITIAL_COUNTRIES = [
    ("United States", "Washington D.C."),
    ("United Kingdom", "London"),
    ("France", "Paris"),
    ("Germany", "Berlin"),
    ("Japan", "Tokyo"),
    ("China", "Beijing"),
    ("India", "New Delhi"),
    ("Brazil", "Brasilia"),
    ("Australia", "Canberra"),
    ("Canada", "Ottawa"),
    ("Italy", "Rome"),
    ("Spain", "Madrid"),
    ("Russia", "Moscow"),
    ("South Korea", "Seoul"),
    ("Mexico", "Mexico City"),
    ("Indonesia", "Jakarta"),
    ("Netherlands", "Amsterdam"),
    ("Switzerland", "Bern"),
    ("Sweden", "Stockholm"),
    ("Norway", "Oslo"),
    ("Denmark", "Copenhagen"),
    ("Poland", "Warsaw"),
    ("Argentina", "Buenos Aires"),
    ("Egypt", "Cairo"),
    ("South Africa", "Pretoria"),
    ("Thailand", "Bangkok"),
    ("Vietnam", "Hanoi"),
    ("Turkey", "Ankara"),
    ("Greece", "Athens"),
    ("Portugal", "Lisbon"),
]


def create_database():
    """Create the database and table."""
    
    # Connect to database (creates file if it doesn't exist)
    print(f"Connecting to {DATABASE_FILE}...")
    conn = sqlite3.connect(DATABASE_FILE)
    
    # A cursor is how you execute SQL commands
    cursor = conn.cursor()
    
    # Create the table
    print("Creating countries table...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS countries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            country TEXT NOT NULL UNIQUE,
            capital TEXT NOT NULL
        )
    ''')
    
    # Explanation of the SQL above:
    # - CREATE TABLE IF NOT EXISTS: Only create if it doesn't already exist
    # - id INTEGER PRIMARY KEY AUTOINCREMENT: Auto-incrementing unique ID (1, 2, 3...)
    # - country TEXT NOT NULL UNIQUE: Text field, required, no duplicates allowed
    # - capital TEXT NOT NULL: Text field, required
    
    # Check if table is empty before inserting
    cursor.execute('SELECT COUNT(*) FROM countries')
    count = cursor.fetchone()[0]
    
    if count == 0:
        print(f"Inserting {len(INITIAL_COUNTRIES)} countries...")
        cursor.executemany(
            'INSERT INTO countries (country, capital) VALUES (?, ?)',
            INITIAL_COUNTRIES
        )
        # The ? marks are placeholders - SQLite fills them with the tuple values
        # This prevents SQL injection attacks
    else:
        print(f"Table already has {count} countries. Skipping insert.")
    
    # Save (commit) the changes
    conn.commit()
    
    # Close the connection
    conn.close()
    
    print("Database setup complete!")


def verify_database():
    """Print all countries to verify setup worked."""
    
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, country, capital FROM countries ORDER BY country')
    rows = cursor.fetchall()
    
    print(f"\n--- Database contains {len(rows)} countries ---")
    for row in rows[:5]:  # Show first 5
        print(f"  {row[0]}: {row[1]} -> {row[2]}")
    print("  ...")
    
    conn.close()


if __name__ == '__main__':
    create_database()
    verify_database()
