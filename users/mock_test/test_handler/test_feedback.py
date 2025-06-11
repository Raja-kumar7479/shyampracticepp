from flask import flash, jsonify, redirect, render_template, request, session, url_for
from users.mock_test.handler_db.test_handler_db import TestHandler
from users.mock_test.handler_db.user_db import UserOperation
from users.mock_test.utils_dashboard import get_user_session
from users.mock_test.decorator import secure_access_required
from extensions import login_required
from users import users_bp
from extensions import login_required


import logging

test_op = TestHandler()
user_op = UserOperation()

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

@users_bp.route('/test_feedback/<test_id>/<course_code>/<unique_code>')
@login_required
@secure_access_required(('unique_code', 'course_code'))
def test_feedback(test_id, course_code, unique_code):
    user_session = get_user_session()
    
    user_email, username = user_session

    return render_template('users/course_materials/mock_test/result_handler/test_feedback_form.html',
                           test_id=test_id,
                           course_code=course_code,
                           unique_code=unique_code,
                           email=user_email,
                           username=username)

@users_bp.route('/submit_feedback/<test_id>/<course_code>/<unique_code>', methods=['POST'])
@login_required
@secure_access_required(('unique_code', 'course_code'))
def submit_feedback(test_id, course_code, unique_code):
    user_session = get_user_session()
    
    user_email, username = user_session

    try:
        feedback_data = request.json
        
        software_feedback = feedback_data.get('software_feedback')
        content_feedback = feedback_data.get('content_feedback')
        speed_feedback = feedback_data.get('speed_feedback')
        suggestions = feedback_data.get('suggestions')

        if not all([software_feedback, content_feedback, speed_feedback]):
            return jsonify({"status": "error", "message": "Please provide feedback for all required fields."}), 400

        query = """
            INSERT INTO test_feedback (
                test_id, email, feedback_software, feedback_content, feedback_speed, suggestions
            ) VALUES (%s, %s, %s, %s, %s, %s)
        """
        user_op.execute_query(query, (
            test_id, user_email, software_feedback, content_feedback, speed_feedback, suggestions
        ))

        logger.info(f"Feedback stored for user {username} ({user_email}) on test {test_id}")

        overview_url = url_for('users.test_overview',
                               test_id=test_id,
                               course_code=course_code,
                               unique_code=unique_code)
        return jsonify({
            "status": "success",
            "message": "Feedback submitted successfully!",
            "redirect_url": overview_url
        }), 200

    except Exception as e:
        logger.exception(f"Error submitting feedback for user {username} ({user_email}), test {test_id}: {e}")
        return jsonify({
            "status": "error",
            "message": "Failed to submit feedback due to an internal error."
        }), 500



@users_bp.route('/calculator-popup')
def calculator_popup():
    return render_template('users/course_materials/test_calculator/calculator_popup.html')