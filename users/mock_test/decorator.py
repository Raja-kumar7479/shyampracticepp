from functools import wraps
from flask import flash, jsonify, redirect, render_template, request, session, url_for, abort
from extensions import user_login_required
from users.enroll.user_db import UserOperation
import logging
import uuid
import time

user_op = UserOperation()

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

def secure_access_required(param_names=('unique_code', 'course_code')):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            user_email = session.get('user_email')
            if not user_email:
                logger.warning("Access denied: No user email in session.")
                flash("Please login to access this page.", "warning")
                return redirect(url_for('users.user_login'))

            unique_code = kwargs.get(param_names[0])
            course_code = kwargs.get(param_names[1])

            if not unique_code or not course_code:
                logger.warning("Access denied: Missing unique_code or course_code.")
                flash("Missing information. Access denied.", "danger")
                return redirect(url_for('users.user_login'))

            correct_code = user_op.get_user_unique_code(user_email, course_code)
            if correct_code is None:
                logger.warning(f"Access denied: No record found for course {course_code} and email {user_email}.")
            elif unique_code != correct_code:
                logger.warning(f"Access denied: Mismatched code. Provided: {unique_code}, Expected: {correct_code}.")

            if correct_code is None or unique_code != correct_code:
                flash("Invalid or unauthorized access.", "danger")
                time.sleep(1)
                return redirect(url_for('users.user_login'))

            logger.info(f"Access granted for user {user_email} to course {course_code} with code {unique_code}")
            return f(*args, **kwargs)
        return wrapped
    return decorator

