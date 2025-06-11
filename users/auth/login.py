from flask import flash, redirect, render_template, request, session, url_for, current_app as app
import time
import bcrypt
from flask_mail import Mail
from users.auth.user_db import UserOperation
from users import users_bp
from users.auth.utils_login import is_locked_out

user_op = UserOperation()
mail = Mail()


@users_bp.route("/user_login", methods=['GET', 'POST'])
def user_login():
    if 'username' in session and 'email' in session:
        flash("You are already logged in.", 'login_alerts')
        return redirect(url_for('users.login_success'))

    if request.args.get('go_back'):
        session.pop('login_step', None)
        session.pop('email', None)
        return redirect(url_for('users.user_login'))

    if is_locked_out():
        flash("Too many login attempts. Try again in 5 minutes.", 'login_alerts')
        return redirect(url_for('users.login_success'))

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
            
            if user.get('auth_type') == 'google' and not user.get('password'):
                session['email'] = email
                flash("This account was registered with Google. Please set a password first.", 'login_alerts')
                return redirect(url_for('users.set_password'))
            
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

            if bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
                session['username'] = user['username']
                session['email'] = user['email']
                session.permanent = True 
                session.pop('login_step', None)
                session.pop('login_attempts', None)
                session.pop('last_attempt_time', None)
                flash("Login successful!", 'success')
                return redirect(url_for('users.login_success'))
            else:
                session['login_attempts'] = session.get('login_attempts', 0) + 1
                session['last_attempt_time'] = time.time()
                flash("Invalid password.", 'login_alerts')
                return redirect(url_for('users.user_login'))

    return render_template("users/auth/user_login.html", step=session.get('login_step', 'email'))

@users_bp.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out successfully.", 'logout_success')
    return redirect(url_for('users.login_success'))