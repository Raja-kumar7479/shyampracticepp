from flask import flash, redirect, request, session, url_for
from users.mock_test.handler_db.user_db import UserOperation
from users.mock_test.utils_dashboard import get_user_session
from users.mock_test.decorator import secure_access_required
from extensions import user_login_required
from users import users_bp

user_op = UserOperation()

@users_bp.route('/process-readiness/<test_key>/<course_code>/<unique_code>', methods=['POST'])
@user_login_required
@secure_access_required(('unique_code', 'course_code'))
def process_readiness(test_key, course_code, unique_code):
    email, username = get_user_session()
    is_checkbox_checked = request.form.get('readiness_checkbox') == 'on'
    if not is_checkbox_checked:
        flash('You must acknowledge the instructions before proceeding.', 'test_error')
        return redirect(url_for('users.paper_instruction', test_key=test_key, course_code=course_code, unique_code=unique_code))

    user_op.store_user_test_start(email, test_key, username, is_checkbox_checked=True, ready_to_begin=True)
    flash('You are now ready to begin the test.', 'test_success')
    return redirect(url_for('users.start_test', test_key=test_key, course_code=course_code, unique_code=unique_code))
