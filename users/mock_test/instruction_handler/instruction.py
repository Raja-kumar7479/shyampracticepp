from flask import redirect, render_template, url_for
from users.mock_test.handler_db.user_db import UserOperation
from users.mock_test.utils_dashboard import get_user_session, redirect_if_test_not_found, format_section_count
from users.mock_test.decorator import secure_access_required
from extensions import user_login_required
from users import users_bp

user_op = UserOperation()

@users_bp.route('/test-instruction/<test_key>/<course_code>/<unique_code>', methods=['GET'])
@user_login_required
@secure_access_required(('unique_code', 'course_code'))
def test_instruction(test_key, course_code, unique_code):
    email, username = get_user_session()
    test = user_op.get_test_details(test_key)
    
    # Safely handle redirects if the test isn't found
    if not test:
        return redirect_if_test_not_found(test, 'purchase_dashboard', course_code=course_code, unique_code=unique_code)

    return render_template('users/mock_test/instruction_handler/instruction.html',
                           test_key=test_key, course_code=course_code, unique_code=unique_code,
                           username=username, email=email, total_duration_minutes=test['total_duration_minutes'])

@users_bp.route('/paper-instruction/<test_key>/<course_code>/<unique_code>', methods=['GET'])
@user_login_required
@secure_access_required(('unique_code', 'course_code'))
def paper_instruction(test_key, course_code, unique_code):
    email, username = get_user_session()
    test = user_op.get_test_details(test_key)
    
    if not test:
        return redirect_if_test_not_found(test, 'purchase_dashboard', course_code=course_code, unique_code=unique_code)

    sections = user_op.get_test_sections(test_key)
    return render_template('users/mock_test/instruction_handler/paper_instruction.html',
                           test_key=test_key, course_code=course_code, unique_code=unique_code,
                           username=username, email=email, total_questions=test['total_questions'],
                           total_marks=test['total_marks'], num_sections_text=format_section_count(sections),
                           sections=sections)
