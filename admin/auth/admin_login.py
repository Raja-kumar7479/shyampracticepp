import logging
import time
import bcrypt
from functools import wraps
from flask import (
    flash, redirect, render_template, request, session, url_for, current_app as app, Response
)
from flask_mail import Mail
from extensions import admin_login_required
from admin.auth.admin_db import UserOperation as AdminDb

from admin.auth.admin_utils import (
    increment_admin_login_attempts, is_admin_locked_out, reset_admin_login_attempts
)

from admin.auth.admin_utils import verify_password as verify_admin_password
from admin.auth.admin_utils import hash_password as hash_admin_password

from users import users_bp
from admin import admin_bp

admin_db = AdminDb()
mail = Mail()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@admin_bp.route('/admin_dashboard')
@admin_login_required
def admin_dashboard():
    username = session.get('admin_username')
    email = session.get('admin_email')
    role = session.get('admin_role')

    if not username or not email or not role:
        flash("Session expired or incomplete. Please log in again.", "admin_warning")
        return redirect(url_for('admin.admin_login'))

    return render_template('admin/admin_dashboard/admin.html', username=username, email=email, role=role)

@admin_bp.route("/admin_login", methods=['GET', 'POST'])
def admin_login():
    if 'admin_email' in session:
        flash("Already logged in as Admin.", 'admin_info')
        return redirect(url_for('admin.admin_dashboard'))

    if request.args.get('go_back'):
        session.pop('admin_login_step', None)
        session.pop('admin_email_pending', None)
        return redirect(url_for('admin.admin_login'))

    if is_admin_locked_out():
        flash("Too many login attempts. Try again later.", 'admin_error')
        return redirect(url_for('index'))

    step = session.get('admin_login_step', 'email')
    
    if request.method == 'POST':
        if step == 'email':
            email = request.form.get('email', '').strip()
            if not email:
                flash("Please enter your email.", 'admin_warning')
                return redirect(url_for('admin.admin_login'))

            admin = admin_db.get_admin_by_email(email)
            if not admin:
                flash("No admin found with that email.", 'admin_error')
                return redirect(url_for('admin.admin_login'))

            session['admin_email_pending'] = email
            session['admin_login_step'] = 'password'
            logger.info(f"Admin email found: {email}")
            return redirect(url_for('admin.admin_login'))

        elif step == 'password':
            password = request.form.get('password', '').strip()
            email = session.get('admin_email_pending')

            if not password or not email:
                flash("Session expired or invalid step. Start again.", 'admin_error')
                return redirect(url_for('admin.admin_login'))

            admin = admin_db.get_admin_by_email(email)
            if not admin:
                flash("Invalid login attempt.", 'admin_error')
                logger.warning(f"Invalid login attempt for email: {email}")
                return redirect(url_for('admin.admin_login'))

            if not admin['password']:
                hashed_pw = hash_admin_password(password)
                admin_db.set_admin_password(email, hashed_pw)
                logger.info(f"Admin password set for {email}")
            elif not verify_admin_password(password, admin['password']):
                flash("Incorrect password.", 'admin_error')
                increment_admin_login_attempts()
                logger.warning(f"Failed login attempt for admin {email}")
                return redirect(url_for('admin.admin_login'))

            session['admin_username'] = admin['username']
            session['admin_email'] = admin['email']
            session['admin_role'] = 'owner' if admin['role'] == 'owner' else 'admin'
            reset_admin_login_attempts()
            session.pop('admin_login_step', None)
            session.pop('admin_email_pending', None)
            flash("Admin login successful!", 'admin_success')
            logger.info(f"Admin login successful for {email}")
            return redirect(url_for('admin.admin_dashboard'))

    return render_template("admin/admin_auth/admin_login.html", step=step)

@admin_bp.route('/admin_logout')
def admin_logout():
    for key in ['admin_username', 'admin_email', 'admin_role', 'admin_login_step', 'admin_email_pending']:
        session.pop(key, None)
    flash("You have been successfully logged out.", 'admin_info')
    logger.info("Admin logged out")
    return redirect(url_for('admin.admin_login'))

@admin_bp.after_request
def set_security_headers(response: Response):
    if request.path.startswith('/admin'):
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    return response

