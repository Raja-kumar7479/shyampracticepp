from functools import wraps
from flask import flash, redirect, render_template, request, session, url_for, current_app as app
import time
import bcrypt
from flask_mail import Mail
from users.auth.user_db import UserOperation
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from extensions import limiter

from users import users_bp

user_op = UserOperation()
mail = Mail()

RATE_LIMIT_MAX_ATTEMPTS = 5
RATE_LIMIT_RESET_TIME = 300  # 5 minutes

def limit_by_session_email(limit="5 per minute"):
    def decorator(f):
        @wraps(f)
        @limiter.limit(limit, key_func=lambda: session.get('email') or get_remote_address())
        def wrapped(*args, **kwargs):
            return f(*args, **kwargs)
        return wrapped
    return decorator

@users_bp.route("/user_login", methods=['GET', 'POST'])
@limit_by_session_email("5 per minute")  # Limit attempts to 5 per minute based on email
def user_login():
    if 'username' in session and 'email' in session:
        flash("You are already logged in.", 'login_alerts')
        return redirect(url_for('index'))

    # Reset step on go_back
    if request.args.get('go_back'):
        session.pop('login_step', None)
        session.pop('email', None)
        return redirect(url_for('users.user_login'))

    # Rate limiting by session for login attempts
    if session.get('login_attempts', 0) >= RATE_LIMIT_MAX_ATTEMPTS:
        last_attempt_time = session.get('last_attempt_time', time.time())
        if time.time() - last_attempt_time < RATE_LIMIT_RESET_TIME:
            flash("Too many login attempts. Try again later.", 'login_alerts')
            return redirect(url_for('index'))
        else:
            # Reset after RATE_LIMIT_RESET_TIME (5 minutes)
            session.pop('login_attempts', None)
            session.pop('last_attempt_time', None)

    step = session.get('login_step', 'email')

    if request.method == 'POST':
        if step == 'email':
            email = request.form.get('email', '').strip().lower()

            if not email:
                flash("Please enter your email.", 'login_alerts')
                return redirect(url_for('users.user_login'))

            user = user_op.get_user_by_email(email)
            if not user:
                flash("No account found with this email.", 'login_alerts')
                return redirect(url_for('users.user_login'))

            session['email'] = email
            session['login_step'] = 'password'
            return redirect(url_for('users.user_login'))

        elif step == 'password':
            email = session.get('email')
            password = request.form.get('password', '').strip()

            if not email:
                flash("Session expired. Please enter your email again.", 'login_alerts')
                session.pop('login_step', None)
                return redirect(url_for('users.user_login'))

            user = user_op.get_user_by_email(email)
            if not user:
                flash("No account found. Please start again.", 'login_alerts')
                session.pop('email', None)
                session.pop('login_step', None)
                return redirect(url_for('users.user_login'))

            if not password:
                flash("Please enter your password.", 'login_alerts')
                return redirect(url_for('users.user_login'))

            if bcrypt.checkpw(password.encode('utf-8'), user[3].encode('utf-8')):
                session['username'] = user[2]
                session['email'] = user[1]
                session.pop('login_step', None)
                session.pop('login_attempts', None)
                session.pop('last_attempt_time', None)
                flash("Login successful!", 'success')
                return redirect(url_for('index'))
            else:
                # Track login attempts and set the last attempt time
                session['login_attempts'] = session.get('login_attempts', 0) + 1
                session['last_attempt_time'] = time.time()
                flash("Invalid password.", 'login_alerts')
                return redirect(url_for('users.user_login'))

    return render_template("users/auth/user_login.html", step=session.get('login_step', 'email'))

@users_bp.route('/logout')
def logout():
    session.clear()
    session.permanent = False
    response = redirect(url_for('index'))
    response.delete_cookie('session')
    flash("You have been logged out successfully.", 'logout_success')
    return response
