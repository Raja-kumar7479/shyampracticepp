from functools import wraps
import logging
import uuid
from venv import logger
from flask import  jsonify, redirect, render_template, request, session, url_for
from extensions import login_required
from users.enroll.user_db import UserOperation
from users.enroll.utils_enroll import generate_secure_code


from users import users_bp
user_op =UserOperation()

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

@users_bp.route('/start_enrollment', methods=['GET'])
@login_required
def start_enrollment():
    try:
        session.pop('captcha_value', None)
        captcha = str(uuid.uuid4())[:6].upper()
        session['captcha_value'] = captcha
        logger.info(f"Captcha generated for session: {captcha}")
        return jsonify({"captcha": captcha})
    except Exception as e:
        logger.exception("Error generating captcha")
        return jsonify({"error": "Unable to start enrollment process."}), 500

@users_bp.route('/check_enrollment', methods=['GET'])
@login_required
def check_enrollment():
    email = session.get('email')
    course_code = request.args.get('course_code', '').strip().upper()

    if not course_code:
        return jsonify({"error": "Course code is required."}), 400

    try:
        enrolled_courses = user_op.get_enrolled_courses(email)
    except Exception as e:
        logger.exception("Error fetching enrolled courses")
        return jsonify({"error": "Unable to check enrollment."}), 500

    if len(enrolled_courses) >= 2:
        return jsonify({"exceeded_limit": True})

    already_enrolled = course_code in enrolled_courses
    return jsonify({"already_enrolled": already_enrolled})


@users_bp.route('/final_enroll', methods=['POST'])
@login_required
def final_enroll():
    try:
        logger.info("Enrollment process started")

        email = session.get('email')
        if not email:
            logger.warning("No email found in session.")
            return jsonify({"success": False, "error": "Unauthorized access."}), 403

        course_code = request.form.get('course_code', '').upper().strip()
        course_name = request.form.get('course_name', '').strip()
        captcha_input = request.form.get('captcha', '').strip()
        captcha_value = session.get('captcha_value')

        if not course_code or not course_name or not captcha_input or not captcha_value:
            logger.warning("Missing required enrollment fields.")
            return jsonify({"success": False, "error": "Missing fields. Please try again."}), 400

        if captcha_input != captcha_value:
            logger.warning("Captcha verification failed for %s", email)
            session.pop('captcha_value', None)
            return jsonify({"success": False, "error": "Captcha verification failed."}), 403

        if user_op.check_enrollment(email, course_code):
            logger.info("User %s already enrolled in course %s", email, course_code)
            session.pop('captcha_value', None)
            return jsonify({"success": False, "error": "Already enrolled in this course."})

        enrolled_courses = user_op.get_enrolled_courses(email)
        if len(enrolled_courses) >= 2:
            logger.info("Enrollment limit exceeded for %s", email)
            session.pop('captcha_value', None)
            return jsonify({"success": False, "error": "Enrollment limit exceeded."}), 403

        # Generate code using email, course_code, and captcha
        unique_code = generate_secure_code(email, course_code, captcha_input)

        # Store the enrollment in DB
        user_op.enroll_user(email, course_code, course_name, unique_code)
        logger.info("User %s enrolled in %s with secure code %s", email, course_code, unique_code)

        session.pop('captcha_value', None)  # Remove used captcha

        return jsonify({"success": True, "course_code": course_code, "unique_code": unique_code})

    except Exception as e:
        logger.exception("Unexpected error during final enrollment")
        return jsonify({"success": False, "error": "An unexpected error occurred."}), 500

@users_bp.route('/get_unique_code', methods=['GET'])
@login_required
def get_unique_code():
    email = session.get('email')
    course_code = request.args.get('course_code', '').strip().upper()

    if not course_code:
        return jsonify({"status": "error", "message": "Course code is required."}), 400

    try:
        unique_code = user_op.get_user_unique_code(email, course_code)
        if unique_code:
            return jsonify({"status": "success", "unique_code": unique_code})
        else:
            return jsonify({"status": "error", "message": "Course not found or not enrolled."}), 404
    except Exception as e:
        logger.exception("Error retrieving unique code")
        return jsonify({"status": "error", "message": "Server error while retrieving code."}), 500
