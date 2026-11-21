"""
=============================================================================
EduConnect - Main Flask Application
Educational Resource & Discovery Platform
=============================================================================
"""

from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config
from db import get_db_connection

# Initialize the Flask application
app = Flask(__name__)

# Load settings from config.py
app.config.from_object(Config)


# ---------------------------------------------------------------------------
# 1. Homepage Route
# ---------------------------------------------------------------------------
@app.route('/')
def home():
    """
    Renders the EduConnect Homepage.
    Displays hero search, categories, featured platforms, recent courses, and rankings.
    """
    return render_template('index.html')


# ---------------------------------------------------------------------------
# 2. Educational Platforms Explorer (Phase 5 - Connected to MySQL)
# ---------------------------------------------------------------------------
@app.route('/platforms')
def organizations():
    """
    Educational Platform Explorer route.
    Fetches organisations from MySQL with real-time search and pricing filters.
    """
    search_query = request.args.get('q', '').strip()
    selected_pricing = request.args.get('pricing', '').strip()

    conn = get_db_connection()
    if not conn:
        flash("Could not connect to the database. Please verify MySQL is running.", "danger")
        return render_template('organizations.html', organizations=[], search_query=search_query, selected_pricing=selected_pricing)

    try:
        cursor = conn.cursor(dictionary=True)

        # Dynamic SQL query with parameterized filters to prevent SQL Injection
        sql = "SELECT * FROM organizations WHERE 1=1"
        params = []

        if search_query:
            sql += " AND (name LIKE %s OR subjects LIKE %s OR description LIKE %s)"
            wildcard = f"%{search_query}%"
            params.extend([wildcard, wildcard, wildcard])

        if selected_pricing in ['Free', 'Freemium', 'Paid']:
            sql += " AND pricing_type = %s"
            params.append(selected_pricing)

        # Order by highest rating and most votes
        sql += " ORDER BY rating DESC, total_votes DESC"

        cursor.execute(sql, tuple(params))
        orgs_list = cursor.fetchall()

        cursor.close()
        conn.close()

        return render_template(
            'organizations.html',
            organizations=orgs_list,
            search_query=search_query,
            selected_pricing=selected_pricing
        )

    except Exception as e:
        flash(f"Error fetching educational platforms: {e}", "danger")
        if conn and conn.is_connected():
            conn.close()
        return render_template('organizations.html', organizations=[], search_query=search_query, selected_pricing=selected_pricing)


# ---------------------------------------------------------------------------
# 3. Free Courses Directory (Phase 6 - Connected to MySQL)
# ---------------------------------------------------------------------------
@app.route('/courses')
def courses():
    """
    Free Courses Directory route.
    Fetches verified free courses from MySQL joining organizations and categories.
    Supports real-time search, category filtering, and certificate filtering.
    """
    search_query = request.args.get('q', '').strip()
    selected_category = request.args.get('category', '').strip()
    certificate_only = request.args.get('certificate', '') == '1'

    conn = get_db_connection()
    if not conn:
        flash("Could not connect to the database. Please verify MySQL is running.", "danger")
        return render_template(
            'courses.html',
            courses=[],
            categories=[],
            search_query=search_query,
            selected_category=selected_category,
            certificate_only=certificate_only
        )

    try:
        cursor = conn.cursor(dictionary=True)

        # 1. Fetch categories for dropdown filter
        cursor.execute("SELECT id, name, icon FROM categories ORDER BY name ASC")
        categories_list = cursor.fetchall()

        # 2. Relational SQL query joining courses, organizations, and categories
        sql = """
            SELECT 
                c.id, c.title, c.description, c.duration, c.certificate_available, c.course_url,
                o.name AS org_name, o.website_url AS org_website,
                cat.name AS category_name, cat.icon AS category_icon
            FROM courses c
            JOIN organizations o ON c.organization_id = o.id
            JOIN categories cat ON c.category_id = cat.id
            WHERE 1=1
        """
        params = []

        if search_query:
            sql += " AND (c.title LIKE %s OR c.description LIKE %s OR o.name LIKE %s)"
            wildcard = f"%{search_query}%"
            params.extend([wildcard, wildcard, wildcard])

        if selected_category:
            sql += " AND cat.name = %s"
            params.append(selected_category)

        if certificate_only:
            sql += " AND c.certificate_available = TRUE"

        sql += " ORDER BY c.id ASC"

        cursor.execute(sql, tuple(params))
        courses_list = cursor.fetchall()

        cursor.close()
        conn.close()

        return render_template(
            'courses.html',
            courses=courses_list,
            categories=categories_list,
            search_query=search_query,
            selected_category=selected_category,
            certificate_only=certificate_only
        )

    except Exception as e:
        flash(f"Error fetching free courses: {e}", "danger")
        if conn and conn.is_connected():
            conn.close()
        return render_template(
            'courses.html',
            courses=[],
            categories=[],
            search_query=search_query,
            selected_category=selected_category,
            certificate_only=certificate_only
        )


# ---------------------------------------------------------------------------
# 4. User Authentication: Registration, Login & Logout (Phase 7)
# ---------------------------------------------------------------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    Student Registration Route.
    Validates inputs, securely hashes password, and stores new student in MySQL.
    """
    # If already logged in, redirect to home
    if session.get('user_id'):
        flash("You are already logged in.", "info")
        return redirect(url_for('home'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Basic Validations
        if not username or not email or not password:
            flash("All fields are required.", "danger")
            return render_template('register.html')

        if len(password) < 6:
            flash("Password must be at least 6 characters long.", "danger")
            return render_template('register.html')

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template('register.html')

        conn = get_db_connection()
        if not conn:
            flash("Database connection failed. Please try again later.", "danger")
            return render_template('register.html')

        try:
            cursor = conn.cursor(dictionary=True)

            # Check if username or email is already registered
            cursor.execute("SELECT id FROM users WHERE username = %s OR email = %s", (username, email))
            existing_user = cursor.fetchone()

            if existing_user:
                flash("A student account with that username or email already exists.", "danger")
                cursor.close()
                conn.close()
                return render_template('register.html')

            # Hash the password securely
            password_hash = generate_password_hash(password)

            # Insert new student account
            insert_sql = "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)"
            cursor.execute(insert_sql, (username, email, password_hash))
            conn.commit()

            new_user_id = cursor.lastrowid
            cursor.close()
            conn.close()

            # Automatically log the student in after successful registration
            session['user_id'] = new_user_id
            session['username'] = username

            flash(f"🎉 Welcome to EduConnect, {username}! Your student account has been created.", "success")
            return redirect(url_for('home'))

        except Exception as e:
            flash(f"Registration error: {e}", "danger")
            if conn and conn.is_connected():
                conn.close()
            return render_template('register.html')

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Student Login Route.
    Verifies username/email and compares password hash.
    """
    # If already logged in, redirect to home
    if session.get('user_id'):
        flash("You are already logged in.", "info")
        return redirect(url_for('home'))

    if request.method == 'POST':
        identifier = request.form.get('identifier', '').strip()
        password = request.form.get('password', '')

        if not identifier or not password:
            flash("Please enter both username/email and password.", "danger")
            return render_template('login.html')

        conn = get_db_connection()
        if not conn:
            flash("Database connection failed. Please try again later.", "danger")
            return render_template('login.html')

        try:
            cursor = conn.cursor(dictionary=True)

            # Query user by either username or email
            cursor.execute("SELECT * FROM users WHERE username = %s OR email = %s", (identifier, identifier.lower()))
            user = cursor.fetchone()

            cursor.close()
            conn.close()

            # Verify user exists and password hash matches
            if user and check_password_hash(user['password_hash'], password):
                session['user_id'] = user['id']
                session['username'] = user['username']
                flash(f"Welcome back, {user['username']}! Logged in successfully.", "success")
                return redirect(url_for('home'))
            else:
                flash("Invalid username/email or password. Please try again.", "danger")
                return render_template('login.html')

        except Exception as e:
            flash(f"Login error: {e}", "danger")
            if conn and conn.is_connected():
                conn.close()
            return render_template('login.html')

    return render_template('login.html')


@app.route('/logout')
def logout():
    """
    Clears the student session and logs them out.
    """
    session.clear()
    flash("You have been logged out successfully.", "info")
    return redirect(url_for('home'))


# ---------------------------------------------------------------------------
# 5. Statistics Dashboard (Chart.js integration in Phase 9)
# ---------------------------------------------------------------------------
@app.route('/dashboard')
def dashboard():
    """
    Statistics Dashboard route.
    In Phase 9, this will render Chart.js graphs populated by live MySQL data.
    """
    flash("The Statistics Dashboard with Chart.js graphs will be built in Phase 9!", "info")
    return redirect(url_for('home'))


# ---------------------------------------------------------------------------
# 6. AI Learning Assistant (Gemini API integration in Phase 10)
# ---------------------------------------------------------------------------
@app.route('/ai-assistant')
def ai_assistant():
    """
    AI Assistant route.
    In Phase 10, this will provide an academic concept explainer using an AI API.
    """
    flash("The AI Learning Assistant module will be developed in Phase 10!", "info")
    return redirect(url_for('home'))


# ---------------------------------------------------------------------------
# 7. Error Handlers
# ---------------------------------------------------------------------------
@app.errorhandler(404)
def page_not_found(e):
    """
    Custom 404 handler for missing pages.
    """
    flash("The requested page was not found. Redirected to Homepage.", "danger")
    return redirect(url_for('home'))


# ---------------------------------------------------------------------------
# Application Entry Point
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    print("=" * 60)
    print("🚀 EduConnect Server is starting...")
    print(f"🌐 Local URL: http://127.0.0.1:{Config.PORT}")
    print(f"📚 Platforms Explorer: http://127.0.0.1:{Config.PORT}/platforms")
    print(f"🎓 Free Courses: http://127.0.0.1:{Config.PORT}/courses")
    print(f"🔑 Student Register: http://127.0.0.1:{Config.PORT}/register")
    print(f"🔐 Student Login: http://127.0.0.1:{Config.PORT}/login")
    print("=" * 60)
    app.run(host='0.0.0.0', port=Config.PORT, debug=Config.DEBUG)
