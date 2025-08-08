from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_mail import Mail
from flask_limiter.util import get_remote_address
from extensions import limiter
from users.auth.utils_signup import (
    clear_signup_session, is_valid_email, is_password_secure,
    generate_otp, validate_otp, send_signup_email_otp, send_signup_success_email
)
from users.auth.user_db import UserOperation
import time
import bcrypt
from functools import wraps
import logging

from users import users_bp

mail = Mail()
user_op = UserOperation()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def limit_by_signup_email(limit="3 per minute"):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            email = session.get('user_signup_email')
            key_func = (lambda: email) if email else get_remote_address
            return limiter.limit(limit, key_func=key_func)(f)(*args, **kwargs)
        return wrapped
    return decorator

@users_bp.route("/user_signup", methods=['GET', 'POST'])
def user_signup():
    if 'user_email' in session and 'user_username' in session:
        flash("You're already logged in.", 'info')
        return redirect(url_for('users.login_success'))

    session.setdefault('user_signup_data', {})
    signup_data = session['user_signup_data']

    if request.args.get('go_back'):
        for field in ('user_signup_password', 'user_signup_email', 'user_signup_username'):
            if field in signup_data:
                signup_data.pop(field)
                session.modified = True
                break
        return redirect(url_for('users.user_signup'))

    if request.method == 'POST':
        if 'user_signup_username' not in signup_data:
            username = request.form.get('username', '').strip()
            if username:
                signup_data['user_signup_username'] = username
                flash("Username saved. Enter your email.", 'signup_info')
                logger.info(f"Signup: Username step completed for {username}")
                return redirect(url_for('users.user_signup'))
            flash("Username is required.", 'signup_warning')

        elif 'user_signup_email' not in signup_data:
            email = request.form.get('email', '').strip()
            if not is_valid_email(email):
                flash("Invalid email format.", 'signup_error')
            elif user_op.get_user_by_email(email):
                flash("Email already exists.", 'signup_error')
            else:
                signup_data['user_signup_email'] = email
                flash("Email saved. Enter your password.", 'signup_info')
                logger.info(f"Signup: Email step completed for {email}")
                return redirect(url_for('users.user_signup'))

        elif 'user_signup_password' not in signup_data:
            password = request.form.get('password', '').strip()
            if not is_password_secure(password):
                flash("Password must include uppercase, number, and special character.", 'signup_warning')
            else:
                hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
                signup_data['user_signup_password'] = hashed_pw

                otp_value = generate_otp()
                session['user_signup_otp_data'] = {
                    'otp': otp_value,
                    'timestamp': time.time(),
                    'user_signup_username': signup_data['user_signup_username'],
                    'user_signup_email': signup_data['user_signup_email'],
                    'user_signup_password': signup_data['user_signup_password']
                }
                session['user_signup_otp_last_sent'] = time.time()

                try:
                    send_signup_email_otp(signup_data['user_signup_username'], signup_data['user_signup_email'], otp_value, mail)
                    flash("OTP sent to your email.", 'signup_success')
                    logger.info(f"Signup: OTP sent to {signup_data['user_signup_email']}")
                    return redirect(url_for('users.user_email_otp_verify'))
                except Exception:
                    flash("Failed to send OTP. Try again.", 'signup_error')
                    logger.error("Signup: Failed to send OTP")

    step = 'username'
    if 'user_signup_username' in signup_data and 'user_signup_email' not in signup_data:
        step = 'email'
    elif 'user_signup_email' in signup_data and 'user_signup_password' not in signup_data:
        step = 'password'

    return render_template("users/auth/user_signup.html", step=step, signup_data=signup_data)

@users_bp.route("/user_email_otp_verify", methods=['GET', 'POST'])
@limit_by_signup_email("3 per minute")
def user_email_otp_verify():
    otp_data = session.get('user_signup_otp_data')
    signup_data = session.get('user_signup_data', {})

    if request.args.get('go_back'):
        session['user_signup_data'] = {
            'user_signup_username': otp_data.get('user_signup_username'),
            'user_signup_email': otp_data.get('user_signup_email')
        }
        session.pop('user_signup_otp_data', None)
        session.pop('user_signup_otp_attempts', None)
        return redirect(url_for('users.user_signup'))

    if not otp_data or time.time() - otp_data.get('timestamp', 0) > 300:
        clear_signup_session()
        flash("OTP expired or session invalid. Please restart signup.", 'signup_error')
        logger.warning("Signup: OTP expired or invalid session")
        return redirect(url_for('users.user_signup'))

    if otp_data['user_signup_email'] != signup_data.get('user_signup_email'):
        clear_signup_session()
        flash("Email mismatch. Signup restarted for safety.", 'signup_error')
        logger.error("Signup: Email mismatch during OTP verification")
        return redirect(url_for('users.user_signup'))

    if request.method == 'POST':
        user_otp = request.form.get('otp', '').strip()
        if not user_otp:
            flash("Enter OTP.", 'signup_warning')
        else:
            is_valid, message = validate_otp(user_otp)
            if not is_valid:
                session['user_signup_otp_attempts'] = session.get('user_signup_otp_attempts', 0) + 1
                if session['user_signup_otp_attempts'] >= 5:
                    clear_signup_session()
                    flash("Too many attempts. Restart signup.", 'signup_error')
                    logger.warning("Signup: Too many OTP attempts")
                    return redirect(url_for('users.user_signup'))
                flash(message, 'signup_error')
            else:
                if user_op.get_user_by_email(otp_data['user_signup_email']):
                    clear_signup_session()
                    flash("User already exists. Please log in.", 'signup_info')
                    logger.info("Signup: User already exists")
                    return redirect(url_for('users.user_login'))

                user_op.user_signup_insert(
                    otp_data['user_signup_username'],
                    otp_data['user_signup_password'],
                    otp_data['user_signup_email'],
                    is_verified=True
                )

                send_signup_success_email(otp_data['user_signup_username'], otp_data['user_signup_email'], mail)

                session['user_username'] = otp_data['user_signup_username']
                session['user_email'] = otp_data['user_signup_email']
                clear_signup_session()
                flash("Signup successful!", 'signup_success')
                logger.info(f"User signup successful for {otp_data['user_signup_email']}")
                return redirect(url_for('users.login_success'))

    return render_template("users/auth/user_signup.html", step='otp', signup_data=signup_data)

@users_bp.route("/user_resend_otp", methods=['POST'])
@limit_by_signup_email("3 per minute")
def user_resend_otp():
    signup_data = session.get('user_signup_data', {})
    otp_data = session.get('user_signup_otp_data', {})

    if not signup_data or otp_data.get('user_signup_email') != signup_data.get('user_signup_email'):
        clear_signup_session()
        flash("Session error. Restart signup.", 'signup_error')
        logger.error("Signup: Resend OTP failed due to session mismatch")
        return redirect(url_for('users.user_signup'))

    if time.time() - session.get('user_signup_otp_last_sent', 0) < 60:
        flash("Wait 60 seconds before resending OTP.", 'signup_warning')
        return redirect(url_for('users.user_email_otp_verify'))

    new_otp = generate_otp()
    session['user_signup_otp_data']['otp'] = new_otp
    session['user_signup_otp_data']['timestamp'] = time.time()
    session['user_signup_otp_last_sent'] = time.time()
    session['user_signup_otp_attempts'] = 0

    try:
        send_signup_email_otp(signup_data['user_signup_username'], signup_data['user_signup_email'], new_otp, mail)
        flash("New OTP sent to email.", 'signup_success')
        logger.info(f"Signup: New OTP sent to {signup_data['user_signup_email']}")
    except Exception:
        flash("OTP send failed. Try later.", 'signup_error')
        logger.error("Signup: Failed to resend OTP")

    return redirect(url_for('users.user_email_otp_verify'))
