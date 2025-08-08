import logging
from flask import flash, redirect, render_template, url_for
from users.mock_test.handler_db.result_handler_db import ResultHandler
from users.mock_test.utils_dashboard import get_user_session
from users.mock_test.decorator import secure_access_required
from extensions import user_login_required
from users.mock_test.handler_db.user_db import UserOperation
from users import users_bp

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

result_handler = ResultHandler()
user_op = UserOperation()

@users_bp.route('/test_overview/<test_key>/<course_code>/<unique_code>')
@user_login_required
@secure_access_required(('unique_code', 'course_code'))
def test_overview(test_key, course_code, unique_code):
    email, username = get_user_session()
    if not email or not username:
        return redirect(url_for('users.user_login'))
    
    summary_data = result_handler.get_test_summary_details(test_key, email)
    
    if not summary_data:
        flash("Test overview data not found.", "test_error")
        logger.warning(f"Test overview data not found for test_key: {test_key}, user: {email}")
        return redirect(url_for('users.purchase_dashboard', course_code=course_code, unique_code=unique_code))

    section_id = summary_data.get('overall', {}).get('test_id')
    logger.info(f"User {email} is viewing test overview for test_key: {test_key}")

    return render_template('users/mock_test/result_handler/test_overview.html',
                           overview_table_data=summary_data.get('overall', {}),
                           test_key=test_key, 
                           test_id=section_id,
                           course_code=course_code, 
                           unique_code=unique_code, 
                           username=username)

@users_bp.route('/test_result/<test_key>/<course_code>/<unique_code>')
@user_login_required
@secure_access_required(('unique_code', 'course_code'))
def test_result(test_key, course_code, unique_code):
    email, username = get_user_session()
    if not email or not username:
        return redirect(url_for('users.user_login'))

    summary_data = result_handler.get_test_summary_details(test_key, email)
    
    if not summary_data:
        flash("Could not retrieve test result details.", "test_error")
        logger.warning(f"Test result details not found for test_key: {test_key}, user: {email}")
        test_details = user_op.get_test_details(test_key)
        section_id = test_details['test_id'] if test_details else ''
        return redirect(url_for('users.open_mock_test_section', section_id=section_id, course_code=course_code, unique_code=unique_code))
    
    logger.info(f"User {email} is viewing test result for test_key: {test_key}")
    return render_template('users/mock_test/result_handler/test_result.html',
                           summary=summary_data, test_key=test_key, course_code=course_code,
                           unique_code=unique_code, username=username, current_user_email=email)

@users_bp.route('/test_analysis/<test_key>/<course_code>/<unique_code>')
@user_login_required
@secure_access_required(('unique_code', 'course_code'))
def test_analysis(test_key, course_code, unique_code):
    email, username = get_user_session()
    if not email or not username:
        return redirect(url_for('users.user_login'))

    summary_data = result_handler.get_test_summary_details(test_key, email)
    
    if not summary_data:
        flash("Could not retrieve detailed test analysis.", "test_error")
        logger.warning(f"Test analysis data not found for test_key: {test_key}, user: {email}")
        return redirect(url_for('users.test_result', test_key=test_key, course_code=course_code, unique_code=unique_code))

    questions_by_section = {}
    for q in summary_data.get('details', []):
        section_name = q.get('section_name', 'Default Section')
        if section_name not in questions_by_section:
            questions_by_section[section_name] = []
        questions_by_section[section_name].append(q)
    
    logger.info(f"User {email} is viewing test analysis for test_key: {test_key}")
    return render_template('users/mock_test/result_handler/test_analysis.html',
                           summary=summary_data, questions_by_section=questions_by_section,
                           sorted_sections=sorted(questions_by_section.keys()),
                           test_key=test_key, course_code=course_code, unique_code=unique_code, username=username)
