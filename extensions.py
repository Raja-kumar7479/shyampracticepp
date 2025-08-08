from functools import wraps
from flask import flash, redirect, request, session, url_for, abort
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    headers_enabled=True,
)

def init_limiter(app):
    limiter.init_app(app)

def user_login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_username' not in session or 'user_email' not in session:
            flash("Access denied. Please log in to continue.", 'error')
            return redirect(url_for('users.user_login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_email' not in session or 'admin_username' not in session:
            flash("Admin login required to access this page.", "admin_login_required")
            return redirect(url_for('admin.admin_login', next=request.url))

        if session.get('admin_role') not in ['admin', 'owner']:
            flash("You do not have permission to access this page.", "admin_login_permission")
            return abort(403)
        return f(*args, **kwargs)
    return decorated_function
