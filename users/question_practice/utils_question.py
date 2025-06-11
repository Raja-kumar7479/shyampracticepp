from functools import wraps
from flask import session, redirect, url_for, flash, request
import logging
import time
from users.question_practice.user_db import UserOperation

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

user_op = UserOperation()


def secure_access_required(param_names=('unique_code', 'paper_code')):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            email = session.get('email')
            username = session.get('username')

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
