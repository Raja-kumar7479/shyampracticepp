import logging
from flask import (
    flash, redirect, render_template, request, session, url_for, current_app as app, Response
)
from flask_mail import Mail
from users.auth.user_db import UserOperation 

from users.auth.utils_login import (
    increment_user_login_attempts, is_user_locked_out, reset_user_login_attempts
)

from users.auth.utils_login import verify_password as verify_user_password


from users import users_bp


user_op = UserOperation()

mail = Mail()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@users_bp.route("/user_login", methods=['GET', 'POST'])
def user_login():
    if 'user_username' in session and 'user_email' in session:
        flash("You are already logged in.", 'login_info')
        return redirect(url_for('users.login_success'))

    if request.args.get('go_back'):
        session.pop('user_login_step', None)
        session.pop('user_email_pending', None)
        return redirect(url_for('users.user_login'))

    if is_user_locked_out():
        flash("Too many login attempts. Try again in 5 minutes.", 'login_error')
        return redirect(url_for('users.login_success'))

    step = session.get('user_login_step', 'email')

    if request.method == 'POST':
        if step == 'email':
            email = request.form.get('email', '').strip().lower()
            if not email:
                flash("Please enter your email.", 'login_warning')
                return redirect(url_for('users.user_login'))

            user = user_op.get_user_by_email(email)
            if not user:
                flash("No account found with this email.", 'login_error')
                return redirect(url_for('users.user_login'))

            if user.get('auth_type') == 'google' and not user.get('password'):
                session['user_email_pending'] = email
                flash("This account was registered with Google. Please set a password first.", 'login_info')
                return redirect(url_for('users.user_set_password', email=email))

            session['user_email_pending'] = email
            session['user_login_step'] = 'password'
            logger.info(f"User email found: {email}")
            return redirect(url_for('users.user_login'))

        elif step == 'password':
            email = session.get('user_email_pending')
            password = request.form.get('password', '').strip()

            if not email:
                flash("Session expired. Please enter your email again.", 'login_warning')
                session.pop('user_login_step', None)
                return redirect(url_for('users.user_login'))

            user = user_op.get_user_by_email(email)
            if not user:
                flash("No account found. Please start again.", 'login_error')
                session.pop('user_email_pending', None)
                session.pop('user_login_step', None)
                logger.warning(f"User with pending email not found: {email}")
                return redirect(url_for('users.user_login'))

            if not password:
                flash("Please enter your password.", 'login_warning')
                return redirect(url_for('users.user_login'))

            if verify_user_password(password, user['password']):
                session['user_username'] = user['username']
                session['user_email'] = user['email']
                session.permanent = True
                session.pop('user_login_step', None)
                session.pop('user_email_pending', None)
                reset_user_login_attempts()
                flash("Login successful!", 'login_success')
                logger.info(f"User login successful for {email}")
                return redirect(url_for('users.login_success'))
            else:
                increment_user_login_attempts()
                flash("Invalid password.", 'login_error')
                logger.warning(f"Failed login attempt for user {email}")
                return redirect(url_for('users.user_login'))

    return render_template("users/auth/user_login.html", step=step)

@users_bp.route('/user_logout')
def user_logout():
    keys_to_clear = ['user_username', 'user_email', 'user_login_step', 'user_email_pending', 'user_login_attempts', 'user_last_attempt_time']
    for key in keys_to_clear:
        session.pop(key, None)
    flash("You have been logged out successfully.", 'logout_success')
    logger.info("User logged out")
    return redirect(url_for('users.user_login'))
