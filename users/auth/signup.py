from functools import wraps
from flask import  render_template, request, redirect, url_for, flash, session
from flask_mail import Mail
from users.auth.utils_signup import (
    clear_signup_session, is_valid_email, is_password_secure,
    generate_otp, send_signup_email_otp
)
from flask_limiter.util import get_remote_address
from extensions import limiter
from users.auth.user_db import UserOperation
import bcrypt
import time
from users import users_bp

mail = Mail()
user_op = UserOperation()

def limit_by_signup_email(limit="3 per minute"):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            email = session.get('signup_data', {}).get('email')
            if email:
                key_func = lambda: email
            else:
                key_func = get_remote_address
            return limiter.limit(limit, key_func=key_func)(f)(*args, **kwargs)
        return wrapped
    return decorator

@users_bp.route("/user_signup", methods=['GET', 'POST'])
def user_signup():
    if 'email' in session and 'username' in session:
        flash("You are already logged in.", 'info')
        return redirect(url_for('index'))

    if 'signup_data' not in session:
        session['signup_data'] = {}

    signup_data = session['signup_data']

    if request.args.get('go_back'):
        if 'password' in signup_data:
            signup_data.pop('password')
        elif 'email' in signup_data:
            signup_data.pop('email')
        elif 'username' in signup_data:
            signup_data.pop('username')
        session.modified = True
        return redirect(url_for('users.user_signup'))

    if request.method == 'POST':
        if 'username' not in signup_data:
            username = request.form.get('username', '').strip()
            if username:
                signup_data['username'] = username
                flash("Username saved. Enter your email.", 'signup_success')
                return redirect(url_for('users.user_signup'))
            flash("Username is required.", 'signup_alerts')

        elif 'email' not in signup_data:
            email = request.form.get('email', '').strip()
            if not is_valid_email(email):
                flash("Invalid email format.", 'signup_alerts')
            elif user_op.get_user_by_email(email):
                flash("Email already exists.", 'signup_alerts')
            else:
                signup_data['email'] = email
                flash("Email saved. Enter your password.", 'signup_success')
                return redirect(url_for('users.user_signup'))

        elif 'password' not in signup_data:
            password = request.form.get('password', '').strip()
            if not is_password_secure(password):
                flash("Password must include uppercase, number, and special character.", 'signup_alerts')
            else:
                signup_data['password'] = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

                otp_value = generate_otp()
                session['otp_data'] = {
                    'otp': otp_value,
                    'email': signup_data['email'],
                    'username': signup_data['username'],
                    'password': signup_data['password'],
                    'timestamp': time.time()
                }
                session['otp_last_sent'] = time.time()

                try:
                    send_signup_email_otp(signup_data['username'], signup_data['email'], otp_value, mail)
                    flash("OTP sent to your email.", 'signup_success')
                    return redirect(url_for('users.user_email_otp_verify'))
                except Exception as e:
                    flash("Failed to send OTP. Try again.", 'signup_alerts')

    step = 'username'
    if 'username' in signup_data and 'email' not in signup_data:
        step = 'email'
    elif 'email' in signup_data and 'password' not in signup_data:
        step = 'password'

    return render_template("users/auth/user_signup.html", step=step, signup_data=signup_data)

@users_bp.route("/user_email_otp_verify", methods=['GET', 'POST'])
@limit_by_signup_email("3 per minute")
def user_email_otp_verify():
    otp_data = session.get('otp_data')
    signup_data = session.get('signup_data', {})

    # Go back option
    if request.args.get('go_back'):
        if otp_data:
            session['signup_data'] = {
                'username': otp_data.get('username'),
                'email': otp_data.get('email')
            }
            session.pop('otp_data', None)
            session.pop('otp_attempts', None)
        return redirect(url_for('users.user_signup'))

    # Already logged in
    if 'email' in session and 'username' in session:
        flash("You're already signed up!", 'signup_success')
        return redirect(url_for('index'))

    # OTP session missing or corrupted
    if not otp_data or not all(k in otp_data for k in ('otp', 'email', 'username', 'password', 'timestamp')):
        clear_signup_session()
        flash("OTP session expired or invalid. Please start signup again.", 'signup_alerts')
        return redirect(url_for('users.user_signup'))

    # OTP expired (5 minutes)
    if time.time() - otp_data['timestamp'] > 300:
        clear_signup_session()
        flash("OTP expired. Please restart signup.", 'signup_alerts')
        return redirect(url_for('users.user_signup'))

    # Ensure session email matches OTP email (no tampering)
    if otp_data['email'] != signup_data.get('email'):
        clear_signup_session()
        flash("Email mismatch detected. Signup process restarted for security.", 'signup_alerts')
        return redirect(url_for('users.user_signup'))

    if request.method == 'POST':
        user_otp = request.form.get('otp', '').strip()

        if not user_otp:
            flash("Please enter the OTP.", 'signup_alerts')

        elif user_otp != otp_data['otp']:
            session['otp_attempts'] = session.get('otp_attempts', 0) + 1

            if session['otp_attempts'] >= 5:
                clear_signup_session()
                flash("Too many failed attempts. Please start the signup again.", 'signup_alerts')
                return redirect(url_for('users.user_signup'))

            flash("Incorrect OTP. Try again.", 'signup_alerts')

        else:
            # Check again if user already exists before inserting
            if user_op.get_user_by_email(otp_data['email']):
                clear_signup_session()
                flash("User already exists. Please log in.", 'signup_alerts')
                return redirect(url_for('login'))

            user_op.user_signup_insert(
                otp_data['username'],
                otp_data['password'],
                otp_data['email'],
                is_verified=True
            )

            session['username'] = otp_data['username']
            session['email'] = otp_data['email']

            clear_signup_session()
            flash("Signup complete! Welcome.", 'signup_success')
            return redirect(url_for('index'))

    return render_template("users/auth/user_signup.html", step='otp', signup_data=signup_data)

@users_bp.route("/resend_otp", methods=['POST'])
@limit_by_signup_email("3 per minute")
def resend_otp():
    signup_data = session.get('signup_data', {})
    otp_data = session.get('otp_data', {})

    # Check essential fields
    if not all(k in signup_data for k in ('email', 'username')) or otp_data.get('email') != signup_data.get('email'):
        clear_signup_session()
        flash("Session invalid or expired. Please restart signup.", 'signup_alerts')
        return redirect(url_for('users.user_signup'))

    # Wait at least 60 seconds between resends
    if 'otp_last_sent' in session and time.time() - session['otp_last_sent'] < 60:
        wait_time = int(60 - (time.time() - session['otp_last_sent']))
        flash(f"Please wait {wait_time} seconds before resending OTP.", 'signup_alerts')
        return redirect(url_for('users.user_email_otp_verify'))

    # Generate and send new OTP
    otp_value = generate_otp()
    session['otp_data']['otp'] = otp_value
    session['otp_data']['timestamp'] = time.time()  # Reset OTP validity
    session['otp_last_sent'] = time.time()
    session['otp_attempts'] = 0  # Reset OTP attempt counter

    try:
        send_signup_email_otp(signup_data['username'], signup_data['email'], otp_value, mail)
        flash("A new OTP has been sent to your email.", 'signup_success')
    except Exception:
        flash("Failed to resend OTP. Please try again later.", 'signup_alerts')

    return redirect(url_for('users.user_email_otp_verify'))
