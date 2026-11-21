"""
=============================================================================
EduConnect - Database Connection & Management Module
Handles MySQL connections using mysql.connector with Cloud & Local support
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
    Automatically enables SSL when connecting to a remote cloud host (TiDB, Aiven, etc.).
    """
    try:
        connect_params = {
            'host': Config.DB_HOST,
            'port': int(Config.DB_PORT),
            'user': Config.DB_USER,
            'password': Config.DB_PASSWORD,
            'database': Config.DB_NAME,
            'charset': 'utf8mb4'
        }

        # If connecting to a remote cloud database (TiDB, Aiven, Clever Cloud, etc.)
        if Config.DB_HOST not in ('localhost', '127.0.0.1'):
            base_dir = os.path.dirname(os.path.abspath(__file__))
            cert_path = os.path.join(base_dir, 'database', 'Certificate', 'C.pem')

            if os.path.exists(cert_path):
                connect_params['ssl_ca'] = cert_path
                connect_params['ssl_disabled'] = False
            else:
                connect_params['ssl_disabled'] = False
                connect_params['ssl_verify_cert'] = False

        connection = mysql.connector.connect(**connect_params)
        return connection
    except Error as e:
        print(f"\n❌ MySQL Connection Error: {e}")
        print("💡 Helpful Troubleshooting Checklist:")
        if os.getenv('RENDER') and Config.DB_HOST in ('localhost', '127.0.0.1'):
            print("  🚨 ACTION REQUIRED ON RENDER:")
            print("  Render is trying to connect to 'localhost', but Render runs in the cloud!")
            print("  Please go to your Render Dashboard -> click 'Environment' -> add your TiDB/cloud variables:")
            print("  DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME")
        elif Config.DB_HOST in ('localhost', '127.0.0.1'):
            print("  1. If running locally: Is MySQL Server running on your system? (Check 'Services' app in Windows for 'MySQL80')")
        print(f"  Attempted settings: Host={Config.DB_HOST}, Port={Config.DB_PORT}, User={Config.DB_USER}, Database={Config.DB_NAME}\n")
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
    1. Connects to MySQL server.
    2. Runs database/schema.sql to create database and tables.
    3. Runs database/seed_data.sql to populate verified educational data.
    """
    print("=" * 60)
    print("🔧 Initializing EduConnect MySQL Database...")
    print(f"Connecting to MySQL at {Config.DB_HOST}:{Config.DB_PORT} as '{Config.DB_USER}'...")
    print("=" * 60)

    try:
        connect_params = {
            'host': Config.DB_HOST,
            'port': int(Config.DB_PORT),
            'user': Config.DB_USER,
            'password': Config.DB_PASSWORD
        }

        # Enable SSL for cloud databases
        if Config.DB_HOST not in ('localhost', '127.0.0.1'):
            base_dir = os.path.dirname(os.path.abspath(__file__))
            cert_path = os.path.join(base_dir, 'database', 'Certificate', 'C.pem')

            if os.path.exists(cert_path):
                connect_params['ssl_ca'] = cert_path
                connect_params['ssl_disabled'] = False
            else:
                connect_params['ssl_disabled'] = False
                connect_params['ssl_verify_cert'] = False

            if Config.DB_NAME:
                connect_params['database'] = Config.DB_NAME

        server_conn = mysql.connector.connect(**connect_params)
        cursor = server_conn.cursor()

        base_dir = os.path.dirname(os.path.abspath(__file__))

        # Step 2: Run schema.sql
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
        return False


def auto_setup_cloud_db():
    """
    Checks if tables are initialized; if not, automatically sets them up.
    Called on web server startup so remote databases are seeded automatically.
    """
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SHOW TABLES LIKE 'organizations'")
            exists = cursor.fetchone()
            cursor.close()
            conn.close()

            if not exists:
                print("▶ First-time setup detected: Seeding cloud database automatically...")
                init_db()
        except Exception as e:
            print(f"Auto setup check: {e}")


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
    success = init_db()
    if success:
        test_db_diagnostics()
