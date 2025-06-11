from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_mail import Mail
from flask_limiter.util import get_remote_address
from extensions import limiter
from users.auth.utils_signup import (
    clear_signup_session, is_valid_email, is_password_secure,
    generate_otp, validate_otp, send_signup_email_otp,send_signup_success_email
)
from users.auth.user_db import UserOperation
import time
import bcrypt
from functools import wraps

from users import users_bp

mail = Mail()
user_op = UserOperation()

def limit_by_signup_email(limit="3 per minute"):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            email = session.get('signup_data', {}).get('email')
            key_func = (lambda: email) if email else get_remote_address
            return limiter.limit(limit, key_func=key_func)(f)(*args, **kwargs)
        return wrapped
    return decorator

@users_bp.route("/user_signup", methods=['GET', 'POST'])
def user_signup():
    if 'email' in session and 'username' in session:
        flash("You're already logged in.", 'info')
        return redirect(url_for('users.login_success'))

    session.setdefault('signup_data', {})
    signup_data = session['signup_data']

    if request.args.get('go_back'):
        for field in ('password', 'email', 'username'):
            if field in signup_data:
                signup_data.pop(field)
                session.modified = True
                break
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
                hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
                signup_data['password'] = hashed_pw

                otp_value = generate_otp()
                session['otp_data'] = {
                    'otp': otp_value,
                    'timestamp': time.time(),
                    **signup_data
                }
                session['otp_last_sent'] = time.time()

                try:
                    send_signup_email_otp(signup_data['username'], signup_data['email'], otp_value, mail)
                    flash("OTP sent to your email.", 'signup_success')
                    return redirect(url_for('users.user_email_otp_verify'))
                except Exception:
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

    if request.args.get('go_back'):
        session['signup_data'] = {
            'username': otp_data.get('username'),
            'email': otp_data.get('email')
        }
        session.pop('otp_data', None)
        session.pop('otp_attempts', None)
        return redirect(url_for('users.user_signup'))

    if not otp_data or time.time() - otp_data.get('timestamp', 0) > 300:
        clear_signup_session()
        flash("OTP expired or session invalid. Please restart signup.", 'signup_alerts')
        return redirect(url_for('users.user_signup'))

    if otp_data['email'] != signup_data.get('email'):
        clear_signup_session()
        flash("Email mismatch. Signup restarted for safety.", 'signup_alerts')
        return redirect(url_for('users.user_signup'))

    if request.method == 'POST':
        user_otp = request.form.get('otp', '').strip()
        if not user_otp:
            flash("Enter OTP.", 'signup_alerts')
        else:
            is_valid, message = validate_otp(user_otp)
            if not is_valid:
                session['otp_attempts'] = session.get('otp_attempts', 0) + 1
                if session['otp_attempts'] >= 5:
                    clear_signup_session()
                    flash("Too many attempts. Restart signup.", 'signup_alerts')
                    return redirect(url_for('users.user_signup'))
                flash(message, 'signup_alerts')
            else:
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

                send_signup_success_email(otp_data['username'], otp_data['email'], mail)

                session['username'] = otp_data['username']
                session['email'] = otp_data['email']
                clear_signup_session()
                flash("Signup successful!", 'signup_success')
                return redirect(url_for('users.login_success'))

    return render_template("users/auth/user_signup.html", step='otp', signup_data=signup_data)

@users_bp.route("/resend_otp", methods=['POST'])
@limit_by_signup_email("3 per minute")
def resend_otp():
    signup_data = session.get('signup_data', {})
    otp_data = session.get('otp_data', {})

    if not signup_data or otp_data.get('email') != signup_data.get('email'):
        clear_signup_session()
        flash("Session error. Restart signup.", 'signup_alerts')
        return redirect(url_for('users.user_signup'))

    if time.time() - session.get('otp_last_sent', 0) < 60:
        flash("Wait 60 seconds before resending OTP.", 'signup_alerts')
        return redirect(url_for('users.user_email_otp_verify'))

    new_otp = generate_otp()
    session['otp_data']['otp'] = new_otp
    session['otp_data']['timestamp'] = time.time()
    session['otp_last_sent'] = time.time()
    session['otp_attempts'] = 0

    try:
        send_signup_email_otp(signup_data['username'], signup_data['email'], new_otp, mail)
        flash("New OTP sent to email.", 'signup_success')
    except Exception:
        flash("OTP send failed. Try later.", 'signup_alerts')

    return redirect(url_for('users.user_email_otp_verify'))
