from functools import wraps
from flask import (
    render_template, request, redirect, url_for, session, flash, current_app as app
)
from flask_mail import Mail
from users.auth.utils_signup import is_password_secure
from users.auth.utils_forgot import send_otp_email
from flask_limiter.util import get_remote_address
from extensions import limiter
import time
import bcrypt
from users.auth.user_db import UserOperation

from users import users_bp
user_op = UserOperation()
mail = Mail()


def limit_by_session_email(limit="5 per minute"):
    def decorator(f):
        @wraps(f)
        @limiter.limit(limit, key_func=lambda: session.get('email') or get_remote_address())
        def wrapped(*args, **kwargs):
            return f(*args, **kwargs)
        return wrapped
    return decorator

@users_bp.route("/forgot_password", methods=['GET', 'POST'])
@limit_by_session_email("3 per minute")
def forgot_password():
    if 'email' in session and 'username' in session:
        flash("You are already logged in.", 'info')
        return redirect(url_for('index'))  # change 'dashboard' as needed

    step = session.get('step', 'email')
    go_back = request.args.get('go_back')

    if go_back:
        if go_back == '2':
            session.pop('otp', None)
            session['step'] = 'password'
            return redirect(url_for('users.forgot_password'))
        elif go_back == '1':
            session.pop('new_password', None)
            session['step'] = 'email'
            return redirect(url_for('users.forgot_password'))

    if request.method == 'POST':
        if step == 'email':
            email = request.form.get('email', '').strip()
            if not email:
                flash("Email is required.", 'forgot_alerts')
                return redirect(url_for('users.forgot_password'))

            user = user_op.get_user_by_email(email)
            if user:
                session['email'] = email
                session['step'] = 'password'
                flash("Email found! Please enter your new password.", 'forgot_success')
            else:
                flash("Email not registered.", 'forgot_alerts')
            return redirect(url_for('users.forgot_password'))

        elif step == 'password':
            new_password = request.form.get('new_password', '').strip()
            confirm_password = request.form.get('confirm_password', '').strip()

            if not new_password or not confirm_password:
                flash("Both password fields are required.", 'forgot_alerts')
                return redirect(url_for('users.forgot_password'))

            if new_password != confirm_password:
                flash("Passwords do not match.", 'forgot_alerts')
                return redirect(url_for('users.forgot_password'))

            if not is_password_secure(new_password):
                flash("Password must have 8+ characters with 1 uppercase, 1 number, and 1 special character.", 'forgot_alerts')
                return redirect(url_for('users.forgot_password'))

            session['new_password'] = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            send_otp_email(session['email'], mail)
            flash("OTP has been sent to your email.", 'forgot_success')
            session['step'] = 'otp'
            return redirect(url_for('users.forgot_password'))

        elif step == 'otp':
            user_otp = request.form.get('otp', '').strip()
            otp_session = session.get('otp')

            if not otp_session or user_otp != otp_session['value'] or time.time() > otp_session['expiry']:
                flash("Invalid or expired OTP.", 'forgot_alerts')
                return redirect(url_for('users.forgot_password'))

            email = session.pop('email', None)
            new_password = session.pop('new_password', None)
            session.pop('otp', None)
            session.pop('step', None)

            user_op.update_user_password(email, new_password)
            flash("Password reset successful! You can now log in.", 'forgot_success')
            return redirect(url_for('users.user_login'))

    return render_template('users/auth/forgot_password.html', step=step)

@users_bp.route("/forgot_resend_otp", methods=['GET'])
@limit_by_session_email("3 per minute")
def forgot_resend_otp():
    email = session.get('email')
    if not email:
        flash("Session expired. Please start the process again.", 'forgot_alerts')
        return redirect(url_for('users.forgot_password'))

    send_otp_email(email, mail)
    flash("A new OTP has been sent to your email.", 'forgot_success')
    return redirect(url_for('users.forgot_password', step='otp'))
