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

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('username') or not session.get('email'):
            flash("Access denied. Please log in to continue.", 'error')
            return redirect(url_for('users.user_login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def admin_login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_email') or not session.get('admin_username'):
            flash("Admin login required to access this page.", "admin_login_required")
            return redirect(url_for('admin.admin_login', next=request.url))
        
        # Optional: Check roles strictly
        if session.get('admin_role') not in ['admin', 'owner']:
            flash("You do not have permission to access this page.", "admin_login_permission")
            return abort(403)  # Better than redirecting silently
        return f(*args, **kwargs)
    return decorated_function
