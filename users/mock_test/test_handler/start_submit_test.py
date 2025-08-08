from flask import flash, jsonify, redirect, render_template, request, session, url_for
from users.mock_test.handler_db.test_handler_db import TestHandler
from users.mock_test.handler_db.user_db import UserOperation
from users.mock_test.utils_dashboard import get_user_session
from users.mock_test.decorator import secure_access_required
from users.mock_test.utils_token import generate_test_token, validate_test_token
from extensions import user_login_required
from users import users_bp
import json
import os
import logging

test_op = TestHandler()
user_op = UserOperation()
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

@users_bp.route('/start-test/<test_key>/<course_code>/<unique_code>', methods=['GET'])
@user_login_required
@secure_access_required(('unique_code', 'course_code'))
def start_test(test_key, course_code, unique_code):
    email, username = get_user_session()
    if not session.pop('test_popup_initiated', False):
        return redirect(url_for('users.test_terminated', test_key=test_key, course_code=course_code, unique_code=unique_code, violation_type='direct_url_access'))

    if user_op.check_test_already_taken(email, test_key):
        flash('Test already completed. You cannot retake it.', 'test_warning')
        test_details = user_op.get_test_details(test_key)
        section_id = test_details['test_id'] if test_details else ''
        return redirect(url_for('users.open_mock_test_section', section_id=section_id, course_code=course_code, unique_code=unique_code))

    test_basic_info = user_op.get_test_details(test_key)
    if not test_basic_info:
        flash('Test details not found.', 'test_error')
        return redirect(url_for('users.purchase_dashboard', course_code=course_code, unique_code=unique_code))
    
    course_specific_info = user_op.get_course_info_by_test_id(test_basic_info['test_id'])
    if not course_specific_info:
        flash('Course details could not be found.', 'test_error')
        return redirect(url_for('users.purchase_dashboard', course_code=course_code, unique_code=unique_code))

    test_course_info = {**test_basic_info, **course_specific_info}

    instructions_data = {}
    try:
        file_path = os.path.join(os.path.dirname(__file__), 'instruction_popup.json')
        with open(file_path, 'r', encoding='utf-8') as f:
            instructions_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"ERROR: Could not load instruction_popup.json. Details: {e}")
        instructions_data = {"part1": "<p>Error: Instructions could not be loaded.</p>", "part2": ""}

    duration_seconds = (test_course_info.get('total_duration_minutes') or 0) * 60
    new_token = generate_test_token(email, test_key, duration_seconds)
    session['test_token'] = new_token
    sections = user_op.get_test_sections(test_key)

    return render_template('users/mock_test/test_handler/test_window.html',
                           test_key=test_key, 
                           course_info=test_basic_info, 
                           duration_seconds=duration_seconds,
                           test_course_info=test_course_info,
                           sections_data=sections, 
                           username=username, 
                           unique_code=unique_code, 
                           course_code=course_code,
                           instructions=instructions_data) 

@users_bp.route('/submit-test-action/<test_key>/<course_code>/<unique_code>', methods=['POST'])
@user_login_required
@secure_access_required(('unique_code', 'course_code'))
def submit_test_action(test_key, course_code, unique_code):
    email, username = get_user_session()
    token = session.get('test_token')
    if not validate_test_token(token, email, test_key):
        return jsonify({"error": "Invalid or expired session token."}), 403

    submission_data = request.json
    if not submission_data:
        return jsonify({"error": "No submission data received."}), 400

    test_result_id, error_message = test_op.save_test_submission(email, username, test_key, submission_data)
    if error_message:
        return jsonify({"error": error_message}), 500

    session.pop('test_token', None)
    if test_result_id:
        feedback_url = url_for('users.test_feedback', test_key=test_key, course_code=course_code, unique_code=unique_code)
        return jsonify({"message": "Test submitted successfully.", "redirect_url": feedback_url}), 200

    return jsonify({"error": "An unexpected error occurred."}), 500
