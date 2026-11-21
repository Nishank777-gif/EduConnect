"""
=============================================================================
EduConnect - Main Flask Application
Educational Resource & Discovery Platform
=============================================================================
"""

import re
import json
import urllib.request
import urllib.error
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config
from db import get_db_connection, auto_setup_cloud_db

# Initialize Flask Application
app = Flask(__name__)
app.config.from_object(Config)

# Automatically initialize cloud database if empty on startup
try:
    auto_setup_cloud_db()
except Exception as _e:
    pass


# ---------------------------------------------------------------------------
# Helper: Password Strength Validator
# ---------------------------------------------------------------------------
def is_password_strong(password):
    """
    Validates that a password satisfies security best practices:
    - At least 8 characters
    - At least one uppercase letter (A-Z)
    - At least one lowercase letter (a-z)
    - At least one numeric digit (0-9)
    - At least one special symbol (!@#$%^&*...)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter (A-Z)."
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter (a-z)."
    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one number (0-9)."
    if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=~`]', password):
        return False, "Password must contain at least one special character (!@#$%^&*...)."
    return True, ""


# ---------------------------------------------------------------------------
# 1. Homepage Route
# ---------------------------------------------------------------------------
@app.route('/')
def home():
    """
    Renders the EduConnect Homepage.
    Dynamically loads featured platforms, recent free courses, and top 10 rankings from MySQL.
    """
    featured_orgs = []
    recent_courses = []
    top_orgs = []

    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)

            # 1. Top 3 featured organisations
            cursor.execute("SELECT * FROM organizations ORDER BY rating DESC, total_votes DESC LIMIT 3")
            featured_orgs = cursor.fetchall()

            # 2. Top 3 recently added free courses
            cursor.execute("""
                SELECT c.*, o.name AS org_name, cat.name AS category_name
                FROM courses c
                JOIN organizations o ON c.organization_id = o.id
                JOIN categories cat ON c.category_id = cat.id
                ORDER BY c.id DESC LIMIT 3
            """)
            recent_courses = cursor.fetchall()

            # 3. Top 10 organisations for ranking table
            cursor.execute("SELECT * FROM organizations ORDER BY total_votes DESC, rating DESC LIMIT 10")
            top_orgs = cursor.fetchall()

            cursor.close()
            conn.close()
        except Exception as e:
            print(f"Notice: Failed to load dynamic homepage data ({e}). Falling back safely.")
            if conn and conn.is_connected():
                conn.close()

    return render_template(
        'index.html',
        featured_orgs=featured_orgs,
        recent_courses=recent_courses,
        top_orgs=top_orgs
    )


# ---------------------------------------------------------------------------
# 2. Educational Platforms Explorer & Detail (Phases 5 & 8)
# ---------------------------------------------------------------------------
@app.route('/platforms')
def organizations():
    """
    Platform Explorer route with live search and pricing filters.
    """
    search_query = request.args.get('q', '').strip()
    selected_pricing = request.args.get('pricing', '').strip()

    conn = get_db_connection()
    if not conn:
        flash("Database temporarily unavailable. Please verify MySQL is running.", "danger")
        return render_template('organizations.html', organizations=[], search_query=search_query, selected_pricing=selected_pricing)

    try:
        cursor = conn.cursor(dictionary=True)

        sql = "SELECT * FROM organizations WHERE 1=1"
        params = []

        if search_query:
            sql += " AND (name LIKE %s OR subjects LIKE %s OR description LIKE %s)"
            wildcard = f"%{search_query}%"
            params.extend([wildcard, wildcard, wildcard])

        if selected_pricing in ['Free', 'Freemium', 'Paid']:
            sql += " AND pricing_type = %s"
            params.append(selected_pricing)

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
        flash(f"Error fetching platforms: {e}", "danger")
        if conn and conn.is_connected():
            conn.close()
        return render_template('organizations.html', organizations=[], search_query=search_query, selected_pricing=selected_pricing)


@app.route('/platforms/<int:org_id>')
def organization_detail(org_id):
    """
    Platform detail page showing full description, community reviews, courses, and voting.
    """
    conn = get_db_connection()
    if not conn:
        flash("Database connection failed. Please check MySQL.", "danger")
        return redirect(url_for('organizations'))

    try:
        cursor = conn.cursor(dictionary=True)

        # 1. Fetch Organisation
        cursor.execute("SELECT * FROM organizations WHERE id = %s", (org_id,))
        org = cursor.fetchone()

        if not org:
            flash("Educational platform not found.", "danger")
            cursor.close()
            conn.close()
            return redirect(url_for('organizations'))

        # 2. Check if logged-in user has already voted
        has_voted = False
        user_id = session.get('user_id')
        if user_id:
            cursor.execute("SELECT id FROM votes WHERE user_id = %s AND organization_id = %s", (user_id, org_id))
            if cursor.fetchone():
                has_voted = True

        # 3. Fetch Reviews
        cursor.execute("""
            SELECT r.*, u.username 
            FROM reviews r
            JOIN users u ON r.user_id = u.id
            WHERE r.organization_id = %s
            ORDER BY r.created_at DESC
        """, (org_id,))
        reviews = cursor.fetchall()

        # 4. Fetch Courses offered by this platform
        cursor.execute("""
            SELECT c.*, cat.name AS category_name
            FROM courses c
            JOIN categories cat ON c.category_id = cat.id
            WHERE c.organization_id = %s
            ORDER BY c.title ASC
        """, (org_id,))
        courses_list = cursor.fetchall()

        cursor.close()
        conn.close()

        return render_template(
            'organization_detail.html',
            org=org,
            has_voted=has_voted,
            reviews=reviews,
            courses=courses_list
        )

    except Exception as e:
        flash(f"Error loading organisation details: {e}", "danger")
        if conn and conn.is_connected():
            conn.close()
        return redirect(url_for('organizations'))


# ---------------------------------------------------------------------------
# 3. Community Voting & Reviews System (Phase 8)
# ---------------------------------------------------------------------------
@app.route('/platforms/<int:org_id>/vote', methods=['POST'])
def vote_organization(org_id):
    """
    Handles student voting.
    Strictly prevents multiple votes by the same student for the same organisation.
    """
    user_id = session.get('user_id')
    if not user_id:
        flash("Please log in to vote for educational platforms.", "warning")
        return redirect(url_for('login'))

    conn = get_db_connection()
    if not conn:
        flash("Database connection error. Could not record vote.", "danger")
        return redirect(url_for('organization_detail', org_id=org_id))

    try:
        cursor = conn.cursor(dictionary=True)

        # Check for existing vote
        cursor.execute("SELECT id FROM votes WHERE user_id = %s AND organization_id = %s", (user_id, org_id))
        existing_vote = cursor.fetchone()

        if existing_vote:
            flash("You have already voted for this organisation. Only one vote per student is allowed.", "warning")
        else:
            # Insert vote into votes table
            cursor.execute("INSERT INTO votes (user_id, organization_id) VALUES (%s, %s)", (user_id, org_id))

            # Increment vote tally on organizations table
            cursor.execute("UPDATE organizations SET total_votes = total_votes + 1 WHERE id = %s", (org_id,))
            conn.commit()

            flash("🎉 Thank you! Your community vote has been recorded.", "success")

        cursor.close()
        conn.close()
        return redirect(url_for('organization_detail', org_id=org_id))

    except Exception as e:
        flash(f"Voting error: {e}", "danger")
        if conn and conn.is_connected():
            conn.close()
        return redirect(url_for('organization_detail', org_id=org_id))


@app.route('/platforms/<int:org_id>/review', methods=['POST'])
def submit_review(org_id):
    """
    Handles review submission and recalculates platform rating.
    """
    user_id = session.get('user_id')
    if not user_id:
        flash("Please log in to share your review.", "warning")
        return redirect(url_for('login'))

    try:
        rating = int(request.form.get('rating', 5))
        review_text = request.form.get('review_text', '').strip()

        if not review_text:
            flash("Please enter some feedback in your review.", "danger")
            return redirect(url_for('organization_detail', org_id=org_id))

        if rating < 1 or rating > 5:
            rating = 5

        conn = get_db_connection()
        if not conn:
            flash("Database connection error.", "danger")
            return redirect(url_for('organization_detail', org_id=org_id))

        cursor = conn.cursor(dictionary=True)

        # Insert review
        cursor.execute(
            "INSERT INTO reviews (user_id, organization_id, rating, review_text) VALUES (%s, %s, %s, %s)",
            (user_id, org_id, rating, review_text)
        )

        # Recalculate average rating for this organisation
        cursor.execute("SELECT AVG(rating) AS avg_rating FROM reviews WHERE organization_id = %s", (org_id,))
        res = cursor.fetchone()
        if res and res['avg_rating']:
            new_rating = round(float(res['avg_rating']), 2)
            cursor.execute("UPDATE organizations SET rating = %s WHERE id = %s", (new_rating, org_id))

        conn.commit()
        cursor.close()
        conn.close()

        flash("⭐ Thank you! Your review has been published.", "success")
        return redirect(url_for('organization_detail', org_id=org_id))

    except Exception as e:
        flash(f"Error submitting review: {e}", "danger")
        return redirect(url_for('organization_detail', org_id=org_id))


# ---------------------------------------------------------------------------
# 4. Free Courses Directory (Phase 6)
# ---------------------------------------------------------------------------
@app.route('/courses')
def courses():
    """
    Free Courses Directory with multi-table relational filtering.
    """
    search_query = request.args.get('q', '').strip()
    selected_category = request.args.get('category', '').strip()
    certificate_only = request.args.get('certificate', '') == '1'

    conn = get_db_connection()
    if not conn:
        flash("Could not connect to database.", "danger")
        return render_template('courses.html', courses=[], categories=[], search_query=search_query, selected_category=selected_category, certificate_only=certificate_only)

    try:
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT id, name, icon FROM categories ORDER BY name ASC")
        categories_list = cursor.fetchall()

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
        return render_template('courses.html', courses=[], categories=[], search_query=search_query, selected_category=selected_category, certificate_only=certificate_only)


# ---------------------------------------------------------------------------
# 5. Statistics Dashboard & Chart.js API (Phase 9)
# ---------------------------------------------------------------------------
@app.route('/dashboard')
def dashboard():
    """
    Statistics Dashboard displaying summary metrics, rankings, and Chart.js visualizations.
    """
    total_students = 0
    total_votes = 0
    total_courses = 0
    total_platforms = 0
    top_orgs = []

    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)

            cursor.execute("SELECT COUNT(*) AS total FROM users")
            total_students = cursor.fetchone()['total']

            cursor.execute("SELECT COALESCE(SUM(total_votes), 0) AS total FROM organizations")
            total_votes = cursor.fetchone()['total']

            cursor.execute("SELECT COUNT(*) AS total FROM courses")
            total_courses = cursor.fetchone()['total']

            cursor.execute("SELECT COUNT(*) AS total FROM organizations")
            total_platforms = cursor.fetchone()['total']

            cursor.execute("SELECT * FROM organizations ORDER BY total_votes DESC, rating DESC LIMIT 10")
            top_orgs = cursor.fetchall()

            cursor.close()
            conn.close()
        except Exception as e:
            flash(f"Notice: Failed to fetch live dashboard stats ({e}).", "warning")
            if conn and conn.is_connected():
                conn.close()

    return render_template(
        'dashboard.html',
        total_students=total_students,
        total_votes=total_votes,
        total_courses=total_courses,
        total_platforms=total_platforms,
        top_orgs=top_orgs
    )


@app.route('/api/stats')
def api_stats():
    """
    JSON API endpoint for Chart.js.
    Provides live statistics and vote distribution data for periodic dashboard refreshes.
    """
    conn = get_db_connection()
    if not conn:
        return jsonify({
            'total_students': 0,
            'total_votes': 0,
            'total_courses': 0,
            'total_platforms': 0,
            'top_organizations': []
        })

    try:
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT COUNT(*) AS total FROM users")
        total_students = cursor.fetchone()['total']

        cursor.execute("SELECT COALESCE(SUM(total_votes), 0) AS total FROM organizations")
        total_votes = cursor.fetchone()['total']

        cursor.execute("SELECT COUNT(*) AS total FROM courses")
        total_courses = cursor.fetchone()['total']

        cursor.execute("SELECT COUNT(*) AS total FROM organizations")
        total_platforms = cursor.fetchone()['total']

        cursor.execute("SELECT id, name, rating, total_votes, pricing_type FROM organizations ORDER BY total_votes DESC, rating DESC LIMIT 10")
        top_orgs = cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify({
            'total_students': total_students,
            'total_votes': total_votes,
            'total_courses': total_courses,
            'total_platforms': total_platforms,
            'top_organizations': top_orgs
        })

    except Exception as e:
        if conn and conn.is_connected():
            conn.close()
        return jsonify({'error': str(e)}), 500


# ---------------------------------------------------------------------------
# 6. AI Learning Assistant Module (Phase 10)
# ---------------------------------------------------------------------------
@app.route('/ai-assistant')
def ai_assistant():
    """
    Renders the AI Learning Assistant concept explainer interface.
    """
    return render_template('ai_assistant.html')


@app.route('/api/ai-explain', methods=['POST'])
def api_ai_explain():
    """
    API endpoint for concept explanation.
    Connects to Google's Gemini API if GEMINI_API_KEY is configured.
    Otherwise, returns a structured, student-friendly academic template.
    """
    data = request.get_json() or {}
    prompt = data.get('prompt', '').strip()
    subject = data.get('subject', 'General')

    if not prompt:
        return jsonify({'success': False, 'message': 'Please enter a concept or question to explain.'})

    api_key = Config.GEMINI_API_KEY.strip()

    # If user provided a real Gemini API key, call the Gemini REST API
    if api_key:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
            payload = {
                "contents": [{
                    "parts": [{
                        "text": f"You are a friendly, encouraging academic tutor for university and high school students. Explain this concept clearly in simple language with a relatable real-world analogy. Keep it structured and easy to digest.\nSubject: {subject}\nConcept/Question: {prompt}"
                    }]
                }]
            }
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode('utf-8'),
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            with urllib.request.urlopen(req, timeout=12) as response:
                result = json.loads(response.read().decode('utf-8'))
                explanation = result['candidates'][0]['content']['parts'][0]['text']
                return jsonify({'success': True, 'explanation': explanation, 'is_live': True})
        except Exception as e:
            print(f"Gemini API request note: {e}")

    # Fallback: Structured, high-quality educational breakdown template
    fallback_explanation = (
        f"📘 Topic: {subject}\n"
        f"🎯 Concept: {prompt}\n\n"
        f"1. Core Idea Explained Simply:\n"
        f"At its foundation, {prompt} is an essential concept in {subject}. "
        f"It allows learners and practitioners to organize principles systematically without unnecessary complexity.\n\n"
        f"2. Real-World Analogy:\n"
        f"Think of this like an organized library or a recipe kitchen: rather than searching every shelf randomly, "
        f"having clear rules and structured steps helps you find and execute what you need with maximum efficiency.\n\n"
        f"3. Key Takeaway for Students:\n"
        f"• Break the concept into fundamental components first.\n"
        f"• Practice with small, concrete examples before tackling advanced applications.\n"
        f"• Review free related courses on EduConnect under the '{subject}' category to master this skill!"
    )

    return jsonify({'success': True, 'explanation': fallback_explanation, 'is_live': False})


# ---------------------------------------------------------------------------
# 7. Student Authentication: Registration, Login & Logout (Phase 7)
# ---------------------------------------------------------------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    Student Registration Route with strong password validation.
    """
    if session.get('user_id'):
        flash("You are already logged in.", "info")
        return redirect(url_for('home'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Basic Checks
        if not username or not email or not password:
            flash("All fields are required.", "danger")
            return render_template('register.html')

        # Strong Password Verification
        is_strong, msg = is_password_strong(password)
        if not is_strong:
            flash(f"Password does not meet requirements: {msg}", "danger")
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

            cursor.execute("SELECT id FROM users WHERE username = %s OR email = %s", (username, email))
            existing_user = cursor.fetchone()

            if existing_user:
                flash("A student account with that username or email already exists.", "danger")
                cursor.close()
                conn.close()
                return render_template('register.html')

            password_hash = generate_password_hash(password)
            insert_sql = "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)"
            cursor.execute(insert_sql, (username, email, password_hash))
            conn.commit()

            new_user_id = cursor.lastrowid
            cursor.close()
            conn.close()

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
    """
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

            cursor.execute("SELECT * FROM users WHERE username = %s OR email = %s", (identifier, identifier.lower()))
            user = cursor.fetchone()

            cursor.close()
            conn.close()

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
# 8. Robust Error Handling (No Page Crashes)
# ---------------------------------------------------------------------------
@app.errorhandler(404)
def page_not_found(e):
    flash("The requested page was not found. Redirected to Homepage.", "info")
    return redirect(url_for('home'))


@app.errorhandler(500)
def internal_server_error(e):
    flash("An unexpected error occurred. Please try again or return to the homepage.", "danger")
    return redirect(url_for('home'))


# ---------------------------------------------------------------------------
# Application Entry Point
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    print("=" * 60)
    print("🚀 EduConnect Full Application Running")
    print(f"🌐 Homepage:            http://127.0.0.1:{Config.PORT}")
    print(f"📚 Platforms Explorer:  http://127.0.0.1:{Config.PORT}/platforms")
    print(f"🎓 Free Courses:        http://127.0.0.1:{Config.PORT}/courses")
    print(f"📊 Statistics Dashboard: http://127.0.0.1:{Config.PORT}/dashboard")
    print(f"🤖 AI Learning Assistant: http://127.0.0.1:{Config.PORT}/ai-assistant")
    print("=" * 60)
    app.run(host='0.0.0.0', port=Config.PORT, debug=Config.DEBUG)
