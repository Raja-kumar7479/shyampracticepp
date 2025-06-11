from flask import render_template, request, redirect, url_for, session, flash, current_app as app
from users.auth.utils_signup import is_password_secure
import bcrypt
from users.auth.user_db import UserOperation
from users import users_bp

user_op = UserOperation()

@users_bp.route("/set_password", methods=['GET', 'POST'])
def set_password():
    email = request.args.get('email') or session.get('email')

    if not email:
        flash("Invalid request. Please log in again.", "login_alerts")
        return redirect(url_for('users.user_login'))

    try:
        user = user_op.get_user_by_email(email)
    except Exception as e:
        flash("There was an error fetching your user details. Please try again.", "login_alerts")
        app.logger.error(f"Error in get_user_by_email: {e}")
        return redirect(url_for('users.user_login'))

    if not user or user.get('auth_type') != 'google':
        flash("This feature is only for Google-registered users.", 'login_alerts')
        return redirect(url_for('users.user_login'))

    if user.get('password'):
        flash("You have already set your password. Please log in.", 'success')
        return redirect(url_for('users.user_login'))

    if request.method == 'POST':
        new_password = request.form.get('new_password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()

        if not new_password or not confirm_password:
            flash("Both fields are required.", 'login_alerts')
            return redirect(url_for('users.set_password', email=email))

        if new_password != confirm_password:
            flash("Passwords do not match.", 'login_alerts')
            return redirect(url_for('users.set_password', email=email))

        if not is_password_secure(new_password):
            flash("Password must have 8+ characters, 1 uppercase, 1 digit, 1 special char.", 'login_alerts')
            return redirect(url_for('users.set_password', email=email))

        try:
            hashed_pw = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            user_op.set_user_password(email, hashed_pw)
        except Exception as e:
            flash("There was an error setting your password. Please try again.", "login_alerts")
            app.logger.error(f"Error hashing or updating password: {e}")
            return redirect(url_for('users.set_password', email=email))

        
        session['username'] = user['username']
        session['email'] = user['email']
        session.permanent = True
        session.pop('login_step', None)
        flash("Password set successfully! You are now logged in.", 'success')
        return redirect(url_for('users.login_success'))

    return render_template("users/auth/set_password.html", email=email)
