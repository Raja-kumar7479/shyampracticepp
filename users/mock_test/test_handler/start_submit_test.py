from flask import flash, jsonify, redirect, render_template, request, session, url_for
from users.mock_test.handler_db.test_handler_db import TestHandler
from users.mock_test.handler_db.user_db import UserOperation
from users.mock_test.utils_dashboard import (get_user_session,
                                             )
from users.mock_test.decorator import secure_access_required
from users.mock_test.utils_token import generate_test_token,validate_test_token
from extensions import login_required
from users import users_bp
from extensions import login_required


import logging

test_op = TestHandler()
user_op = UserOperation()

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)


from datetime import datetime, timezone

@users_bp.route('/start-test/<test_id>/<course_code>/<unique_code>', methods=['GET', 'POST'])
@login_required
@secure_access_required(('unique_code', 'course_code'))
def start_test(test_id, course_code, unique_code):
    email, username = get_user_session()
    logger.info(f"[START TEST] User {email} (username: {username}) trying to start test {test_id}")

    if not session.pop('test_popup_initiated', False):
        logger.warning(f"[START TEST VIOLATION] User {email} attempted direct access to test {test_id}")
        return redirect(url_for('users.test_terminated', test_id=test_id, course_code=course_code, unique_code=unique_code,violation_type='direct_url_access'))

    if user_op.check_test_already_taken(email, test_id):
        flash('Test already completed. You cannot retake it.', 'warning')
        return redirect(url_for('users.open_mock_test', course_code=course_code, unique_code=unique_code))

    test_basic_info = user_op.get_test_basic_details(test_id)
    if not test_basic_info:
        flash('Test details not found.', 'danger')
        return redirect(url_for('users.open_mock_test', course_code=course_code, unique_code=unique_code))

    duration_seconds = (test_basic_info.get('total_duration_minutes') or 0) * 60

    course_info = {
        "code": test_basic_info.get('code'),
        "stream": test_basic_info.get('stream'),
        "subject_title": test_basic_info.get('subject_title')
    }

    new_token = generate_test_token(email, test_id, duration_seconds)
    session['test_token'] = new_token

    sections = user_op.get_test_sections(test_id)

    return render_template(
        'users/course_materials/mock_test/test_handler/test_window.html',
        test_id=test_id,
        course_info=course_info,
        duration_seconds=duration_seconds,
        sections_data=sections,
        username=username,
        unique_code=unique_code,
        course_code=course_code
    )

@users_bp.route('/submit-test-action/<test_id>/<course_code>/<unique_code>', methods=['POST'])
@login_required
@secure_access_required(('unique_code', 'course_code'))
def submit_test_action(test_id, course_code, unique_code):
    try:
        email, username = get_user_session()
        logger.info(f"[SUBMIT TEST] User {email} submitting test {test_id}")

        # Validate token from session
        token = session.get('test_token')
        if not validate_test_token(token, email, test_id):
            logger.warning(f"[SUBMIT TEST] Invalid or expired token for user {email}, test {test_id}")
            return jsonify({"error": "Invalid or expired session token."}), 403

        submission_data = request.json
        if not submission_data:
            return jsonify({"error": "No submission data received."}), 400

        # Save test result
        test_result_id, error_message = test_op.save_test_submission(email, username, test_id, submission_data)

        if error_message:
            return jsonify({"error": error_message}), 500

        # Clear test token from session
        session.pop('test_token', None)

        if test_result_id:
            feedback_url = url_for('users.test_feedback', test_id=test_id,
                                   course_code=course_code, unique_code=unique_code)
            return jsonify({
                "message": "Test submitted successfully. Redirecting to feedback...",
                "redirect_url": feedback_url
            }), 200

        return jsonify({"error": "Unexpected error. Please contact support."}), 500

    except Exception as e:
        logger.exception(f"[SUBMIT TEST] Exception: {e}")
        return jsonify({"error": "Unexpected server error occurred."}), 500
