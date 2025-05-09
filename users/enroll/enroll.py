import base64
from functools import wraps
import hashlib
import uuid
from flask import current_app, flash, jsonify, redirect, render_template, request, session, url_for
import mysql
from extensions import limiter
from extensions import login_required
from config import Config
from users.enroll.user_db import UserOperation
from users.enroll.utils_enroll import generate_secure_code
from flask_limiter.util import get_remote_address
from extensions import limiter

from users import users_bp
user_op =UserOperation()


def limit_by_session_email(limit="5 per minute"):
    def decorator(f):
        @wraps(f)
        @limiter.limit(limit, key_func=lambda: session.get('email') or get_remote_address())
        def wrapped(*args, **kwargs):
            return f(*args, **kwargs)
        return wrapped
    return decorator

def limit_by_enrollment_email(limit="5 per minute"):
    def decorator(f):
        @wraps(f)
        @limiter.limit(limit, key_func=lambda: session.get('email') or get_remote_address())
        def wrapped(*args, **kwargs):
            return f(*args, **kwargs)
        return wrapped
    return decorator

@users_bp.route('/start_enrollment', methods=['GET'])
@limit_by_enrollment_email("5 per minute")
@login_required
def start_enrollment():
    try:
        session.pop('captcha_value', None)
        captcha = str(uuid.uuid4())[:6].upper()
        session['captcha_value'] = captcha
        return jsonify({"captcha": captcha})
    except Exception as e:
        current_app.logger.error(f"Error generating captcha: {e}")
        return jsonify({"error": "Unable to start enrollment process."}), 500


@users_bp.route('/check_enrollment', methods=['GET'])
@limit_by_enrollment_email("10 per minute")
@login_required
def check_enrollment():
    email = session.get('email')
    course_name = request.args.get('course_name', '').strip().upper()

    if not course_name:
        return jsonify({"error": "Course name is required."}), 400

    try:
        enrolled_courses = user_op.get_enrolled_courses(email)
    except Exception as e:
        current_app.logger.error(f"Error fetching enrolled courses: {e}")
        return jsonify({"error": "Unable to check enrollment."}), 500

    if len(enrolled_courses) >= 2:
        return jsonify({"exceeded_limit": True})

    already_enrolled = course_name in enrolled_courses
    return jsonify({"already_enrolled": already_enrolled})

@users_bp.route('/final_enroll', methods=['POST'])
@limit_by_enrollment_email("3 per minute")
@login_required
def final_enroll():
    email = session.get('email')
    if not email:
        return jsonify({"success": False, "error": "Unauthorized access."}), 403

    course_name = request.form.get('course_name', '').upper().strip()
    captcha_input = request.form.get('captcha', '').strip()
    captcha_value = session.get('captcha_value')

    # Security: Prevent missing/empty input
    if not course_name or not captcha_input or not captcha_value:
        return jsonify({"success": False, "error": "Missing fields. Please try again."}), 400

    # Verify CAPTCHA
    if captcha_input != captcha_value:
        session.pop('captcha_value', None)
        return jsonify({"success": False, "error": "Captcha verification failed."}), 403

    # Prevent duplicate enrollment
    if user_op.check_enrollment(email, course_name):
        session.pop('captcha_value', None)
        return jsonify({"success": False, "error": "Already enrolled in this course."})

    # Limit: No more than 2 courses
    enrolled_courses = user_op.get_enrolled_courses(email)
    if len(enrolled_courses) >= 2:
        session.pop('captcha_value', None)
        return jsonify({"success": False, "error": "Enrollment limit exceeded."}), 403

    # Captcha can only be used once
    session.pop('captcha_value', None)

    # Generate and store secure code
    unique_code = generate_secure_code(email, course_name)
    user_op.enroll_user(email, course_name, unique_code)

    return jsonify({"success": True, "course_name": course_name, "unique_code": unique_code})

@users_bp.route('/get_unique_code', methods=['GET'])
@limit_by_session_email("10 per minute")
@login_required
def get_unique_code():
    email = session.get('email')
    course_name = request.args.get('course_name', '').strip().upper()

    if not course_name:
        return jsonify({"error": "Course name is required."}), 400

    try:
        unique_code = user_op.get_user_unique_code(email, course_name)
    except Exception as e:
        current_app.logger.error(f"Error fetching unique code: {e}")
        return jsonify({"error": "Server error while retrieving code."}), 500

    if unique_code:
        return jsonify({"unique_code": unique_code})
    else:
        return jsonify({"error": "Course not found or user is not enrolled."}), 404
