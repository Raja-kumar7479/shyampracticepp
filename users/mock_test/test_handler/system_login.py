from flask import flash, redirect, render_template, request, session, url_for, jsonify
from users.mock_test.handler_db.user_db import UserOperation
from users.mock_test.utils_dashboard import get_user_session
from users.mock_test.decorator import secure_access_required
from extensions import user_login_required
from users import users_bp
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

user_op = UserOperation()

@users_bp.route('/test-login/<test_key>/<course_code>/<unique_code>', methods=['GET', 'POST'])
@user_login_required
@secure_access_required(('unique_code', 'course_code'))
def test_login(test_key, course_code, unique_code):
    email, username = get_user_session()
    logger.info(f"User {email} attempting to log in for test: {test_key}")

    test_details = user_op.get_test_details(test_key)
    
    if not test_details:
        flash('Test not found. The link may be invalid.', 'test_error')
        logger.warning(f"Test not found for key: {test_key}. Redirecting user {email}.")
        return redirect(url_for('users.purchase_dashboard', course_code=course_code, unique_code=unique_code))

    if request.method == 'POST':
        submitted_key = request.form.get('test_key')
        if test_key == submitted_key:
            logger.info(f"User {email} submitted correct test key.")
            if user_op.check_test_already_taken(email, test_key):
                logger.warning(f"User {email} attempted to retake test {test_key}.")
                return jsonify({
                    "success": False,
                    "message": "You have already completed this test."
                }), 403

            user_op.store_user_test_start(email, test_key, username)
            session['test_popup_initiated'] = True
            
            instruction_url = url_for('users.test_instruction', test_key=test_key, course_code=course_code, unique_code=unique_code)
            return jsonify({
                "success": True,
                "instructionUrl": instruction_url
            })
        else:
            logger.warning(f"Invalid test key submitted by user {email} for test {test_key}.")
            return jsonify({
                "success": False,
                "message": "Invalid Test Key!"
            }), 401

    return render_template(
        'users/mock_test/test_handler/test_login.html',
        test=test_details,
        test_key=test_key,
        course_code=course_code,
        unique_code=unique_code,
        username=username
    )
