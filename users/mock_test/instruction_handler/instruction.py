from flask import redirect, render_template, url_for
from users.mock_test.handler_db.user_db import UserOperation
from users.mock_test.utils_dashboard import (get_user_session,
                                             redirect_if_test_not_found,
                                             format_section_count)
from users.mock_test.decorator import secure_access_required

from extensions import login_required
from users import users_bp
from extensions import login_required

user_op = UserOperation() 
import logging


user_op = UserOperation()

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)


@users_bp.route('/test-instruction/<test_id>/<course_code>/<unique_code>', methods=['GET', 'POST'])
@login_required
@secure_access_required(('unique_code', 'course_code'))
def test_instruction(test_id, course_code, unique_code):
    try:
        logger.debug("Entered test_instruction route")
        email, username = get_user_session()
        logger.debug(f"User session retrieved: email={email}, username={username}")

        test = user_op.get_test_details(test_id)
        logger.debug(f"Test details fetched for test_id={test_id}: {test}")

        redir = redirect_if_test_not_found(test, 'open_mock_test', test_id, course_code, unique_code)
        if redir:
            logger.debug("Test not found or invalid. Redirecting...")
            return redir

        total_duration_minutes = test['total_duration_minutes']
        logger.debug(f"Total duration of the test: {total_duration_minutes} minutes")

        return render_template(
            'users/course_materials/mock_test/instruction_handler/instruction.html',
            test_id=test_id,
            course_code=course_code,
            unique_code=unique_code,
            username=username,
            email = email,
            total_duration_minutes=total_duration_minutes
        )
    except Exception as e:
        logger.exception("Error occurred in test_instruction route")
        return "An internal error occurred", 500

@users_bp.route('/paper-instruction/<test_id>/<course_code>/<unique_code>', methods=['GET', 'POST'])
@login_required
@secure_access_required(('unique_code', 'course_code'))
def paper_instruction(test_id, course_code, unique_code):
    email, username = get_user_session()
     
    test = user_op.get_test_details(test_id)
    redir = redirect_if_test_not_found(test, 'open_mock_test', test_id, course_code, unique_code)
    if redir:
        return redir

    sections = user_op.get_test_sections(test_id)

    return render_template('users/course_materials/mock_test/instruction_handler/paper_instruction.html',
                           test_id=test_id,
                           course_code=course_code,
                           unique_code=unique_code,
                           username=username,
                           email = email,
                           total_questions=test['total_questions'],
                           total_marks=test['total_marks'],
                           num_sections_text=format_section_count(sections),
                           sections=sections)
