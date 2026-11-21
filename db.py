"""
=============================================================================
EduConnect - Database Connection & Management Module
Handles MySQL connections using mysql.connector
=============================================================================
"""

import os
import mysql.connector
from mysql.connector import Error
from config import Config


def get_db_connection():
    """
    Establishes and returns a connection to the EduConnect MySQL database.
    Uses credentials loaded from Config (via environment variables).
    Returns None if connection fails.
    """
    try:
        connection = mysql.connector.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME,
            charset='utf8mb4'
        )
        return connection
    except Error as e:
        print(f"\n❌ MySQL Connection Error: {e}")
        print("💡 Helpful Troubleshooting Checklist:")
        print("  1. Is MySQL Server running on your system? (Check 'Services' app in Windows for 'MySQL80')")
        print("  2. Did you set your MySQL password in your '.env' file? (DB_PASSWORD=your_password)")
        print(f"  3. Attempted settings: Host={Config.DB_HOST}, Port={Config.DB_PORT}, User={Config.DB_USER}, Database={Config.DB_NAME}\n")
        return None


def execute_sql_file(cursor, file_path):
    """
    Reads an SQL file and executes its statements one by one.
    """
    if not os.path.exists(file_path):
        print(f"⚠️ SQL file not found: {file_path}")
        return False

    with open(file_path, 'r', encoding='utf-8') as f:
        sql_content = f.read()

    # Execute multi-statement SQL
    for result in cursor.execute(sql_content, multi=True):
        if result.with_rows:
            result.fetchall()
    return True


def init_db():
    """
    Automated Database Initializer.
    1. Connects to MySQL server (without specifying DB_NAME in case it doesn't exist yet).
    2. Runs database/schema.sql to create database and tables.
    3. Runs database/seed_data.sql to populate verified educational data.
    """
    print("=" * 60)
    print("🔧 Initializing EduConnect MySQL Database...")
    print(f"Connecting to MySQL at {Config.DB_HOST}:{Config.DB_PORT} as '{Config.DB_USER}'...")
    print("=" * 60)

    try:
        # Step 1: Connect to MySQL Server instance
        server_conn = mysql.connector.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD
        )
        cursor = server_conn.cursor()

        # Step 2: Run schema.sql
        base_dir = os.path.dirname(os.path.abspath(__file__))
        schema_path = os.path.join(base_dir, 'database', 'schema.sql')
        print("▶ Executing schema.sql (Creating database and tables)...")
        execute_sql_file(cursor, schema_path)
        server_conn.commit()
        print("✅ Tables created successfully: users, categories, organizations, courses, reviews, votes.")

        # Step 3: Run seed_data.sql
        seed_path = os.path.join(base_dir, 'database', 'seed_data.sql')
        print("▶ Executing seed_data.sql (Inserting verified platforms and courses)...")
        execute_sql_file(cursor, seed_path)
        server_conn.commit()
        print("✅ Seed data inserted successfully!")

        cursor.close()
        server_conn.close()

        print("=" * 60)
        print("🎉 EduConnect Database is 100% ready and populated!")
        print("=" * 60)
        return True

    except Error as e:
        print(f"\n❌ Initialization Failed: {e}")
        print("💡 Please check your DB_PASSWORD in .env or verify that MySQL is started.")
        return False


def test_db_diagnostics():
    """
    Runs a quick diagnostic check and prints table counts.
    """
    conn = get_db_connection()
    if not conn:
        return False

    cursor = conn.cursor(dictionary=True)
    print("\n--- EduConnect Database Status ---")
    
    for table in ['categories', 'organizations', 'courses', 'users', 'reviews', 'votes']:
        try:
            cursor.execute(f"SELECT COUNT(*) AS total FROM {table}")
            count = cursor.fetchone()['total']
            print(f"  • Table '{table}': {count} records")
        except Error as e:
            print(f"  • Table '{table}': Not ready ({e})")

    cursor.close()
    conn.close()
    return True


if __name__ == '__main__':
    # When run directly with 'python db.py', initialize and run diagnostics
    success = init_db()
    if success:
        test_db_diagnostics()
