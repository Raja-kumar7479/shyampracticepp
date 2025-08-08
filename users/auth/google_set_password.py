from flask import render_template, request, redirect, url_for, session, flash, current_app as app
from users.auth.utils_signup import is_password_secure
from users.auth.user_db import UserOperation
import bcrypt
import logging

from users import users_bp

user_op = UserOperation()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@users_bp.route("/user_set_password", methods=['GET', 'POST'])
def user_set_password():
    email = request.args.get('email') or session.get('user_email_pending')

    if not email:
        flash("Invalid request. Please log in again.", "login_error")
        return redirect(url_for('users.user_login'))

    try:
        user = user_op.get_user_by_email(email)
    except Exception as e:
        flash("There was an error fetching your user details. Please try again.", "login_error")
        app.logger.error(f"Error in get_user_by_email: {e}")
        return redirect(url_for('users.user_login'))

    if not user or user.get('auth_type') != 'google':
        flash("This feature is only for Google-registered users.", 'login_error')
        return redirect(url_for('users.user_login'))

    if user.get('password'):
        flash("You have already set your password. Please log in.", 'login_info')
        return redirect(url_for('users.user_login'))

    if request.method == 'POST':
        new_password = request.form.get('new_password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()

        if not new_password or not confirm_password:
            flash("Both fields are required.", 'login_error')
            return redirect(url_for('users.user_set_password', email=email))

        if new_password != confirm_password:
            flash("Passwords do not match.", 'login_error')
            return redirect(url_for('users.user_set_password', email=email))

        if not is_password_secure(new_password):
            flash("Password must have 8+ characters, 1 uppercase, 1 digit, 1 special char.", 'login_error')
            return redirect(url_for('users.user_set_password', email=email))

        try:
            hashed_pw = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            user_op.set_user_password(email, hashed_pw)
            logger.info(f"Password set successfully for Google user {email}")
        except Exception as e:
            flash("There was an error setting your password. Please try again.", "login_error")
            app.logger.error(f"Error hashing or updating password: {e}")
            return redirect(url_for('users.user_set_password', email=email))

        session['user_username'] = user['username']
        session['user_email'] = user['email']
        session.permanent = True
        session.pop('user_login_step', None)
        session.pop('user_email_pending', None)
        flash("Password set successfully! You are now logged in.", 'login_success')
        return redirect(url_for('users.login_success'))

    return render_template("users/auth/set_password.html", email=email)
