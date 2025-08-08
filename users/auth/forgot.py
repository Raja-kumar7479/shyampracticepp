from functools import wraps
from flask import (
    render_template, request, redirect, url_for, session, flash, current_app as app
)
from flask_mail import Mail
from users.auth.utils_signup import is_password_secure
from users.auth.utils_forgot import send_forgot_otp_email
from flask_limiter.util import get_remote_address
from extensions import limiter
import time
import bcrypt
from users.auth.user_db import UserOperation
import logging
from users import users_bp

user_op = UserOperation()
mail = Mail()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def limit_by_session_email(limit="5 per minute"):
    def decorator(f):
        @wraps(f)
        @limiter.limit(limit, key_func=lambda: session.get('user_forgot_email') or get_remote_address())
        def wrapped(*args, **kwargs):
            return f(*args, **kwargs)
        return wrapped
    return decorator

@users_bp.route("/user_forgot_password", methods=['GET', 'POST'])
@limit_by_session_email("3 per minute")
def user_forgot_password():
    if 'user_email' in session and 'user_username' in session:
        flash("You are already logged in.", 'info')
        return redirect(url_for('users.login_success'))

    step = session.get('user_forgot_step', 'email')
    go_back = request.args.get('go_back')

    if go_back:
        if go_back == '2':
            session.pop('user_forgot_otp', None)
            session['user_forgot_step'] = 'password'
            return redirect(url_for('users.user_forgot_password'))
        elif go_back == '1':
            session.pop('user_forgot_new_password', None)
            session['user_forgot_step'] = 'email'
            return redirect(url_for('users.user_forgot_password'))

    if request.method == 'POST':
        if step == 'email':
            email = request.form.get('email', '').strip()
            if not email:
                flash("Email is required.", 'forgot_error')
                return redirect(url_for('users.user_forgot_password'))

            user = user_op.get_user_by_email(email)
            if user:
                session['user_forgot_email'] = email
                session['user_forgot_step'] = 'password'
                flash("Email found! Please enter your new password.", 'forgot_success')
                logger.info(f"Forgot password: Email found for {email}")
            else:
                flash("Email not registered.", 'forgot_error')
                logger.warning(f"Forgot password: Email not registered: {email}")
            return redirect(url_for('users.user_forgot_password'))

        elif step == 'password':
            new_password = request.form.get('new_password', '').strip()
            confirm_password = request.form.get('confirm_password', '').strip()

            if not new_password or not confirm_password:
                flash("Both password fields are required.", 'forgot_error')
                return redirect(url_for('users.user_forgot_password'))

            if new_password != confirm_password:
                flash("Passwords do not match.", 'forgot_error')
                return redirect(url_for('users.user_forgot_password'))

            if not is_password_secure(new_password):
                flash("Password must have 8+ characters with 1 uppercase, 1 number, and 1 special character.", 'forgot_error')
                return redirect(url_for('users.user_forgot_password'))

            session['user_forgot_new_password'] = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            send_forgot_otp_email(session['user_forgot_email'], mail)
            flash("OTP has been sent to your email.", 'forgot_success')
            session['user_forgot_step'] = 'otp'
            logger.info(f"Forgot password: OTP sent to {session['user_forgot_email']}")
            return redirect(url_for('users.user_forgot_password'))

        elif step == 'otp':
            user_otp = request.form.get('otp', '').strip()
            otp_session = session.get('user_forgot_otp')

            if not otp_session or user_otp != otp_session['value'] or time.time() > otp_session['expiry']:
                flash("Invalid or expired OTP.", 'forgot_error')
                logger.warning(f"Forgot password: Invalid or expired OTP for {session.get('user_forgot_email')}")
                return redirect(url_for('users.user_forgot_password'))

            email = session.pop('user_forgot_email', None)
            new_password = session.pop('user_forgot_new_password', None)
            session.pop('user_forgot_otp', None)
            session.pop('user_forgot_step', None)

            user_op.update_user_password(email, new_password)
            flash("Password reset successful! You can now log in.", 'login_success')
            logger.info(f"Forgot password: Password reset successfully for {email}")
            return redirect(url_for('users.user_login'))

    return render_template('users/auth/forgot_password.html', step=step)

@users_bp.route("/user_forgot_resend_otp", methods=['GET'])
@limit_by_session_email("3 per minute")
def user_forgot_resend_otp():
    email = session.get('user_forgot_email')
    if not email:
        flash("Session expired. Please start the process again.", 'forgot_error')
        return redirect(url_for('users.user_forgot_password'))

    send_forgot_otp_email(email, mail)
    flash("A new OTP has been sent to your email.", 'forgot_success')
    logger.info(f"Forgot password: New OTP resent to {email}")
    return redirect(url_for('users.user_forgot_password', step='otp'))
