from flask import flash, jsonify, redirect, render_template, request, session, url_for
from users.mock_test.handler_db.test_handler_db import TestHandler
from users.mock_test.utils_dashboard import get_user_session
from users.mock_test.handler_db.user_db import UserOperation
from users.mock_test.decorator import secure_access_required
from users.mock_test.utils_token import generate_test_token, validate_test_token

from extensions import user_login_required
from users import users_bp
import json
import os
import logging
from flask_mail import Mail

test_op = TestHandler()
user_op = UserOperation()
logger = logging.getLogger(__name__)
mail = Mail()


@users_bp.route('/test_feedback/<test_key>/<course_code>/<unique_code>')
@user_login_required
@secure_access_required(('unique_code', 'course_code'))
def test_feedback(test_key, course_code, unique_code):
    email, username = get_user_session()
    if not email or not username:
        return redirect(url_for('users.user_login'))
        
    test_details = user_op.get_test_details(test_key)
    return render_template('users/mock_test/result_handler/test_feedback_form.html',
                           test_key=test_key, course_code=course_code, unique_code=unique_code,
                           email=email, username=username, test_id=test_details.get('test_id'))

@users_bp.route('/submit_feedback/<test_key>/<course_code>/<unique_code>', methods=['POST'])
@user_login_required
@secure_access_required(('unique_code', 'course_code'))
def submit_feedback(test_key, course_code, unique_code):
    email, username = get_user_session()
    if not email or not username:
        return jsonify({"status": "error", "message": "Session expired."}), 401
    
    try:
        feedback_data = request.json
        test_details = user_op.get_test_details(test_key)
        test_id = test_details.get('test_id') if test_details else None

        query = """
            INSERT INTO test_feedback (test_id, test_key, email, feedback_software, feedback_content, feedback_speed, suggestions)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        user_op.execute_query(query, (test_id, test_key, email, feedback_data.get('software_feedback'), feedback_data.get('content_feedback'), feedback_data.get('speed_feedback'), feedback_data.get('suggestions')))
        
        overview_url = url_for('users.test_overview', test_key=test_key, course_code=course_code, unique_code=unique_code)
        return jsonify({"status": "success", "message": "Feedback submitted successfully!", "redirect_url": overview_url}), 200
    except Exception as e:
        logger.exception(f"Failed to submit feedback for test {test_key} by user {email}: {e}")
        return jsonify({"status": "error", "message": "Failed to submit feedback."}), 500
