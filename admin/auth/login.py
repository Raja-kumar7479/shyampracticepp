import logging
import time
from flask import render_template, request, redirect, url_for, session, flash
from admin.auth.admin_db import UserOperation
from admin import admin_bp
from admin.auth.utils_login import (
    increment_login_attempts,
    reset_login_attempts,
    verify_password,
    hash_password,
    reset_admin_session,
    is_rate_limited
)
from extensions import admin_login_required

logging.basicConfig(level=logging.INFO)
user_op = UserOperation()

@admin_bp.route('/admin_dashboard')
@admin_login_required
def admin_dashboard():
    try:
        username = session.get('admin_username')
        email = session.get('admin_email')
        role = session.get('admin_role')

        if not username or not email or not role:
            logging.warning("Admin session incomplete. Redirecting to login.")
            flash("Session expired or incomplete. Please log in again.", "admin_warning")
            return redirect(url_for('admin.admin_login'))

        logging.info(f"Admin dashboard accessed by: {email}")
        return render_template('admin/dashboard/admin.html',
                               username=username,
                               email=email,
                               role=role)
    except Exception as e:
        logging.error(f"Error loading admin dashboard: {e}")
        flash("An unexpected error occurred. Please try again later.", "admin_error")
        return redirect(url_for('admin.admin_login'))

# Admin Login Route
@admin_bp.route("/admin_login", methods=['GET', 'POST'])
def admin_login():
    if 'admin_email' in session:
        flash("Already logged in as Admin.", 'admin_info')
        return redirect(url_for('admin.admin_dashboard'))

    
    if request.args.get('go_back'):
        session.pop('login_step', None)
        session.pop('admin_email_pending', None)
        return redirect(url_for('admin.admin_login'))

   
    if is_rate_limited():
        flash("Too many login attempts. Try again after some time.", 'admin_error')
        return redirect(url_for('index'))

    step = session.get('login_step', 'email')

    if request.method == 'POST':
        # Step 1: Email verification
        if step == 'email':
            email = request.form.get('email', '').strip()
            if not email:
                flash("Please enter your email.", 'admin_warning')
                return redirect(url_for('admin.admin_login'))

            admin = user_op.get_admin_by_email(email)
            if not admin:
                flash("No admin found with that email.", 'admin_error')
                return redirect(url_for('admin.admin_login'))

            session['admin_email_pending'] = email
            session['login_step'] = 'password'
            return redirect(url_for('admin.admin_login'))

        
        elif step == 'password':
            password = request.form.get('password', '').strip()
            email = session.get('admin_email_pending')

            if not password or not email:
                flash("Session expired or invalid step. Start again.", 'admin_error')
                return redirect(url_for('admin.admin_login'))

            admin = user_op.get_admin_by_email(email)
            if not admin:
                flash("Invalid login attempt.", 'admin_error')
                return redirect(url_for('admin.admin_login'))

            if not admin[3]:  # First-time password set
                hashed_pw = hash_password(password)
                user_op.set_admin_password(email, hashed_pw)
            elif not verify_password(password, admin[3]):
                flash("Incorrect password.", 'admin_error')
                increment_login_attempts()
                return redirect(url_for('admin.admin_login'))

          
            session['admin_username'] = admin[1]
            session['admin_email'] = admin[2]
            session['admin_role'] = 'owner' if admin[4] == 'owner' else 'admin'

            reset_login_attempts()
            session.pop('login_step', None)
            session.pop('admin_email_pending', None)
            flash("Admin login successful!", 'admin_success')
            return redirect(url_for('admin.admin_dashboard'))

    return render_template("admin/auth/admin_login.html", step=step)


@admin_bp.route('/admin_logout')
def admin_logout():
    reset_admin_session()
    flash("You have been logged out successfully.", 'admin_info')
    return redirect(url_for('index'))


@admin_bp.after_request
def set_no_cache(response):
    if request.path.startswith("/admin"):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response
