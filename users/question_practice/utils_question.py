import logging
from flask import render_template, request, session, redirect, url_for, jsonify, Blueprint, flash
from users.question_practice.user_db import UserOperation
from extensions import user_login_required
from users import users_bp
from functools import wraps
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

user_op = UserOperation()

def secure_access_required(param_names=('unique_code', 'paper_code')):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            email = session.get('user_email')
            username = session.get('user_username')
            if not email or not username:
                flash("Please login to access this page.", "warning")
                logger.warning("Session missing: Access denied.")
                return redirect(url_for('users.user_login', next=request.url))
            code = kwargs.get(param_names[0])
            course = kwargs.get(param_names[1])
            if not code or not course:
                logger.warning(f"Invalid access attempt: Missing code or course.")
                return redirect(url_for('users.user_login'))
            correct_code = user_op.get_unique_code(email, course)
            if correct_code is None or code != correct_code:
                logger.warning(f"Code verification failed for {email}, course: {course}")
                time.sleep(1)
                return redirect(url_for('users.user_login'))
            return f(*args, **kwargs)
        return wrapped
    return decorator
